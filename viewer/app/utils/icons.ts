import {
  mdiAccountPlusOutline, mdiAlertCircleOutline, mdiCancel, mdiCheckCircleOutline, mdiCloseCircleOutline, mdiDna, mdiFileReplaceOutline,
  mdiFileTreeOutline, mdiFlagCheckered, mdiFlask, mdiGraphOutline, mdiInformationOutline, mdiPlaylistEdit, mdiProgressClock,
  mdiRefresh, mdiTimerSand, mdiWrenchOutline,
} from '@mdi/js'
import type { EntryKind, EntryStatus, TaskAttempt } from '#shared/types/timeline'

// One icon per kind of thing on the screen, so the same thing looks the same everywhere.
export const KIND_ICON: Record<EntryKind, string> = {
  plan: mdiFileTreeOutline,
  graph: mdiGraphOutline,
  agent: mdiAccountPlusOutline,
  task: mdiWrenchOutline,
  queue: mdiPlaylistEdit,
  replan: mdiRefresh,
  evolution: mdiDna,
  end: mdiFlagCheckered,
}

export function attemptIcon(attempt: TaskAttempt): string {
  if (attempt.kind === 'verdict') return attempt.status === 'ok' ? mdiCheckCircleOutline : mdiCloseCircleOutline
  if (attempt.kind === 'rejected') return mdiCancel
  if (attempt.kind === 'plan-change') return mdiFileReplaceOutline
  if (attempt.kind === 'data') return mdiFlask
  return attempt.status === 'waiting' ? mdiTimerSand : mdiInformationOutline
}

export const STATUS_ICON: Record<EntryStatus, string> = {
  ok: mdiCheckCircleOutline,
  fail: mdiCloseCircleOutline,
  warn: mdiAlertCircleOutline,
  info: mdiInformationOutline,
  running: mdiProgressClock,
  waiting: mdiTimerSand,
}

export function runStatusIcon(status: string): string {
  if (status === 'COMPLETED') return mdiCheckCircleOutline
  if (status === 'COMPLETED_WITH_GAPS') return mdiAlertCircleOutline
  if (status === 'RUNNING') return mdiProgressClock
  return mdiCloseCircleOutline
}
