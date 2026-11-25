/** What a block of the flow diagram is: a step the harness does itself, a model, a branch, a jump back or an end. */
export type FlowKind = 'start' | 'end' | 'step' | 'agent' | 'decision' | 'jump'

export interface FlowNode {
  /** For an agent: the name of its prompt file (`seed_coder` is `adk/agents/building/seed_coder.md`). */
  id: string
  kind: FlowKind
  /** Grid position: column 0 is the main line, the rows grow downwards. */
  col: number
  row: number
}

export type FlowEdgeLabel = 'yes' | 'no' | 'code' | 'test' | 'doc' | 'research' | 'more' | 'budget' | 'spent'

export interface FlowEdge {
  from: string
  to: string
  label?: FlowEdgeLabel
}

/** The base prompt of one agent, as the harness reads it from `adk/agents/<group>/<name>.md`. */
export interface AgentPrompt {
  name: string
  group: string
  markdown: string
}
