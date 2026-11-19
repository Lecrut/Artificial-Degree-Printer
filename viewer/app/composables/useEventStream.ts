const RETRY_MS = 3000

/**
 * A server-sent event stream that stays connected: the browser retries a dropped stream by itself,
 * but gives up after an error status — then this retries every few seconds.
 */
export function useEventStream<T>(url: string, onMessage: (message: T) => void) {
  const connected = ref(false)
  const failed = ref(false)
  let source: EventSource | null = null
  let retry: ReturnType<typeof setTimeout> | undefined

  function connect() {
    clearTimeout(retry)
    source?.close()
    source = new EventSource(url)
    source.onopen = () => {
      connected.value = true
      failed.value = false
    }
    source.onerror = () => {
      connected.value = false
      failed.value = true
      if (source?.readyState === EventSource.CLOSED) retry = setTimeout(connect, RETRY_MS)
    }
    source.onmessage = message => onMessage(JSON.parse(message.data) as T)
  }
  onMounted(connect)
  onBeforeUnmount(() => {
    clearTimeout(retry)
    source?.close()
  })

  return { connected, failed, reconnect: connect }
}
