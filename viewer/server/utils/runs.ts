// Reading run folders. A run folder is what the benchmark runner leaves per task:
//   logs/{events,agent_trace}.jsonl, evolved_adk/state/*.json, academic_blueprint.json, code/, results/, thesis/
import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, delimiter, join, relative, resolve, isAbsolute } from 'node:path'

export type Json = Record<string, any>

export function runRoots(): string[] {
  const env = process.env.VIEWER_RUN_ROOTS
  const list = env ? env.split(delimiter) : ['../adk/workspace/benchmarks']
  return list.filter(Boolean).map((p) => resolve(p))
}

/** The folder of run `id` under root number `root`; throws 404 for anything that is not a run folder. */
export function runDir(root: string | number, id: string): string {
  const base = runRoots()[Number(root)]
  if (!base || !/^[\w.-]+$/.test(id) || id.startsWith('_')) throw createError({ statusCode: 404, statusMessage: 'Nie ma takiego przebiegu' })
  const dir = join(base, id)
  if (!existsSync(join(dir, 'logs', 'events.jsonl'))) throw createError({ statusCode: 404, statusMessage: 'Nie ma takiego przebiegu' })
  return dir
}

/** A path inside the run folder, or a 400 for one that leaves it. */
export function insideRun(dir: string, rel: string): string {
  const full = resolve(dir, rel)
  const r = relative(dir, full)
  if (!rel || r.startsWith('..') || isAbsolute(r)) throw createError({ statusCode: 400, statusMessage: 'Ścieżka poza przebiegiem' })
  return full
}

const cache = new Map<string, { mtime: number; value: any }>()

function cached<T>(path: string, parse: (text: string) => T): T {
  const mtime = statSync(path).mtimeMs
  const hit = cache.get(path)
  if (hit && hit.mtime === mtime) return hit.value
  const value = parse(readFileSync(path, 'utf-8'))
  cache.set(path, { mtime, value })
  return value
}

export function readJsonl(path: string): Json[] {
  if (!existsSync(path)) return []
  return cached(path, (text) => {
    const rows: Json[] = []
    for (const line of text.split('\n')) {
      if (!line.trim()) continue
      try {
        rows.push(JSON.parse(line))
      } catch {
        // a line cut by a crash mid-write
      }
    }
    return rows
  })
}

export function readJson(path: string): Json | null {
  if (!existsSync(path)) return null
  try {
    return cached(path, (text) => JSON.parse(text))
  } catch {
    return null
  }
}

export function agentName(agentMd: string): string {
  return basename(String(agentMd).replace(/\\/g, '/')).replace(/\.md$/, '')
}

function taskIdOf(payload: Json | undefined): string | null {
  const task = payload?.task ?? payload?.failed_task
  return task && typeof task === 'object' && task.task_id ? String(task.task_id) : null
}

/** One row per finished (or failed) agent call, in order. Old traces have no `phase`: every row is an answer. */
export function agentCalls(dir: string): Json[] {
  const trace = readJsonl(join(dir, 'logs', 'agent_trace.jsonl'))
  const ends = new Map<number, Json>()
  for (const e of readJsonl(join(dir, 'logs', 'events.jsonl'))) {
    if (e.event === 'LLM_CALL_END' && e.step != null) ends.set(Number(e.step), e)
  }
  const calls: Json[] = []
  trace.forEach((r, line) => {
    const phase = r.phase ?? 'answer'
    if (phase === 'request') return
    const step = r.step ?? calls.length + 1
    const end = ends.get(Number(step))
    const out = r.parsed_output
    calls.push({
      index: calls.length,
      line,
      step,
      ts: r.timestamp,
      agent: agentName(r.agent_md),
      provider: r.provider,
      tier: r.model_tier,
      model: r.model_name,
      elapsed_ms: r.elapsed_ms ?? null,
      task_id: end?.task_id ?? taskIdOf(r.user_payload),
      ok: phase !== 'error',
      error: r.error ?? null,
      verdict: end?.verdict ?? (out && typeof out === 'object' ? out.status ?? null : null),
      decision: end?.decision ?? null,
    })
  })
  return calls
}

