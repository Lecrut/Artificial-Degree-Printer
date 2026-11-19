import { BENCHMARKS_DIR, git, gitBuffer } from '../repo'
import { TASK_NAME, type RunSource } from './types'

// A commit never changes: whatever was read from it is kept.
const cache = new Map<string, Promise<Buffer | null>>()

function read(sha: string, path: string): Promise<Buffer | null> {
  const key = `${sha}:${path}`
  if (!cache.has(key)) cache.set(key, gitBuffer(['show', key]))
  return cache.get(key)!
}

async function listTree(sha: string, path: string): Promise<string[]> {
  const out = await git(['ls-tree', '--name-only', `${sha}:${path}`])
  return out ? out.split('\n').filter(Boolean).sort() : []
}

/** The benchmark results as a commit recorded them. */
export function gitSource(sha: string): RunSource {
  const taskPath = (task: string, rel: string) => `${BENCHMARKS_DIR}/${task}/${rel}`.replace(/\/+$/, '')
  return {
    kind: 'git',
    ref: sha,
    async listTasks() {
      return (await listTree(sha, BENCHMARKS_DIR)).filter(name => TASK_NAME.test(name))
    },
    readBytes: (task, rel) => read(sha, taskPath(task, rel)),
    async readText(task, rel) {
      return (await read(sha, taskPath(task, rel)))?.toString('utf-8') ?? null
    },
    listDir: (task, rel) => listTree(sha, taskPath(task, rel)),
    async readShared(rel) {
      return (await read(sha, `${BENCHMARKS_DIR}/${rel}`))?.toString('utf-8') ?? null
    },
  }
}
