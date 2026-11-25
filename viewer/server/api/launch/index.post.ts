import type { LaunchRequest } from '#shared/types/live'
import { LAUNCH_TASKS, normalizeTasks } from '#shared/utils/launch'
import { launchStatus, startLaunch } from '../../utils/launcher'
import { SNAPSHOT_FILE, resumeDir } from '../../utils/resumeSource'

const PROVIDERS = new Set(['mock', 'ollama', 'google'])
const TEMPLATES = new Set(['thesis_plodz', 'paper_ieee'])
const SOURCES = new Set(['git', 'results', 'live'])
const REF = /^(current|[0-9a-f]{7,40})$/

export default defineEventHandler(async (event) => {
  const body = await readBody<Partial<LaunchRequest>>(event)
  const requested = Array.isArray(body?.tasks) ? body.tasks.map(String) : []
  const tasks = normalizeTasks(requested)
  const known = requested.every(task => (LAUNCH_TASKS as readonly string[]).includes(task))
  if (!tasks.length || !known || !PROVIDERS.has(String(body?.provider)) || (body?.template && !TEMPLATES.has(body.template))) {
    throw createError({ statusCode: 400, statusMessage: 'Unknown tasks, provider or template' })
  }
  const request: LaunchRequest = { tasks, provider: body.provider!, template: body.template ?? null }
  const from = body?.resume
  if (!from) return startLaunch(request)
  const snapshotOk = from.snapshot === undefined || SNAPSHOT_FILE.test(from.snapshot)
  const valid = tasks.length === 1 && SOURCES.has(from.source) && REF.test(from.ref) && (from.source === 'git') === (from.ref !== 'current') && snapshotOk
  if (!valid) throw createError({ statusCode: 400, statusMessage: 'Resume needs one task and a known run' })
  if (launchStatus().running) throw createError({ statusCode: 409, statusMessage: 'A benchmark is already running' })
  return startLaunch(request, await resumeDir(from, tasks[0]!))
})
