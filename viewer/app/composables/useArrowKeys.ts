interface ArrowHandlers {
  left?: () => void
  right?: () => void
  escape?: () => void
}

const TYPING = new Set(['INPUT', 'TEXTAREA', 'SELECT'])

/** ← / → (and Esc) while `active`, except while the user types in a field. */
export function useArrowKeys(active: MaybeRefOrGetter<boolean>, handlers: ArrowHandlers) {
  function onKey(event: KeyboardEvent) {
    if (!toValue(active) || TYPING.has((event.target as HTMLElement | null)?.tagName ?? '')) return
    const handler = { ArrowLeft: handlers.left, ArrowRight: handlers.right, Escape: handlers.escape }[event.key]
    if (!handler) return
    event.preventDefault()
    handler()
  }
  onMounted(() => window.addEventListener('keydown', onKey))
  onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
}
