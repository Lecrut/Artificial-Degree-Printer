import type { SnapshotRoute } from '#shared/types/snapshot'
import { snapshotRoute } from '#shared/utils/snapshot'
import type { PackReader } from './packs'

const json = (body: unknown) => new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } })
const notFound = () => new Response('Not in the snapshot', { status: 404 })

function decode(base64: string): Uint8Array<ArrayBuffer> {
  return Uint8Array.from(atob(base64), c => c.charCodeAt(0))
}

async function answer(route: SnapshotRoute, packs: PackReader): Promise<Response> {
  if (route.kind === 'empty') return json([])
  if (route.kind === 'history' || route.kind === 'changelog') {
    const index = await packs.index()
    return index ? json(index[route.kind]) : notFound()
  }
  if (route.kind === 'commit') {
    const commit = await packs.commit(route.ref)
    return commit ? json(commit.tasks) : notFound()
  }
  const run = await packs.run(route.ref, route.task)
  if (!run) return notFound()
  switch (route.kind) {
    case 'bundle': return json(run.bundle)
    case 'calls': return json(run.calls)
    case 'detail': return route.step in run.details ? json(run.details[route.step]) : notFound()
    case 'file': {
      const file = run.files[route.path]
      return file ? new Response(decode(file.data), { headers: { 'content-type': file.type } }) : notFound()
    }
  }
}

/**
 * The deployed viewer has no server: every `/api/*` request (useFetch, $fetch) is answered from the snapshot.
 * ofetch calls `globalThis.fetch` on each request, so replacing it here reaches every composable unchanged.
 */
export function installFetchShim(packs: PackReader) {
  const original = globalThis.fetch.bind(globalThis)
  globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(input instanceof Request ? input.url : String(input), location.origin)
    if (url.origin !== location.origin || !url.pathname.startsWith('/api/')) return original(input, init)
    const route = snapshotRoute(url.pathname, url.searchParams)
    return route ? answer(route, packs) : notFound()
  }) as typeof fetch
}
