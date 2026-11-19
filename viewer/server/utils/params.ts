import type { H3Event } from 'h3'
import type { SourceKind } from '#shared/types/run'
import { runSource } from './sources'
import { TASK_NAME, type RunSource } from './sources/types'

const SOURCES = new Set<SourceKind>(['git', 'results', 'live'])
const REF = /^(current|[0-9a-f]{7,40})$/

/** The source a route names (`/api/runs/:source/:ref`), or a 404 for anything else. */
export function sourceFromParams(event: H3Event): RunSource {
  const source = getRouterParam(event, 'source') as SourceKind
  const ref = getRouterParam(event, 'ref') ?? ''
  if (!SOURCES.has(source) || !REF.test(ref) || (source === 'git') === (ref === 'current')) {
    throw createError({ statusCode: 404, statusMessage: 'Unknown run source' })
  }
  return runSource(source, ref)
}

export function taskFromParams(event: H3Event): string {
  const task = getRouterParam(event, 'task') ?? ''
  if (!TASK_NAME.test(task)) throw createError({ statusCode: 404, statusMessage: 'Unknown task' })
  return task
}
