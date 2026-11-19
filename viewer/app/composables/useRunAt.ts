import type { InjectionKey } from 'vue'
import type { RunRef } from '#shared/types/run'

const RUN_AT: InjectionKey<Ref<RunRef | null>> = Symbol('run-at')

/** The run a view shows, handed down to everything inside it that fetches more of that run (a plan, a call). */
export function provideRunAt(at: MaybeRefOrGetter<RunRef | null>): void {
  provide(RUN_AT, computed(() => toValue(at)))
}

export function useRunAt(): Ref<RunRef | null> {
  return inject(RUN_AT, ref(null))
}
