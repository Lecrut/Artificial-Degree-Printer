export interface VertexAttempt {
  task_id: string
  issues: string[]
}

export interface Vertex {
  kind: string
  owner: string | null
  state: string
  description: string
  attempts: number
  failures?: number
  history: VertexAttempt[]
  last_writer: { agent: string, task_id: string } | null
  files: string[]
}

export interface Edge {
  type: 'I' | 'R' | 'N'
  members: Record<string, string>
  spec: Record<string, unknown>
  fingerprint: string | null
  observed: string[]
}

export interface Hypergraph {
  version: number
  vertices: Record<string, Vertex>
  edges: Record<string, Edge>
  order: [string, string][]
}
