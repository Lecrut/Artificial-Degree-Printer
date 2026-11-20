import type { IndexPack, RunPack } from '#shared/types/snapshot'
import { INDEX_PACK, packUrl, runPackKey } from '#shared/utils/snapshot'

/** Reads the snapshot's packs, static files next to the page; each pack once per page load. */
export function packReader() {
  const cache = new Map<string, Promise<unknown>>()

  function pack<T>(key: string): Promise<T | null> {
    if (!cache.has(key)) cache.set(key, fetch(packUrl(key)).then(res => (res.ok ? res.json() : null)))
    return cache.get(key) as Promise<T | null>
  }

  const index = () => pack<IndexPack>(INDEX_PACK)

  /** The full sha of a commit named by any prefix of it (the addresses carry what the history gave). */
  async function commit(ref: string) {
    return (await index())?.history.find(c => c.sha.startsWith(ref)) ?? null
  }

  async function run(ref: string, task: string) {
    const found = await commit(ref)
    return found ? pack<RunPack>(runPackKey(found.sha, task)) : null
  }

  return { index, commit, run }
}

export type PackReader = ReturnType<typeof packReader>
