/** One section of `audit_repairs.md`, with the day it is about. */
export interface AuditEntry {
  id: string
  level: 1 | 2
  title: string
  date: string
  parent: string | null
  body: string
}

/** One commit of the repository with the size of its change. */
export interface CommitInfo {
  sha: string
  short: string
  date: string
  message: string
  files: number
  insertions: number
  deletions: number
  benchmarks: boolean
}

export interface Changelog {
  entries: AuditEntry[]
  commits: CommitInfo[]
}
