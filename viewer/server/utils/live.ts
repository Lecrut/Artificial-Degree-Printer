import { readdir, readFile, stat } from 'node:fs/promises'
import { join, resolve } from 'node:path'
import type { Hypergraph } from '#shared/types/hypergraph'
import type { QueueTask } from '#shared/types/live'
import type { RunEvent } from '#shared/types/run'
import { parseJsonl } from '#shared/utils/events'
import { REPO_ROOT, SANDBOX_DIR } from './repo'
import { runPath } from './runLayout'
import { TASK_NAME } from './sources/types'
import { parseJson } from '#shared/utils/json'

const sandbox = resolve(REPO_ROOT, SANDBOX_DIR)
const pathOf = (task: string, key: 'events' | 'trace' | 'hypergraph' | 'queue') => join(sandbox, task, runPath('live', key))
const mtime = (path: string) => stat(path).then(s => s.mtimeMs).catch(() => 0)

/** The sandbox whose events changed last: the running benchmark task, or the last one that ran. */
export async function liveTask(): Promise<string | null> {
  const tasks = (await readdir(sandbox).catch(() => [] as string[])).filter(name => TASK_NAME.test(name))
  const times = await Promise.all(tasks.map(async task => ({ task, at: await mtime(pathOf(task, 'events')) })))
  const latest = times.filter(t => t.at > 0).sort((a, b) => b.at - a.at)[0]
  return latest?.task ?? null
}

/** Events appended since `offset` (bytes): only complete lines, and the offset after them. */
export async function eventsSince(task: string, offset: number): Promise<{ events: RunEvent[], offset: number }> {
  const bytes = await readFile(pathOf(task, 'events')).catch(() => null)
  if (!bytes || bytes.length <= offset) return { events: [], offset: bytes && bytes.length < offset ? 0 : offset }
  const fresh = bytes.subarray(offset)
  const end = fresh.lastIndexOf(0x0a) + 1
  return { events: parseJsonl(fresh.subarray(0, end).toString('utf-8')), offset: offset + end }
}

async function readJson<T>(path: string, fallback: T): Promise<T> {
  return parseJson<T>(await readFile(path, 'utf-8').catch(() => null)) ?? fallback
}

/** The hypergraph and the queue of the sandbox, and a stamp that changes when either file does. */
export async function liveState(task: string) {
  const stamp = `${await mtime(pathOf(task, 'hypergraph'))}:${await mtime(pathOf(task, 'queue'))}`
  return {
    stamp,
    hypergraph: await readJson<Hypergraph | null>(pathOf(task, 'hypergraph'), null),
    queue: await readJson<QueueTask[]>(pathOf(task, 'queue'), []),
  }
}

/** Stamp of `agent_trace.jsonl` (task, byte size and mtime) so the Agents view refreshes when calls start or finish. */
export async function liveTraceStamp(task: string): Promise<string> {
  const info = await stat(pathOf(task, 'trace')).catch(() => null)
  return info ? `${task}:${info.size}:${Math.trunc(info.mtimeMs)}` : `${task}:0`
}
