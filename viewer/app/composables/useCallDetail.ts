import type { AgentCallDetail } from '#shared/types/calls'
import type { RunRef } from '#shared/types/run'
import { callApi } from '~/utils/runUrls'

/** One agent call with its prompt, payload and answer, fetched when it is first shown. */
export function useCallDetail(at: MaybeRefOrGetter<RunRef>, step: MaybeRefOrGetter<number>) {
  return useFetch<AgentCallDetail>(() => callApi(toValue(at), toValue(step)), { lazy: true, key: callApi(toValue(at), toValue(step)) })
}
