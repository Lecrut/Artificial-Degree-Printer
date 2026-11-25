/** One finished (or failed) agent call, without its prompt and answer. */
export interface AgentCallSummary {
  step: number
  ts: string
  agent: string
  tier: string
  model: string
  provider: string
  elapsedMs: number | null
  taskId: string | null
  ok: boolean
  running?: boolean
  verdict: string | null
  decision: string | null
}

export interface AgentCallDetail extends AgentCallSummary {
  systemPrompt: string
  payload: unknown
  answer: unknown
  rawAnswer: string
  error: string | null
}
