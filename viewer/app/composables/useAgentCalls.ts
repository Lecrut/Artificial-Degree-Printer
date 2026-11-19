import type { AgentCallDetail, AgentCallSummary } from '#shared/types/calls'
import type { RunRef } from '#shared/types/run'
import { callApi, callsApi } from '~/utils/runUrls'

/** The agent calls of a run, filtered by agent and text, and the one opened in detail with its neighbours. */
export function useAgentCalls(at: MaybeRefOrGetter<RunRef>) {
  const { data, pending, error, refresh } = useFetch<AgentCallSummary[]>(() => callsApi(toValue(at)), { default: () => [], lazy: true })
  const agent = ref<string | null>(null)
  const search = ref('')

  const agents = computed(() => [...new Set(data.value.map(c => c.agent))].sort())
  const calls = computed(() => {
    const query = search.value.trim().toLowerCase()
    return data.value.filter(c => (!agent.value || c.agent === agent.value)
      && (!query || [c.taskId, c.decision, c.model].some(v => v?.toLowerCase().includes(query))))
  })

  const openStep = ref<number | null>(null)
  const detail = ref<AgentCallDetail | null>(null)
  const loading = ref(false)
  const detailFailed = ref(false)
  // Arrow keys move faster than answers come back: only the answer for the call still open is shown.
  watch(openStep, async (step) => {
    if (step === null) return void (detail.value = null)
    loading.value = true
    detailFailed.value = false
    try {
      const answer = await $fetch<AgentCallDetail>(callApi(toValue(at), step))
      if (openStep.value === step) detail.value = answer
    }
    catch {
      if (openStep.value !== step) return
      detail.value = null
      detailFailed.value = true
    }
    finally {
      if (openStep.value === step) loading.value = false
    }
  })

  const position = computed(() => calls.value.findIndex(c => c.step === openStep.value))
  function move(delta: number) {
    const next = calls.value[position.value + delta]
    if (next) openStep.value = next.step
  }

  return { calls, agents, agent, search, pending, error, refresh, openStep, detail, loading, detailFailed, position, move }
}
