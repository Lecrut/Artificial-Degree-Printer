import type { FlowEdgeLabel, FlowKind } from '#shared/types/flow'
import { flowAgents } from './flowAgents'
import { flowSteps, type FlowText } from './flowSteps'

/** Texts of the flow page: the page itself, the answers on the arrows, and one label and note per block. */
export const flowLabels = {
  title: 'Przepływ systemu',
  subtitle: 'Od startu do końca, od góry do dołu: kto po kim działa, gdzie jest „jeśli” i dokąd wracają pętle. Kliknij blok, żeby zobaczyć opis, a dla agenta jego prompt.',
  legend: 'Legenda',
  kinds: {
    start: 'Start / koniec',
    end: 'Start / koniec',
    step: 'Krok harnessu (bez modelu)',
    agent: 'Agent (model z promptem)',
    decision: 'Rozgałęzienie „jeśli”',
    jump: 'Powrót do wcześniejszego kroku',
  } satisfies Record<FlowKind, string>,
  edges: {
    yes: 'tak',
    no: 'nie',
    code: 'kod',
    test: 'test',
    doc: 'dokument',
    research: 'literatura',
    more: 'kolejny etap',
    budget: 'jest budżet',
    spent: 'wyczerpany',
  } satisfies Record<FlowEdgeLabel, string>,
  details: {
    kind: 'Rodzaj',
    prompt: 'Prompt agenta',
    promptHint: 'Prompt bazowy z adk/agents. Prompt, który agent dostał w konkretnym przebiegu (z regułami z ewolucji), jest w widoku Agenci.',
    loading: 'Wczytuję prompt…',
    missing: 'Nie znaleziono pliku z promptem tego agenta.',
    close: 'Zamknij',
    noPrompt: 'Ten blok nie jest agentem, więc nie ma promptu: robi to sam harness.',
  },
  nodes: { ...flowSteps, ...flowAgents } as Record<string, FlowText>,
}
