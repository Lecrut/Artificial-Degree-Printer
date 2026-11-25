<script setup lang="ts">
import { mdiRestart } from '@mdi/js'
import type { LaunchProvider } from '#shared/types/live'
import type { RunRef } from '#shared/types/run'
import { taskKey } from '#shared/utils/launch'
import type { Snapshot } from '#shared/utils/snapshots'
import { labels } from '~/utils/labels'

// Continue a run from a saved state: the harness skips what is verified and builds only the rest. Without a
// snapshot it is the end state of the run; with one, the moment after that task (the run's `logs/snapshots/`).
const props = defineProps<{ at: RunRef, snapshot?: Snapshot | null, compact?: boolean, here?: boolean }>()
const deployed = useDeployed()
const open = ref(false)
const provider = ref<LaunchProvider>('ollama')
const busy = ref(false)
const error = ref<string | null>(null)
// A point of the run („stąd”) needs the snapshot saved there; runs from before snapshots have none.
const unavailable = computed(() => !!props.here && !props.snapshot)
const key = computed(() => taskKey(props.at.task))
const providers = Object.entries(labels.launch.providers).map(([value, title]) => ({ value, title }))
const where = computed(() => (props.snapshot ? labels.launch.snapshotInfo(props.snapshot) : labels.launch.endState))

async function resume() {
  busy.value = true
  error.value = null
  try {
    const from = { source: props.at.source, ref: props.at.ref, snapshot: props.snapshot?.file }
    await $fetch('/api/launch', { method: 'POST', body: { tasks: [key.value], provider: provider.value, template: null, resume: from } })
    open.value = false
    await navigateTo('/live?console=1')
  }
  catch (e) {
    error.value = (e as { statusMessage?: string }).statusMessage ?? String(e)
  }
  busy.value = false
}
</script>

<template>
  <span v-if="key && !deployed" @click.stop>
    <v-btn
      :prepend-icon="mdiRestart"
      :color="snapshot && !snapshot.failed ? 'success' : 'secondary'"
      variant="tonal"
      :size="compact ? 'x-small' : 'small'"
      :class="compact ? '' : 'mt-1'"
      :text="here || snapshot ? labels.launch.resumeHere : labels.launch.resume"
      :disabled="unavailable"
      :title="unavailable ? labels.launch.noSnapshot : undefined"
      @click="open = true"
    />
    <v-dialog v-model="open" max-width="520">
      <v-card :title="labels.launch.resumeTitle" :subtitle="`${at.task} · ${where}`">
        <v-card-text class="d-flex flex-column ga-4">
          <span class="text-body-2">{{ labels.launch.resumeHint }}</span>
          <v-select v-model="provider" :items="providers" :label="labels.launch.provider" hide-details />
          <v-alert v-if="error" type="error" variant="tonal" density="compact" :text="error" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn :text="labels.launch.cancel" @click="open = false" />
          <v-btn :loading="busy" color="primary" variant="flat" :prepend-icon="mdiRestart" :text="labels.launch.resume" @click="resume" />
        </v-card-actions>
      </v-card>
    </v-dialog>
  </span>
</template>
