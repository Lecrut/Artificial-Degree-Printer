import type { SourceKind } from '#shared/types/run'
import { BENCHMARKS_DIR, SANDBOX_DIR } from '../repo'
import { fsSource } from './fsSource'
import { gitSource } from './gitSource'
import type { RunSource } from './types'

export function runSource(kind: SourceKind, ref: string): RunSource {
  if (kind === 'git') return gitSource(ref)
  return fsSource(kind, kind === 'live' ? SANDBOX_DIR : BENCHMARKS_DIR)
}
