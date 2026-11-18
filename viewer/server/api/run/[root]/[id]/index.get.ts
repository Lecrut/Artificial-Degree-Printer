import { join } from 'node:path'

export default defineEventHandler((event) => {
  const { root, id } = getRouterParams(event)
  const dir = runDir(root, id)
  const events = readJsonl(join(dir, 'logs', 'events.jsonl'))
  const state = join(dir, 'evolved_adk', 'state')
  return {
    id,
    root: Number(root),
    summary: summarize(dir, events),
    events,
    hypergraph: readJson(join(state, 'hypergraph.json')),
    blueprint: readJson(join(dir, 'academic_blueprint.json')) ?? readJson(join(state, 'academic_blueprint.json')),
    calls: agentCalls(dir),
    files: runFiles(dir),
  }
})
