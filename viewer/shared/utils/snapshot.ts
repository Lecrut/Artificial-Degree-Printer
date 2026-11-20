import type { SnapshotRoute } from '../types/snapshot'

// The deployed viewer (ARCHITECTURE.md §13): the git history as JSON packs served next to the page.
export const INDEX_PACK = 'index'

export const runPackKey = (sha: string, task: string) => `${sha}_${task}`
export const packUrl = (key: string) => `/snapshot/${key}.json`

const RUN = /^\/api\/runs\/git\/([0-9a-f]{7,40})(?:\/([\w-]+)(?:\/(calls(?:\/(\d+))?|file))?)?$/

/** The part of the snapshot behind an API address, or null for one the deployed viewer does not have (live, launch). */
export function snapshotRoute(pathname: string, query: URLSearchParams): SnapshotRoute | null {
  if (pathname === '/api/history') return { kind: 'history' }
  if (pathname === '/api/changelog') return { kind: 'changelog' }
  // The results on disk exist only on the computer that ran them.
  if (pathname === '/api/runs/results/current') return { kind: 'empty' }
  const match = RUN.exec(pathname)
  if (!match) return null
  const [, ref = '', task, sub, step] = match
  if (!task) return { kind: 'commit', ref }
  if (!sub) return { kind: 'bundle', ref, task }
  if (sub === 'calls') return { kind: 'calls', ref, task }
  if (step) return { kind: 'detail', ref, task, step }
  const path = query.get('path')
  return path ? { kind: 'file', ref, task, path } : null
}
