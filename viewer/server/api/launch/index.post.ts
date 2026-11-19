import type { LaunchRequest } from '#shared/types/live'
import { startLaunch } from '../../utils/launcher'

const TASKS = new Set(['1', '2', '3', '4', 'all'])
const PROVIDERS = new Set(['mock', 'ollama', 'google'])
const TEMPLATES = new Set(['thesis_plodz', 'paper_ieee'])

export default defineEventHandler(async (event) => {
  const body = await readBody<Partial<LaunchRequest>>(event)
  if (!TASKS.has(String(body?.task)) || !PROVIDERS.has(String(body?.provider)) || (body?.template && !TEMPLATES.has(body.template))) {
    throw createError({ statusCode: 400, statusMessage: 'Unknown task, provider or template' })
  }
  return startLaunch({ task: body.task!, provider: body.provider!, template: body.template ?? null })
})
