import { describe, expect, test } from 'bun:test'
import { readdirSync } from 'node:fs'
import { flowLabels } from '../../../app/utils/labelParts/flow'
import { FLOW_AGENTS, FLOW_EDGES, FLOW_NODES, flowBounds, flowElements } from './index'

const AGENTS_DIR = new URL('../../../../adk/agents/', import.meta.url)
const promptFiles = readdirSync(AGENTS_DIR, { withFileTypes: true })
  .filter(entry => entry.isDirectory())
  .flatMap(group => readdirSync(new URL(`${group.name}/`, AGENTS_DIR)).filter(file => file.endsWith('.md')).map(file => file.slice(0, -3)))
const ids = new Set(FLOW_NODES.map(node => node.id))

describe('flow diagram', () => {
  test('blocks have unique ids and their own place on the grid', () => {
    expect(ids.size).toBe(FLOW_NODES.length)
    expect(new Set(FLOW_NODES.map(node => `${node.col}:${node.row}`)).size).toBe(FLOW_NODES.length)
  })

  test('every arrow joins two existing blocks and a branch has at least two ways out', () => {
    for (const edge of FLOW_EDGES) {
      expect(ids.has(edge.from)).toBe(true)
      expect(ids.has(edge.to)).toBe(true)
    }
    for (const node of FLOW_NODES.filter(n => n.kind === 'decision')) {
      expect(FLOW_EDGES.filter(edge => edge.from === node.id).length).toBeGreaterThanOrEqual(2)
    }
  })

  test('the flow starts at one block, ends at ends and jumps, and reaches everything', () => {
    expect(FLOW_NODES.filter(node => node.kind === 'start').map(node => node.id)).toEqual(['start'])
    for (const node of FLOW_NODES) {
      const out = FLOW_EDGES.filter(edge => edge.from === node.id).length
      const into = FLOW_EDGES.filter(edge => edge.to === node.id).length
      expect(node.kind === 'end' || node.kind === 'jump' ? out === 0 : out > 0).toBe(true)
      expect(node.kind === 'start' || into > 0).toBe(true)
    }
  })

  test('the agents on the diagram are exactly the prompt files of the harness', () => {
    expect([...FLOW_AGENTS].sort()).toEqual([...promptFiles].sort())
  })

  test('every block and every answer on an arrow has a text', () => {
    for (const node of FLOW_NODES) {
      expect(flowLabels.nodes[node.id]?.label).toBeTruthy()
      expect(flowLabels.nodes[node.id]?.note).toBeTruthy()
    }
    for (const edge of FLOW_EDGES) if (edge.label) expect(flowLabels.edges[edge.label]).toBeTruthy()
  })

  test('elements carry the position of the grid and the proportions are those of a tall diagram', () => {
    const { nodes, edges } = flowElements({ node: id => id, edge: label => label })
    expect(nodes).toHaveLength(FLOW_NODES.length)
    expect(edges).toHaveLength(FLOW_EDGES.length)
    expect(nodes.find(node => node.data.id === 'start')?.position).toEqual({ x: 0, y: 0 })
    const { width, height } = flowBounds()
    expect(height).toBeGreaterThan(width)
  })
})
