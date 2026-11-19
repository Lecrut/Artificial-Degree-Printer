import type { RunFiles, RunRef } from '#shared/types/run'
import { parseCsv } from '#shared/utils/csv'
import { renderThesis } from '#shared/utils/markdown'
import { fileApi } from '~/utils/runUrls'

async function text(at: RunRef, path: string | null): Promise<string> {
  return path ? await $fetch<string>(fileApi(at, path), { responseType: 'text' }) : ''
}

/** The thesis of a run (with its pointers, or with the values they resolve to), its results table and figures. */
export function useThesis(at: MaybeRefOrGetter<RunRef>, files: MaybeRefOrGetter<RunFiles>) {
  const compiled = ref(false)
  const { data, pending, error, refresh } = useAsyncData(
    () => `thesis-${JSON.stringify(toValue(at))}`,
    async () => {
      const f = toValue(files)
      const ref = toValue(at)
      const [source, resolved, csv] = await Promise.all([text(ref, f.thesis), text(ref, f.thesisCompiled), text(ref, f.results)])
      return { source, resolved, csv }
    },
    { lazy: true },
  )
  const html = computed(() => renderThesis((compiled.value ? data.value?.resolved : data.value?.source) ?? ''))
  const results = computed(() => parseCsv(data.value?.csv ?? ''))
  const figures = computed(() => toValue(files).figures.map(path => ({ path, url: fileApi(toValue(at), path) })))
  const pdf = computed(() => (toValue(files).pdf ? fileApi(toValue(at), toValue(files).pdf!) : null))
  return { compiled, html, results, figures, pdf, pending, error, refresh, hasCompiled: computed(() => !!toValue(files).thesisCompiled) }
}
