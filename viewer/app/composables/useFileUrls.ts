import type { RunRef } from '#shared/types/run'
import { fileApi } from '~/utils/runUrls'

/**
 * Addresses for `<img>` and links to a run's files. Locally the API serves them; the deployed viewer has no server,
 * so each file is fetched from the snapshot (through the fetch shim) and shown from a blob URL.
 */
export function useFileUrls(at: MaybeRefOrGetter<RunRef>, paths: MaybeRefOrGetter<string[]>) {
  const deployed = useDeployed()
  if (!deployed) return computed(() => Object.fromEntries(toValue(paths).map(p => [p, fileApi(toValue(at), p)])))
  const { data } = useAsyncData(
    () => `file-urls-${JSON.stringify([toValue(at), toValue(paths)])}`,
    async () => Object.fromEntries(await Promise.all(toValue(paths).map(async (p) => {
      const blob = await $fetch<Blob>(fileApi(toValue(at), p), { responseType: 'blob' })
      return [p, URL.createObjectURL(blob)] as const
    }))),
    { lazy: true },
  )
  return computed<Record<string, string>>(() => data.value ?? {})
}
