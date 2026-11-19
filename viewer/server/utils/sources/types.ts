import type { SourceKind } from '#shared/types/run'

/** Where the files of benchmark runs are read from: a commit, the results on disk, or a running sandbox. */
export interface RunSource {
  kind: SourceKind
  ref: string
  listTasks(): Promise<string[]>
  readText(task: string, rel: string): Promise<string | null>
  readBytes(task: string, rel: string): Promise<Buffer | null>
  listDir(task: string, rel: string): Promise<string[]>
  /** A file next to the task folders (`benchmark_summary.json`). */
  readShared(rel: string): Promise<string | null>
}

export const TASK_NAME = /^\d{2}_[\w-]+$/
