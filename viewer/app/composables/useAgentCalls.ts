import type { AgentCallDetail, AgentCallSummary } from '#shared/types/calls'
import type { RunRef } from '#shared/types/run'
import { callApi, callsApi } from '~/utils/runUrls'

function useOpenedCall(at: MaybeRefOrGetter<RunRef>, calls: ComputedRef<AgentCallSummary[]>) {
  const openStep = ref<number | null>(null)
  const detail = ref<AgentCallDetail | null>(null)
  const loading = ref(false)
  const detailFailed = ref(false)

  async function fetchDetail(step: number) {
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
  }

  // Arrow keys move faster than answers come back: only the answer for the call still open is shown.
  watch(openStep, (step) => {
    if (step === null) detail.value = null
    else void fetchDetail(step)
  })
  // If an in-flight call finishes while its dialog is open, pull the newly written answer automatically.
  watch(calls, (list) => {
    if (openStep.value === null || !detail.value?.running) return
    const latest = list.find(c => c.step === openStep.value)
    if (latest && !latest.running) void fetchDetail(openStep.value)
  })

  return { openStep, detail, loading, detailFailed }
}

/** The agent calls of a run, kept fresh via `liveStamp` on live runs, filtered by agent and text. */
export function useAgentCalls(at: MaybeRefOrGetter<RunRef>, liveStamp?: MaybeRefOrGetter<string | undefined>) {
  const { data, pending, error, refresh } = useFetch<AgentCallSummary[]>(() => callsApi(toValue(at)), { default: () => [], lazy: true })
  const agent = ref<string | null>(null)
  const search = ref('')
  const initialPending = computed(() => pending.value && !data.value.length)

  if (liveStamp) {
    watch(() => toValue(liveStamp), (stamp) => {
      if (stamp) void refresh()
    })
  }

  const agents = computed(() => [...new Set(data.value.map(c => c.agent))].sort())
  const calls = computed(() => {
    const query = search.value.trim().toLowerCase()
    return data.value.filter(c => (!agent.value || c.agent === agent.value)
      && (!query || [c.taskId, c.decision, c.model].some(v => v?.toLowerCase().includes(query))))
  })

  const { openStep, detail, loading, detailFailed } = useOpenedCall(at, calls)
  const position = computed(() => calls.value.findIndex(c => c.step === openStep.value))
  function move(delta: number) {
    const next = calls.value[position.value + delta]
    if (next) openStep.value = next.step
  }

  return { calls, agents, agent, search, pending: initialPending, error, refresh, openStep, detail, loading, detailFailed, position, move }
}
