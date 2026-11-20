// Packs the git history the local viewer serves into .snapshot/*.json for the deployed viewer (ARCHITECTURE.md §13).
// Needs the local viewer running (`bun run dev`); a commit never changes, so a run already packed is not read again.
import { existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import type { AgentCallDetail, AgentCallSummary } from '../shared/types/calls'
import type { Changelog } from '../shared/types/changelog'
import type { CommitSummary, RunBundle } from '../shared/types/run'
import type { IndexPack, PackedFile, RunPack } from '../shared/types/snapshot'
import { INDEX_PACK, runPackKey } from '../shared/utils/snapshot'

const BASE = process.env.VIEWER_URL ?? 'http://127.0.0.1:3000'
const OUT = '.snapshot'
const PARALLEL = 16

async function get(path: string): Promise<Response> {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res
}

const json = async <T>(path: string) => (await get(path)).json() as Promise<T>

async function inBatches<T, R>(items: T[], fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = []
  for (let i = 0; i < items.length; i += PARALLEL) out.push(...await Promise.all(items.slice(i, i + PARALLEL).map(fn)))
  return out
}

async function packFile(api: string, path: string): Promise<[string, PackedFile]> {
  const res = await get(`${api}/file?path=${encodeURIComponent(path)}`)
  const type = res.headers.get('content-type') ?? 'application/octet-stream'
  return [path, { type, data: Buffer.from(await res.arrayBuffer()).toString('base64') }]
}

async function packRun(sha: string, task: string): Promise<RunPack> {
  const api = `/api/runs/git/${sha}/${task}`
  const bundle = await json<RunBundle>(api)
  const calls = await json<AgentCallSummary[]>(`${api}/calls`)
  const details = await inBatches(calls, async c => [String(c.step), await json<AgentCallDetail>(`${api}/calls/${c.step}`)] as const)
  const f = bundle.files
  const paths = [f.thesis, f.thesisCompiled, f.results, f.pdf, ...f.figures].filter((p): p is string => !!p)
  const files = await inBatches(paths, p => packFile(api, p))
  return { bundle, calls, details: Object.fromEntries(details), files: Object.fromEntries(files) }
}

function save(key: string, pack: unknown): number {
  const text = JSON.stringify(pack)
  writeFileSync(`${OUT}/${key}.json`, text)
  return text.length
}

async function main() {
  mkdirSync(OUT, { recursive: true })
  const history = await json<CommitSummary[]>('/api/history')
  const index: IndexPack = { history, changelog: await json<Changelog>('/api/changelog') }
  const keep = new Set([INDEX_PACK])
  console.log(`index: ${(save(INDEX_PACK, index) / 1e6).toFixed(2)} MB`)
  for (const commit of history) {
    for (const { task } of commit.tasks) {
      const key = runPackKey(commit.sha, task)
      keep.add(key)
      if (existsSync(`${OUT}/${key}.json`)) continue
      console.log(`${commit.short} ${task}: ${(save(key, await packRun(commit.sha, task)) / 1e6).toFixed(2)} MB`)
    }
  }
  for (const name of readdirSync(OUT)) if (!keep.has(name.replace(/\.json$/, ''))) rmSync(`${OUT}/${name}`)
}

main().catch((error: Error) => {
  console.error(`snapshot: ${error.message} — czy lokalny viewer działa pod ${BASE} (bun run dev)?`)
  process.exit(1)
})
