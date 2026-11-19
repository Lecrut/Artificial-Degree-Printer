import type { SourceKind } from '#shared/types/run'

export type RunFileKey = 'events' | 'trace' | 'hypergraph' | 'blueprint' | 'blueprintRoot' | 'queue' | 'thesis' | 'thesisCompiled' | 'results' | 'pdf' | 'figures'

// Where each file of a run lives, relative to the task folder (ARCHITECTURE.md §4).
const RESULTS: Record<RunFileKey, string> = {
  events: 'logs/events.jsonl',
  trace: 'logs/agent_trace.jsonl',
  hypergraph: 'evolved_adk/state/hypergraph.json',
  blueprint: 'evolved_adk/state/academic_blueprint.json',
  blueprintRoot: 'academic_blueprint.json',
  queue: 'evolved_adk/state/task_queue.json',
  thesis: 'thesis/thesis.md',
  thesisCompiled: 'thesis/thesis.compiled.md',
  results: 'results/results.csv',
  pdf: 'thesis/thesis.pdf',
  figures: 'results/figures',
}

const LIVE: Record<RunFileKey, string> = {
  events: 'workspace/logs/events.jsonl',
  trace: 'workspace/logs/agent_trace.jsonl',
  hypergraph: 'state/hypergraph.json',
  blueprint: 'state/academic_blueprint.json',
  blueprintRoot: 'state/academic_blueprint.json',
  queue: 'state/task_queue.json',
  thesis: 'workspace/thesis.md',
  thesisCompiled: 'workspace/thesis.compiled.md',
  results: 'workspace/results.csv',
  pdf: 'workspace/thesis.pdf',
  figures: 'workspace/figures',
}

export function runPath(source: SourceKind, key: RunFileKey): string {
  return (source === 'live' ? LIVE : RESULTS)[key]
}