export function callDetail(dir: string, index: number): Json {
  const call = agentCalls(dir)[index]
  if (!call) throw createError({ statusCode: 404, statusMessage: 'Nie ma takiego wywołania' })
  const r = readJsonl(join(dir, 'logs', 'agent_trace.jsonl'))[call.line]
  return { ...call, system_prompt: r.system_prompt, user_payload: r.user_payload, raw_response: r.raw_response, parsed_output: r.parsed_output }
}

function countAnswers(dir: string): number {
  const path = join(dir, 'logs', 'agent_trace.jsonl')
  if (!existsSync(path)) return 0
  return readJsonl(path).filter((r) => (r.phase ?? 'answer') !== 'request').length
}

export function summarize(dir: string, events: Json[]): Json {
  const count = (name: string) => events.filter((e) => e.event === name).length
  const end = [...events].reverse().find((e) => e.event === 'RUN_END' || e.event === 'RUN_STOPPED')
  const blueprint = readJson(join(dir, 'academic_blueprint.json')) ?? {}
  const tasks = new Set(events.filter((e) => e.event === 'TASK_START').map((e) => e.task_id))
  const done = new Set(events.filter((e) => e.event === 'TASK_DONE').map((e) => e.task_id))
  return {
    status: end?.status ?? end?.reason ?? 'W TOKU / PRZERWANY',
    started: events[0]?.ts ?? null,
    ended: events.at(-1)?.ts ?? null,
    title: blueprint.thesis_title ?? null,
    thesis_statement: blueprint.thesis_statement ?? null,
    tasks: tasks.size,
    tasks_done: done.size,
    llm_calls: countAnswers(dir),
    failed_verdicts: events.filter((e) => e.event === 'VERDICT' && e.status === 'FAIL').length,
    rejected_writes: count('SPEC_WRITE_REJECTED') + count('BUILDER_ANSWER_REJECTED'),
    plan_attempts: count('PLAN_CHECKED'),
    critic_reviews: count('PLAN_REVIEWED'),
    h_extended: count('H_EXTENDED'),
    evolution: events.filter((e) => /^AGENT_|SPLIT|MUTAT/.test(e.event)).length,
  }
}

export function listRuns(): Json[] {
  const runs: Json[] = []
  runRoots().forEach((base, root) => {
    if (!existsSync(base)) return
    for (const id of readdirSync(base)) {
      if (id.startsWith('_')) continue
      const dir = join(base, id)
      const eventsPath = join(dir, 'logs', 'events.jsonl')
      if (!existsSync(eventsPath)) continue
      runs.push({ root, rootPath: base, id, modified: statSync(eventsPath).mtimeMs, ...summarize(dir, readJsonl(eventsPath)) })
    }
  })
  return runs.sort((a, b) => b.modified - a.modified)
}

function listFiles(dir: string, sub: string, pattern: RegExp): string[] {
  const full = join(dir, sub)
  if (!existsSync(full)) return []
  return readdirSync(full).filter((f) => pattern.test(f)).map((f) => `${sub}/${f}`)
}

export function runFiles(dir: string): Json {
  const exists = (rel: string) => (existsSync(join(dir, rel)) ? rel : null)
  return {
    thesis_md: exists('thesis/thesis.md'),
    thesis_compiled_md: exists('thesis/thesis.compiled.md'),
    thesis_pdf: exists('thesis/thesis.pdf') ?? exists('thesis.pdf'),
    results_csv: exists('results/results.csv'),
    figures: listFiles(dir, 'results/figures', /\.(png|svg|jpe?g)$/i),
    code: [...listFiles(dir, 'code', /\.py$/), ...listFiles(dir, 'tests', /\.py$/)],
  }
}
