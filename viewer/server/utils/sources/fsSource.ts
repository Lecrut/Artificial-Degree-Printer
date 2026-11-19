import { readdir, readFile } from 'node:fs/promises'
import { join, relative, resolve } from 'node:path'
import type { SourceKind } from '#shared/types/run'
import { REPO_ROOT } from '../repo'
import { TASK_NAME, type RunSource } from './types'

/** Runs in a folder of the repository: the results on disk or the sandboxes of a running benchmark. */
export function fsSource(kind: SourceKind, base: string): RunSource {
  const root = resolve(REPO_ROOT, base)

  function inside(task: string, rel: string): string | null {
    const path = resolve(root, task, rel)
    return relative(join(root, task), path).startsWith('..') ? null : path
  }

  async function readBytes(task: string, rel: string): Promise<Buffer | null> {
    const path = inside(task, rel)
    return path ? readFile(path).catch(() => null) : null
  }

  return {
    kind,
    ref: 'current',
    async listTasks() {
      const names = await readdir(root).catch(() => [] as string[])
      return names.filter(name => TASK_NAME.test(name)).sort()
    },
    readBytes,
    async readText(task, rel) {
      return (await readBytes(task, rel))?.toString('utf-8') ?? null
    },
    async readShared(rel) {
      return readFile(resolve(root, rel), 'utf-8').catch(() => null)
    },
    async listDir(task, rel) {
      const path = inside(task, rel)
      return path ? (await readdir(path).catch(() => [] as string[])).sort() : []
    },
  }
}
