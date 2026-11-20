import type { AgentCallDetail, AgentCallSummary } from './calls'
import type { Changelog } from './changelog'
import type { CommitSummary, RunBundle } from './run'

/** What the deployed viewer reads instead of the API: everything that does not depend on a run. */
export interface IndexPack {
  history: CommitSummary[]
  changelog: Changelog
}

/** One file of a run (thesis, results, figure, PDF), as base64 with its media type. */
export interface PackedFile {
  type: string
  data: string
}

/** Everything the API answers about one run of one commit. */
export interface RunPack {
  bundle: RunBundle
  calls: AgentCallSummary[]
  details: Record<string, AgentCallDetail>
  files: Record<string, PackedFile>
}

/** Which part of the snapshot answers an API address. */
export type SnapshotRoute
  = | { kind: 'history' }
    | { kind: 'changelog' }
    | { kind: 'empty' }
    | { kind: 'commit', ref: string }
    | { kind: 'bundle', ref: string, task: string }
    | { kind: 'calls', ref: string, task: string }
    | { kind: 'detail', ref: string, task: string, step: string }
    | { kind: 'file', ref: string, task: string, path: string }
