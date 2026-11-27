import type { FlowText } from './flowSteps'

/** The agents: what each does and when it runs. The prompt itself comes from `adk/agents/` (the base version, not an evolved one). */
export const flowAgents: Record<string, FlowText> = {
  plan_outline: {
    label: 'plan_outline',
    note: 'Etap 1 planu: moduły z celem, zależnościami i obiecanymi nazwami, punkt wejścia, wykresy, metryki i rozdziały. Pisze go jeden agent, a poprawia na uwagach kodu i krytyka. Ten sam agent w trybie rewizji (pole revision) po nieudanej kolejce zwraca zarys i status każdego modułu: keep, change, new, remove.',
  },
  outline_critic_guard: {
    label: 'outline_critic_guard',
    note: 'Krytyk zarysu. Ocenia moduły, zależności, obiecane nazwy, eksperyment, metryki i rozdziały, zanim powstanie jakikolwiek interfejs; nie powtarza kontroli kodu. Blokuje w najwyżej dwóch rundach.',
  },
  plan_module: {
    label: 'plan_module',
    note: 'Etap 2 planu: deklaruje interfejs jednego modułu naraz (nazwy, sygnatury, docstringi), zależności najpierw. Zwraca szkic JSON bez miejsca na ciało funkcji; interfejs składa z niego harness. Pierwszą odpowiedź pisze mały model, każdą poprawkę duży. Widzi zaakceptowane interfejsy, na których się opiera, i może poprosić zależność o brakujące elementy.',
  },
  module_critic_guard: {
    label: 'module_critic_guard',
    note: 'Krytyk interfejsu jednego modułu: sprawdza go po tym, jak przeszły kontrole kodu. Jedna runda blokująca.',
  },
  plan_critic_guard: {
    label: 'plan_critic_guard',
    note: 'Etap 4 planu: krytyk główny ocenia cały plan (zarys, interfejsy, zadania) po złożeniu. Do dwóch rund może odesłać część planu.',
  },
  seed_coder: {
    label: 'seed_coder',
    note: 'Buduje i naprawia moduły kodu. Dostaje zadanie i wycinek hipergrafu swojego pliku (interfejs, zależności, testy), a nie całą wiedzę o projekcie.',
  },
  seed_tester: {
    label: 'seed_tester',
    note: 'Pisze testy modułów. Test musi pasować do zamrożonego interfejsu; na stubach może padać tylko NotImplementedError.',
  },
  seed_writer: {
    label: 'seed_writer',
    note: 'Pisze rozdziały pracy (thesis.md). Liczby i symbole z kodu cytuje wskaźnikami \\ref_csv, \\ref_ast i \\ref_fig, które kompilator rozwiązuje na prawdziwe wartości.',
  },
  background_researcher: {
    label: 'background_researcher',
    note: 'Pierwszy etap badań literatury: podstawy dziedziny. Plan wybiera etapy według typu pracy: magisterska ma podstawy i najnowsze prace, artykuł tylko najnowsze, pozostałe podstawy.',
  },
  discoverer_researcher: {
    label: 'discoverer_researcher',
    note: 'Drugi etap badań: najnowsze prace (mniej więcej z ostatnich trzech lat), ich metody oceny i luka badawcza, którą wypełnia ta praca. Występuje w pracach magisterskich i artykułach.',
  },
  sota_researcher: {
    label: 'sota_researcher (opcjonalnie)',
    note: 'Przegląd literatury (stan wiedzy) z zweryfikowanych kluczy bibliograficznych. Etapowy plan przydziela dziś badania agentom background i discoverer, więc ten pojawia się tylko, gdy plan sam go wskaże.',
  },
  task_planner: {
    label: 'task_planner',
    note: 'Przeplanowanie nieudanych wierzchołków: pierwsza reakcja na koniec kolejki z porażkami, a potem znów, gdy rundy przeprojektowania są wyczerpane albo ich wytyczne nie przeszły. Dostaje akta napraw (co próbowano i jaki był błąd) i zmienia zadania albo interfejsy tylko nieudanych fragmentów; zweryfikowanych nie rusza.',
  },
  plan_change_guard: {
    label: 'plan_change_guard',
    note: 'Sędzia zmiany interfejsu (duży model). Gdy ten sam błąd powtarza się jako naruszenie interfejsu, decyduje: AMEND (interfejs jest zły i się zmienia) albo zostaje, razem z uzasadnieniem dla autora.',
  },
  evolution_architect: {
    label: 'evolution_architect',
    note: 'Samoewolucja (warstwa 4, duży model). Widzi wzorzec porażek jednego agenta w kilku zadaniach i proponuje regułę do jego promptu, albo zgłasza błąd harnessu, gdy reguła nic nie da.',
  },
  prompt_consolidator: {
    label: 'prompt_consolidator',
    note: 'Gdy agent zbierze w sekcji LEARNED RULES cztery reguły, mechanizm zmiany promptu (agent_mutator) wzywa konsolidatora, który redaguje prompt całościowo, żeby nie rósł i nie sprzeczał sam sobie.',
  },
  remediation_planner: {
    label: 'remediation_planner',
    note: 'Planuje chirurgiczną naprawę dla plików spoza hipergrafu (np. thesis.md). Dla kodu z hipergrafu jest pomijany: te naprawy przejmuje przeplanowanie.',
  },
  implementation_auditor: {
    label: 'implementation_auditor',
    note: 'Audyt implementacji (mały model, jedno wywołanie na plik, wynik zapamiętany po odcisku pliku): czyta kod jednego modułu i opisuje słowami, co każda funkcja bierze, zwraca i jak liczy, czy plik zgadza się z interfejsem z planu i co jest podejrzane. Jedyne miejsce, w którym czyta się ciała funkcji; projektant dostaje same opisy. Fakty (deklaracje, wywołania, wyjątki, kto kogo używa, testy, błędy) liczy kod z drzewa AST, więc nie da się ich zmyślić.',
  },
  code_auditor: {
    label: 'code_auditor',
    note: 'Obrona końcowa, krok 1 (mały model): ocena kodu na podstawie raportu testów. Działa tylko w Gate 3; przy zadaniach pośrednich weryfikacja jest deterministyczna.',
  },
  symbolic_auditor: {
    label: 'symbolic_auditor',
    note: 'Obrona końcowa, krok 2 (mały model): ocena wskaźników, plików CSV i bibliografii w pracy. Działa tylko w Gate 3.',
  },
  redteam_critic_guard: {
    label: 'redteam_critic_guard',
    note: 'Obrona końcowa, krok 3 (mały model): czerwony zespół ocenia całość, łącznie z zadeklarowanymi metrykami. Jego opinie są ostrzeżeniami; błędem jest dopiero to, co udowodnił harness.',
  },
}
