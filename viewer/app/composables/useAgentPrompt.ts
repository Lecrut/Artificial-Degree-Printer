import type { AgentPrompt } from '#shared/types/flow'

/** The base prompt of the agent `name` (null = none wanted), fetched when the name appears or changes. */
export function useAgentPrompt(name: Ref<string | null>) {
  const { data, status, execute } = useFetch<AgentPrompt>(() => `/api/agents/${name.value ?? ''}`, { lazy: true, immediate: false, watch: false })
  watch(name, (next) => { if (next) void execute() }, { immediate: true })
  // A slow answer for the previous agent must not show under the new one.
  const prompt = computed(() => (data.value?.name === name.value ? data.value : null))
  return { prompt, loading: computed(() => name.value !== null && !prompt.value && status.value !== 'error'), failed: computed(() => status.value === 'error') }
}
