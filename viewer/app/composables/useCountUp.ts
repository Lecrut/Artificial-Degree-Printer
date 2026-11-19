const DURATION_MS = 900
const easeOut = (t: number) => 1 - (1 - t) ** 3

/** A number that runs up to its target (and from one target to the next); instant when the system asks for less motion. */
export function useCountUp(target: MaybeRefOrGetter<number>) {
  const shown = ref(0)
  const still = import.meta.client && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  let frame = 0

  watch(() => toValue(target), (to) => {
    cancelAnimationFrame(frame)
    if (still) return void (shown.value = to)
    const from = shown.value
    const start = performance.now()
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / DURATION_MS)
      shown.value = from + (to - from) * easeOut(t)
      if (t < 1) frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
  }, { immediate: true })
  onBeforeUnmount(() => cancelAnimationFrame(frame))

  return shown
}
