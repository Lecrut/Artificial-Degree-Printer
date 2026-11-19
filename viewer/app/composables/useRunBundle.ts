import type { RunBundle, RunRef } from '#shared/types/run'
import { runApi } from '~/utils/runUrls'

/** Everything about one run: its events, hypergraph, blueprint and files. */
export function useRunBundle(ref: MaybeRefOrGetter<RunRef>) {
  return useFetch<RunBundle>(() => runApi(toValue(ref)))
}
