import type { LaunchRequest } from '#shared/types/live'
import { LAUNCH_TASKS, normalizeTasks } from '#shared/utils/launch'
import { startLaunch } from '../../utils/launcher'

const PROVIDERS = new Set(['mock', 'ollama', 'google'])
const TEMPLATES = new Set(['thesis_plodz', 'paper_ieee'])

export default defineEventHandler(async (event) => {
  const body = await readBody<Partial<LaunchRequest>>(event)
  const requested = Array.isArray(body?.tasks) ? body.tasks.map(String) : []
  const tasks = normalizeTasks(requested)
  const known = requested.every(task => (LAUNCH_TASKS as readonly string[]).includes(task))
  if (!tasks.length || !known || !PROVIDERS.has(String(body?.provider)) || (body?.template && !TEMPLATES.has(body.template))) {
    throw createError({ statusCode: 400, statusMessage: 'Unknown tasks, provider or template' })
  }
  return startLaunch({ tasks, provider: body.provider!, template: body.template ?? null })
})
