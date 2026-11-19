/** Seconds since `since`, ticking every second while the component is mounted. */
export function useSecondsSince(since: MaybeRefOrGetter<string | null | undefined>) {
  const now = ref(Date.now())
  let timer: ReturnType<typeof setInterval> | undefined
  onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 1000) })
  onBeforeUnmount(() => clearInterval(timer))
  return computed(() => {
    const at = toValue(since)
    return at ? Math.max(0, Math.round((now.value - Date.parse(at)) / 1000)) : 0
  })
}
