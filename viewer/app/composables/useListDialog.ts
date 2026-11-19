/** A dialog over a list, driven by the index of the open item (`null` = closed). */
export function useListDialog<T>(index: Ref<number | null>, items: MaybeRefOrGetter<T[]>) {
  const open = computed({
    get: () => index.value !== null,
    set: (value: boolean) => { if (!value) index.value = null },
  })
  const current = computed(() => (index.value === null ? null : toValue(items)[index.value] ?? null))
  function move(delta: number) {
    if (index.value !== null) index.value = Math.min(toValue(items).length - 1, Math.max(0, index.value + delta))
  }
  return { open, current, move }
}
