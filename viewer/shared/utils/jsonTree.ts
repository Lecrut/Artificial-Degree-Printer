/** A JSON value as tree items for `v-treeview`: objects and arrays open, scalars are leaves with their text. */
export interface JsonTreeItem {
  id: string
  title: string
  value: string | null
  kind: 'object' | 'array' | 'string' | 'number' | 'boolean' | 'null'
  children?: JsonTreeItem[]
}

function kindOf(value: unknown): JsonTreeItem['kind'] {
  if (value === null || value === undefined) return 'null'
  if (Array.isArray(value)) return 'array'
  return typeof value === 'object' ? 'object' : (typeof value as 'string' | 'number' | 'boolean')
}

export function toJsonTree(value: unknown, title = '', id = '$'): JsonTreeItem {
  const kind = kindOf(value)
  if (kind === 'object' || kind === 'array') {
    const entries = kind === 'array' ? (value as unknown[]).map((v, i) => [String(i), v] as const) : Object.entries(value as object)
    return {
      id,
      title: `${title}${kind === 'array' ? ` [${entries.length}]` : ` {${entries.length}}`}`.trim(),
      value: null,
      kind,
      children: entries.map(([key, child]) => toJsonTree(child, key, `${id}.${key}`)),
    }
  }
  return { id, title, value: kind === 'null' ? 'null' : String(value), kind }
}
