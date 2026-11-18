<script setup lang="ts">
const { data, error, refresh } = await useFetch<{ roots: string[]; runs: Record<string, any>[] }>('/api/runs')
</script>

<template>
  <div>
    <div class="row" style="margin-bottom: 12px">
      <h1 class="grow">Przebiegi</h1>
      <button @click="refresh()">Odśwież</button>
    </div>
    <p v-if="error" class="muted">Błąd: {{ error.message }}</p>
    <p v-else-if="!data?.runs.length" class="muted">
      Brak przebiegów w: <code v-for="r in data?.roots" :key="r">{{ r }} </code>. Ustaw <code>VIEWER_RUN_ROOTS</code>.
    </p>
    <div class="grid">
      <NuxtLink v-for="run in data?.runs" :key="run.root + run.id" :to="`/run/${run.root}/${run.id}`" class="panel card">
        <div class="row">
          <b class="grow">{{ run.id }}</b>
          <span class="badge" :style="{ background: statusColor(run.status) }">{{ run.status }}</span>
        </div>
        <div class="muted title">{{ run.title || run.thesis_statement || '—' }}</div>
        <div class="row stats">
          <div class="stat"><b>{{ run.tasks_done }}/{{ run.tasks }}</b><span>zadania</span></div>
          <div class="stat"><b>{{ run.llm_calls }}</b><span>wywołania LLM</span></div>
          <div class="stat"><b>{{ run.failed_verdicts }}</b><span>porażki weryf.</span></div>
          <div class="stat"><b>{{ run.rejected_writes }}</b><span>odrzucone zapisy</span></div>
          <div class="stat"><b>{{ run.plan_attempts }}</b><span>wersje planu</span></div>
        </div>
        <div class="muted small">{{ run.started?.slice(0, 16).replace('T', ' ') }} · {{ fmtDuration(run.started, run.ended) }} · {{ data?.roots[run.root] }}</div>
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 12px; }
.card { color: var(--text); display: flex; flex-direction: column; gap: 8px; }
.card:hover { border-color: var(--accent); text-decoration: none; }
.title { font-size: 13px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.stats { gap: 16px; }
.small { font-size: 12px; word-break: break-all; }
</style>
