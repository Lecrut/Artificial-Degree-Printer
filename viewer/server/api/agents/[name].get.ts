import { readAgentPrompt } from '../../utils/agentPrompts'

const AGENT_NAME = /^[a-z][a-z0-9_]*$/

export default defineEventHandler(async (event) => {
  const name = getRouterParam(event, 'name') ?? ''
  const prompt = AGENT_NAME.test(name) ? await readAgentPrompt(name) : null
  if (!prompt) throw createError({ statusCode: 404, statusMessage: 'Unknown agent' })
  return prompt
})
