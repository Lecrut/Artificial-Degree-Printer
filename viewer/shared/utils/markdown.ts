import MarkdownIt from 'markdown-it'

// Vuetify utility classes per element: the thesis gets typography from the theme, not from a stylesheet.
const HEADING: Record<string, string> = {
  h1: 'text-h4 font-weight-bold mt-8 mb-4',
  h2: 'text-h5 font-weight-bold text-primary mt-8 mb-3',
  h3: 'text-h6 font-weight-bold mt-6 mb-2',
}
const CLASSES: Record<string, string> = {
  paragraph_open: 'text-body-1 mb-4',
  bullet_list_open: 'ps-6 mb-4',
  ordered_list_open: 'ps-6 mb-4',
  blockquote_open: 'border-s-lg border-primary ps-4 my-4 text-medium-emphasis',
  fence: 'd-block pa-4 rounded-lg bg-surface-bright text-pre-wrap',
  code_block: 'd-block pa-4 rounded-lg bg-surface-bright text-pre-wrap',
  code_inline: 'px-1 rounded bg-surface-bright text-primary',
  table_open: 'w-100 mb-6',
  th_open: 'pa-2 border-b text-start',
  td_open: 'pa-2 border-b',
  hr: 'my-6',
}

const md = new MarkdownIt({ html: false, linkify: true, typographer: true })
md.core.ruler.push('vuetify_classes', (state) => {
  for (const token of state.tokens) {
    const cls = token.type === 'heading_open' ? HEADING[token.tag] ?? 'text-subtitle-1 font-weight-bold mt-4 mb-2' : CLASSES[token.type]
    if (cls) token.attrJoin('class', cls)
    for (const child of token.children ?? []) if (CLASSES[child.type]) child.attrJoin('class', CLASSES[child.type]!)
  }
})

/** Plain markdown as HTML (an agent prompt): the same Vuetify classes, no pointer marks; raw HTML in the source is escaped. */
export function renderMarkdown(markdown: string): string {
  return md.render(markdown)
}

const POINTER = /\\ref_(ast|csv|fig)\{([^}]*)\}/g
const POINTER_CLASS: Record<string, string> = { ast: 'text-info', csv: 'text-primary', fig: 'text-secondary' }

/** Thesis markdown as HTML; raw HTML in the source is escaped. Symbolic pointers (`\ref_csv{…}`) are marked. */
export function renderThesis(markdown: string): string {
  return md.render(markdown).replace(POINTER, (_all, kind: string, target: string) =>
    `<span class="${POINTER_CLASS[kind]} font-weight-bold" title="\\ref_${kind}">⟨${kind}: ${target}⟩</span>`)
}
