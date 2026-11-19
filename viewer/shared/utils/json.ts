/** JSON that may be missing or cut off mid-write (a crash, a file still being written): null instead of a throw. */
export function parseJson<T>(text: string | null | undefined): T | null {
  if (!text) return null
  try {
    return JSON.parse(text) as T
  }
  catch {
    return null
  }
}

/** Every complete JSON line of a JSONL file; broken lines are skipped. */
export function parseJsonLines<T>(text: string): T[] {
  return text.split('\n').flatMap((line) => {
    const row = parseJson<T>(line.trim())
    return row === null ? [] : [row]
  })
}
