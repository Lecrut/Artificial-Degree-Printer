import type { EntryKind, EntryStatus, PhaseId } from '#shared/types/timeline'
import type { SourceKind } from '#shared/types/run'
import { thesisLabels } from './labelParts/thesis'
import { agentsLabels } from './labelParts/agents'
import { graphLabels } from './labelParts/graph'
import { launchLabels } from './labelParts/launch'
import { liveLabels } from './labelParts/live'
import { changelogLabels } from './labelParts/changelog'
import { historyLabels } from './labelParts/history'
import { compareLabels } from './labelParts/compare'
import { navLabels } from './labelParts/nav'

// Every text of the interface (ARCHITECTURE.md §3.6).
export const labels = {
  app: 'ADK Viewer',
  common: {
    copy: 'Kopiuj',
    prev: 'Poprzednie (←)',
    next: 'Następne (→)',
    arrows: '← → przełączają między elementami · Esc zamyka',
    loadError: 'Nie udało się wczytać danych z serwera viewera.',
    loadErrorHint: 'Sprawdź, czy serwer viewera (bun run dev) dalej działa; dane w repozytorium są nietknięte.',
    retry: 'Spróbuj ponownie',
    reconnecting: 'Brak połączenia ze strumieniem na żywo — przeglądarka ponawia próbę sama.',
  },
  tagline: 'przebiegi harnessu',
  tabs: { history: 'Historia', timeline: 'Oś czasu', graph: 'Hipergraf', agents: 'Agenci', thesis: 'Praca', live: 'Na żywo', changelog: 'Postęp', compare: 'Porównanie' },
  history: historyLabels,
  sources: { git: 'commit', results: 'na dysku', live: 'na żywo' } satisfies Record<SourceKind, string>,
  stats: {
    tasks: 'zadania',
    llmCalls: 'wywołania LLM',
    failedVerdicts: 'porażki weryfikacji',
    rejectedWrites: 'odrzucone zapisy',
    planVersions: 'wersje planu',
    replans: 'przebudowy i przeplanowania',
    duration: 'czas',
  },
  phases: {
    planning: 'Planowanie',
    building: 'Budowanie',
    repairs: 'Naprawy',
    replans: 'Przeplanowania',
    end: 'Koniec',
  } satisfies Record<PhaseId, string>,
  kinds: {
    plan: 'plan',
    graph: 'hipergraf',
    agent: 'agenci',
    task: 'zadania',
    queue: 'kolejki',
    replan: 'przeplanowania',
    evolution: 'ewolucja',
    end: 'koniec',
  } satisfies Record<EntryKind, string>,
  statuses: {
    ok: 'gotowe',
    fail: 'padło',
    warn: 'z uwagami',
    info: 'informacja',
    running: 'w toku',
    waiting: 'czeka',
  } satisfies Record<EntryStatus, string>,
  timeline: {
    onlyProblems: 'tylko problemy',
    search: 'szukaj pliku, zadania, treści',
    empty: 'Ten przebieg nie ma zdarzeń (events.jsonl) albo filtry wszystko ukryły.',
    attempts: 'przebieg zadania',
    moreLines: 'pokaż pełny komunikat',
    planWriting: 'Planista jeszcze pisze ten plan — pojawi się tu, gdy skończy.',
    planThesis: 'praca',
    planTasks: (n: number) => `zadania planu (${n})`,
    planInterfaces: 'interfejsy modułów',
    details: 'Szczegóły (dialog)',
    noDetails: 'Brak dodatkowych szczegółów dla tej pozycji.',
    problems: (n: number) => `${n} × błąd`,
    llm: (calls: number, seconds: number) => `${calls} wywołań LLM · ${Math.round(seconds)} s`,
  },
  run: { notFound: 'Nie udało się wczytać przebiegu.', noGraph: 'Ten przebieg nie zapisał hipergrafu.' },
  agents: agentsLabels,
  live: liveLabels,
  launch: launchLabels,
  changelog: changelogLabels,
  thesis: thesisLabels,
  graph: graphLabels,
  compare: compareLabels,
  nav: navLabels,
}
