/** A small CSV reader for results files: header row, quoted fields, commas inside quotes. */
export function parseCsv(text: string): { headers: string[], rows: Record<string, string>[] } {
  const lines = text.split(/\r?\n/).filter(line => line.trim())
  const split = (line: string) => {
    const cells: string[] = []
    let cell = ''
    let quoted = false
    for (const ch of line) {
      if (ch === '"') quoted = !quoted
      else if (ch === ',' && !quoted) {
        cells.push(cell)
        cell = ''
      }
      else cell += ch
    }
    return [...cells, cell]
  }
  const headers = lines[0] ? split(lines[0]) : []
  const rows = lines.slice(1).map(line => Object.fromEntries(split(line).map((value, i) => [headers[i] ?? `col${i}`, value])))
  return { headers, rows }
}
