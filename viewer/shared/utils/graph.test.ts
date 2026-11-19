import { describe, expect, it } from 'bun:test'
import type { Hypergraph } from '../types/hypergraph'
import type { RunEvent } from '../types/run'
import { graphElements, vertexLabel } from './graph'
import { toJsonTree } from './jsonTree'
import { stateChanges, statesAt } from './replay'

const vertex = (kind: string, state: string, files: string[] = []) => ({
  kind, owner: null, state, description: '', attempts: 0, history: [], last_writer: null, files,
})

const H: Hypergraph = {
  version: 2,
  vertices: { 'core.py': vertex('entry', 'verified', ['style.py']), 'thesis.md#ch2': vertex('chapter', 'drafted') },
  edges: {
    'I:core.py': { type: 'I', members: { 'core.py': 'P' }, spec: {}, fingerprint: null, observed: [] },
    'N:thesis.md#ch2': { type: 'N', members: { 'thesis.md#ch2': 'X', 'core.py': 'C' }, spec: {}, fingerprint: null, observed: ['core.py'] },
  },
  order: [['I:core.py', 'N:thesis.md#ch2']],
}

describe('hypergraph view', () => {
  it('draws vertices, bags, members with roles, the order and helper files', () => {
    const { nodes, links } = graphElements(H, {})
    expect(nodes.map(n => n.id)).toEqual(['v:core.py', 'v:thesis.md#ch2', 'e:I:core.py', 'e:N:thesis.md#ch2', 'f:style.py'])
    expect(links.find(l => l.id === 'm:N:thesis.md#ch2:core.py')).toMatchObject({ label: 'C', observed: true })
    expect(links.filter(l => l.group === 'order')).toHaveLength(1)
    expect(vertexLabel('thesis.md#ch2')).toBe('rozdz. 2')
  })

  it('replays the state changes from the states after planning to the saved graph', () => {
    const events: RunEvent[] = [
      { ts: '1', event: 'VERTEX_STATE', vertex: 'core.py', state: 'impl' },
      { ts: '2', event: 'TASK_DONE', task_id: 'T1' },
      { ts: '3', event: 'VERTEX_STATE', vertex: 'core.py', state: 'verified' },
    ]
    const changes = stateChanges(events)
    expect(statesAt(H, changes, 0)).toEqual({ 'core.py': 'stub', 'thesis.md#ch2': 'spec' })
    expect(statesAt(H, changes, 1)['core.py']).toBe('impl')
    expect(statesAt(H, changes, 2)).toEqual({ 'core.py': 'verified', 'thesis.md#ch2': 'drafted' })
  })

  it('turns JSON into tree items', () => {
    const tree = toJsonTree({ status: 'FAIL', issues: ['a'], n: 2 })
    expect(tree.children?.map(c => [c.title, c.kind, c.value])).toEqual([
      ['status', 'string', 'FAIL'], ['issues [1]', 'array', null], ['n', 'number', '2'],
    ])
  })
})
