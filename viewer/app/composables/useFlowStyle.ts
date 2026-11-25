import type { StylesheetJson } from 'cytoscape'
import { useTheme } from 'vuetify'
import type { FlowKind } from '#shared/types/flow'
import { FLOW_KIND_COLOR } from '#shared/utils/colors'
import { BLOCK_SIZE } from '#shared/utils/flow'

const SHAPE: Record<FlowKind, string> = {
  start: 'barrel',
  end: 'barrel',
  step: 'rectangle',
  agent: 'round-rectangle',
  decision: 'diamond',
  jump: 'round-tag',
}

/** Cytoscape styles of the flow diagram from the Vuetify theme: each kind of block in the color the legend shows. */
export function useFlowStyle() {
  const theme = useTheme()
  return computed<StylesheetJson>(() => {
    const c = theme.current.value.colors as Record<string, string>
    const color = (key: string) => c[key] ?? '#6b7280'
    return [
      { selector: 'node', style: { 'label': 'data(label)', 'width': 'data(w)', 'height': 'data(h)', 'text-valign': 'center', 'text-halign': 'center', 'text-wrap': 'wrap', 'text-max-width': '170px', 'font-size': 13, 'color': color('on-surface'), 'border-width': 2, 'background-opacity': 0.16 } },
      ...(Object.keys(SHAPE) as FlowKind[]).map(kind => ({
        selector: `node[kind = "${kind}"]`,
        style: {
          'shape': SHAPE[kind], 'background-color': color(FLOW_KIND_COLOR[kind]), 'border-color': color(FLOW_KIND_COLOR[kind]),
          // A diamond has less room for text than its box suggests.
          'text-max-width': `${Math.round(BLOCK_SIZE[kind].w * (kind === 'decision' ? 0.52 : 0.82))}px`,
        },
      })),
      { selector: 'node[kind = "jump"]', style: { 'border-style': 'dashed', 'font-size': 12, 'color': color('on-surface-variant') } },
      { selector: 'node[kind = "agent"]', style: { 'font-weight': 'bold', 'font-family': 'monospace', 'font-size': 12 } },
      { selector: 'edge', style: { 'width': 2, 'line-color': color('on-surface-variant'), 'target-arrow-shape': 'triangle', 'target-arrow-color': color('on-surface-variant'), 'curve-style': 'taxi', 'taxi-direction': 'auto', 'label': 'data(label)', 'font-size': 12, 'color': color('on-surface'), 'text-background-color': color('background'), 'text-background-opacity': 1, 'text-background-padding': '3px', 'line-opacity': 0.7 } },
      { selector: 'node.hovered', style: { 'background-opacity': 0.4 } },
      { selector: ':selected', style: { 'border-width': 4, 'background-opacity': 0.45, 'overlay-opacity': 0 } },
    ]
  })
}
