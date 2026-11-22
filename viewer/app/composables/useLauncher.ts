import type { LaunchRequest, LaunchStatus } from '#shared/types/live'

const POLL_MS = 1500

/** The benchmark started from the viewer: its status and console, polled while the page is open. */
export function useLauncher() {
  const status = ref<LaunchStatus | null>(null)
  const error = ref<string | null>(null)
  const request = reactive<LaunchRequest>({ tasks: ['1'], provider: 'ollama', template: null })

  async function refresh() {
    status.value = await $fetch<LaunchStatus>('/api/launch').catch(() => status.value)
  }

  async function call(method: 'POST' | 'DELETE') {
    error.value = null
    try {
      status.value = await $fetch<LaunchStatus>('/api/launch', { method, body: method === 'POST' ? request : undefined })
    }
    catch (e) {
      error.value = (e as { statusMessage?: string }).statusMessage ?? String(e)
    }
  }

  let timer: ReturnType<typeof setInterval> | undefined
  onMounted(() => {
    void refresh()
    timer = setInterval(refresh, POLL_MS)
  })
  onBeforeUnmount(() => clearInterval(timer))

  return { status, error, request, start: () => call('POST'), stop: () => call('DELETE') }
}
