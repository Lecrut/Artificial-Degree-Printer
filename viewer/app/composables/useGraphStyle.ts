import type { StylesheetJson } from 'cytoscape'
import { useTheme } from 'vuetify'
import { BAG_COLOR } from '#shared/utils/roles'
import { vertexStateColor } from '#shared/utils/states'

const STATES = ['spec', 'stub', 'impl', 'written', 'drafted', 'verified', 'stale', 'failed']

/** Cytoscape styles from the Vuetify theme, so the graph uses the same colors as the rest of the page. */
export function useGraphStyle() {
  const theme = useTheme()
  return computed<StylesheetJson>(() => {
    const c = theme.current.value.colors as Record<string, string>
    const color = (key: string) => c[key] ?? '#6b7280'
    return [
      { selector: 'node', style: { 'label': 'data(label)', 'color': color('on-surface'), 'font-size': 10, 'text-valign': 'bottom', 'text-margin-y': 4 } },
      { selector: 'node[group = "vertex"]', style: { 'shape': 'round-rectangle', 'width': 26, 'height': 26, 'background-color': color('surface-bright'), 'border-width': 3, 'underlay-shape': 'round-rectangle', 'transition-property': 'border-color, underlay-opacity, underlay-padding', 'transition-duration': 350 } },
      ...STATES.map(state => ({ selector: `node[state = "${state}"]`, style: { 'border-color': color(vertexStateColor(state)), 'underlay-color': color(vertexStateColor(state)) } })),
      // A vertex whose state just changed in the replay glows in its new color for a moment.
      { selector: 'node.changed', style: { 'underlay-opacity': 0.55, 'underlay-padding': 14 } },
      { selector: 'node[group = "bag"]', style: { 'shape': 'diamond', 'width': 16, 'height': 16, 'font-size': 8, 'color': color('on-surface-variant') } },
      ...Object.entries(BAG_COLOR).map(([type, key]) => ({ selector: `node[group = "bag"][kind = "${type}"]`, style: { 'background-color': color(key) } })),
      { selector: 'node[group = "helper"]', style: { 'shape': 'ellipse', 'width': 12, 'height': 12, 'background-color': color('surface-variant') } },
      { selector: 'edge', style: { 'width': 1.2, 'line-color': color('surface-variant'), 'curve-style': 'bezier', 'label': '', 'font-size': 7, 'color': color('on-surface-variant'), 'text-background-color': color('surface'), 'text-background-opacity': 1 } },
      { selector: 'edge[?observed]', style: { 'line-style': 'dashed', 'line-color': color('warning') } },
      { selector: 'edge[group = "order"]', style: { 'line-style': 'dotted', 'target-arrow-shape': 'triangle', 'target-arrow-color': color('primary'), 'line-color': color('primary'), 'width': 1.5 } },
      { selector: '.faded', style: { opacity: 0.12 } },
      // Role labels clutter the whole graph, so they appear only on the links of the selected element.
      { selector: 'edge.highlighted', style: { 'width': 2.2, 'line-color': color('primary'), 'label': 'data(label)' } },
      { selector: 'node.highlighted', style: { 'font-weight': 'bold' } },
      { selector: ':selected', style: { 'overlay-color': color('primary'), 'overlay-opacity': 0.25, 'overlay-padding': 6 } },
      { selector: 'node.hovered', style: { 'underlay-color': color('primary'), 'underlay-opacity': 0.3, 'underlay-padding': 8, 'underlay-shape': 'ellipse', 'font-weight': 'bold' } },
    ]
  })
}
