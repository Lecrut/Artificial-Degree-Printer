# ADK Viewer — dokument projektowy

Przeglądarka przebiegów harnessu ADK: historia benchmarków z commitów, podgląd trwającego przebiegu i jego uruchamianie.
Ten dokument jest źródłem prawdy dla kodu w `viewer/`; zmiana zasad = zmiana tutaj najpierw.

## 1. Cel

| Zakładka | Pytanie, na które odpowiada |
|---|---|
| **Historia** | Jak wypadły dotychczasowe benchmarki? (kafelek na commit z wynikami w `adk/workspace/benchmarks`) |
| **Porównanie** | Czym różnią się przebiegi (do 4)? Czas, wywołania, czas obliczeń SML/LRM, ≈ tokeny, postęp w czasie, agenci — na wspólnych wykresach, z różnicą względem pierwszego. |
| **Na żywo** | Co harness robi teraz? Co z planu jest gotowe, co padło, co się toczy, który agent myśli? |
| **Przepływ** | Jak system działa krok po kroku? Który agent po którym, gdzie są rozgałęzienia i pętle, i jaki prompt ma każdy agent (klik w agenta). |
| **Na żywo → panel „Uruchom / konsola”** | Start i stop benchmarku oraz konsola w panelu z prawej strony podglądu na żywo (dawna strona `/launch` przekierowuje tutaj z otwartym panelem). |

Widok jednego przebiegu jest wspólny dla Historii i Na żywo: **Oś czasu** (plan i jego wykonanie), **Hipergraf**, **Agenci**, **Praca**.

Poza zakresem: edycja czegokolwiek w `adk/`, czytanie `.env`. Praca na innym komputerze niż lokalny — tylko historia, przez wersję wdrożoną (§13).

## 2. Stack

| Warstwa | Wybór | Wersja (≥ 2 tyg., sprawdzone 2026-11-18) |
|---|---|---|
| Framework | Nuxt 4 (`app/`, `server/`, `shared/`) | `nuxt` 4.6.4 |
| UI | Vuetify przez `vuetify-nuxt-module` | `vuetify` 4.3.2, `vuetify-nuxt-module` 0.19.5 |
| Ikony | `@mdi/js` (zestaw `mdi-svg`, bez fontu) | najnowsza ≥ 2 tyg. |
| Język | TypeScript `strict` | `typescript` 5.9.3, `vue-tsc` 3.3.14 |
| Graf | Cytoscape (tylko klient) | `cytoscape` 3.34.4 |
| Markdown | markdown-it | `markdown-it` 14.3.3 |
| Wykresy | ECharts przez `vue-echarts` (tylko porównanie; rejestrowane tylko linie i słupki) | `echarts` 6.1.0, `vue-echarts` 8.3.2 |
| Narzędzia | Bun (instalacja, uruchamianie, testy `bun test`), ESLint przez `@nuxt/eslint` | `bun` 1.3, `@nuxt/eslint` 1.17.0, `eslint` 10.14.0 |

Uruchomienie: `cd viewer && bun install && bun run dev` (port 3000, tylko `127.0.0.1`). Kontrola: `bun run lint`, `bun run typecheck`, `bun test`.

Storybook: `bun run storybook` (port 6006) — `@nuxtjs/storybook` 10.0.3 / `storybook` 10.6.5, framework `@storybook-vue/nuxt` (startuje prawdziwą aplikację Nuxt, więc Vuetify, motyw i auto-importy działają jak w viewerze). Stories w `stories/*.stories.ts`, dane z prawdziwego przebiegu 18.11 w `stories/fixtures/` (`hypergraph.json`, `timeline.json`; `bun stories/fixtures/build.ts <events.jsonl>` odtwarza oś czasu). Vuetify jest tree-shakowany: komponenty `v-*` użyte w szablonach-stringach stories i dekoratora trzeba zaimportować z `vuetify/components`.

ESLint pilnuje zasad z §3: zakaz bloków `<style>`, atrybutów i bindowań `style`, limit 160 linii na plik i 40 na funkcję (poza testami).

## 3. Zasady kodu

1. **Bez własnego CSS.** Motyw jeden, ciemny: granatowe powierzchnie, wyrazisty szmaragdowy akcent (`primary`), zdefiniowany w `vuetify.config.ts`; animacje z przejść Vuetify (`v-slide-y-transition`, `v-fade-transition`, `v-expand-transition`). Żadnych bloków `<style>`, plików `.css`, atrybutów `style`. Wygląd = komponenty Vuetify, ich propsy (`color`, `variant`, `density`, `elevation`) i klasy narzędziowe Vuetify (`d-flex`, `ga-2`, `pa-4`, `text-medium-emphasis`, `text-truncate`). Kolory tylko z motywu (`primary`, `success`, `error`, `warning`, `info`, `surface-variant`). Zaokrąglenia i warianty to domyślne propsy w `vuetify.config.ts` (karty `xl`, chipy, przyciski i pola `pill`), nie atrybuty w szablonach. Jedyny wyjątek: `app/spa-loading-template.html` (ekran startowy przed załadowaniem aplikacji — Vuetify jeszcze nie istnieje, więc ma własne kilka linii CSS, kolory z motywu). **Animacje** (wszystkie wyłączają się przy `prefers-reduced-motion`): przejście `fade-transition` między stronami, szkielety `CommonPageSkeleton` w czasie ładowania, liczby odliczane do wartości (`CommonCountUp` / `useCountUp`), poświata wierzchołka zmieniającego stan w odtwarzaniu hipergrafu (`flashClass('changed')`), przejścia Vuetify w listach i oknach, rysowanie wykresów ECharts.
2. **Logika w composables, komponenty prezentują.** Komponent dostaje dane przez propsy, emituje zdarzenia, nie liczy niczego poza formatowaniem. Pobieranie, przekształcanie, filtrowanie, stan — w `use*`.
3. **Czyste funkcje w `shared/utils`.** Mapowanie zdarzeń na oś czasu, stany, kolory, formatowanie — funkcje bez Vue, testowane `bun test`, używane przez klienta i serwer.
4. **Typy w `shared/types`.** Jeden opis danych dla serwera i klienta; żadnych `any` w API.
5. **Małe pliki.** Komponent ≤ ~120 linii, composable ≤ ~80, funkcja ≤ ~30. Jeden plik = jedna odpowiedzialność. Za duże → podział, nie wyjątek.
6. **Nazwy po angielsku, teksty interfejsu po polsku.** Teksty interfejsu w `app/utils/labels.ts` i jego częściach `app/utils/labelParts/*` (jak `agent_texts.py` w harnessie).
7. **Serwer tylko czyta**, z jednym wyjątkiem: `server/api/launch/*` uruchamia i zatrzymuje proces. Żadnych importów z `adk/`; styk z harnessem = pliki, git, CLI `main.py`.
8. **Błąd danych nie psuje strony.** Brakujący plik (stare commity nie mają `events.jsonl`) = pusta sekcja z informacją, nie wyjątek. **Ładowanie i błąd to dwa różne stany, żaden nie udaje „braku danych”:** w trakcie — `CommonPageSkeleton` albo szkielet w miejscu treści (komunikat „brak pliku” dopiero po załadowaniu); błąd serwera — `CommonLoadError` z „Spróbuj ponownie” (`refresh()` z `useFetch`/`useAsyncData`); strumień na żywo po odmowie ponawia połączenie co 3 s; szczegóły wywołania pokazują tylko odpowiedź dla wciąż otwartego kroku (szybkie ← → nie mieszają odpowiedzi). Teksty Vuetify (tabele, paginacja) po polsku: `locale: pl` w `vuetify.config.ts` — zmiana tego pliku wymaga restartu `bun run dev`.
9. **Jeden kształt dla jednej rzeczy.** Okno elementu listy z ← → i Esc = `CommonBrowseDialog` + `useListDialog`; klikalna karta = `CommonHoverCard` (ramka w kolorze akcentu, bo cień na granacie jest niewidoczny); adresy przebiegu = `app/utils/runUrls.ts`; kolory statusów, werdyktów, tierów i kolejki = `shared/utils/colors.ts`; ikony = `app/utils/icons.ts`; JSON, który może być ucięty = `shared/utils/json.ts`. Nowy widok składa się z tych klocków, nie kopiuje ich.
10. **Telefon też.** Bez poziomego przewijania strony przy 390 px; pasek zakładek pokazuje wtedy same ikony, hipergraf startuje w widoku macierzy.
11. **Wykresy według metody dataviz.** Kolory serii przebiegów `SERIES_COLORS` i tierów `TIER_COLORS` (`shared/utils/compare.ts`) przeszły walidator palety na tle `#0a1430` (pasmo jasności, odstęp dla daltonistów, kontrast); kolor należy do przebiegu, nie do miejsca na liście. Jedna oś Y na wykres, linie 2 px, legenda + etykiety na końcu linii, podpowiedź pokazuje wszystkie przebiegi w danej minucie. Napisy w kolorach tekstu motywu (`useChartInk`), nie w kolorze serii. Brak danych = „—” i brak linii, nigdy fałszywe zero.

## 4. Źródła danych

Jeden interfejs, trzy implementacje (`server/utils/sources/`):

```ts
interface RunSource {
  listTasks(): Promise<string[]>                      // 01_rl_tictactoe, ...
  readText(task: string, rel: string): Promise<string | null>
  exists(task: string, rel: string): Promise<boolean>
}
```

| Źródło | `ref` | Skąd czyta | Uwagi |
|---|---|---|---|
| `git` | sha commita | `git show <sha>:adk/workspace/benchmarks/<task>/<rel>` | niezmienne → cache w pamięci po `(sha, ścieżka)` |
| `results` | `current` | `adk/workspace/benchmarks/<task>/<rel>` | ostatnie wyniki na dysku |
| `live` | `current` | `adk/workspace/benchmarks/_evolved_adk_state/<task>/` (`workspace/logs/`, `state/`) | pliki dopisywane w trakcie przebiegu |

Ścieżki w obrębie przebiegu (różne między źródłami, mapuje je `server/utils/layout.ts`):

| Co | `results` / `git` | `live` |
|---|---|---|
| zdarzenia | `logs/events.jsonl` | `workspace/logs/events.jsonl` |
| ślad agentów | `logs/agent_trace.jsonl` | `workspace/logs/agent_trace.jsonl` |
| hipergraf, kolejka, blueprint | `evolved_adk/state/*.json` | `state/*.json` |
| praca, wyniki | `thesis/`, `results/` | `workspace/` |

Commity historii: `git log --format=%H%x09%aI%x09%s -- adk/workspace/benchmarks`. Podsumowanie zadania z jego `events.jsonl`; przebiegi sprzed 17.11 nie mają tego pliku — wtedy status, wywołania LLM, przebudowy i czas pochodzą z `benchmark_summary.json` obok folderów zadań (`server/utils/legacySummary.ts`).

## 5. API (Nitro, `server/api/`)

| Metoda i ścieżka | Zwraca |
|---|---|
| `GET /api/history` | `CommitSummary[]` |
| `GET /api/changelog` | `Changelog`: sekcje audytu z datami i wszystkie commity ze statystyką zmian |
| `GET /api/runs/:source/:ref` | `TaskSummary[]` |
| `GET /api/runs/:source/:ref/:task` | `RunBundle` (zdarzenia, hipergraf, blueprint, kolejka, lista plików) |
| `GET /api/runs/:source/:ref/:task/calls` | `AgentCallSummary[]` (bez promptów) |
| `GET /api/runs/:source/:ref/:task/calls/:step` | `AgentCallDetail` (payload, odpowiedź, prompt systemowy) |
| `GET /api/agents/:name` | `AgentPrompt`: prompt bazowy agenta z `adk/agents/<grupa>/<name>.md` (nazwa tylko `[a-z_]`, szukana na liście plików, nie składana w ścieżkę) |
| `GET /api/runs/:source/:ref/:task/file?path=` | plik (obraz, PDF, CSV, markdown) |
| `GET /api/live/stream` | SSE: nowe zdarzenia i zmiany stanu trwającego przebiegu |
| `GET /api/launch` | `LaunchStatus` (czy działa, PID, argumenty, ostatnie linie konsoli) |
| `POST /api/launch` | start: `{ tasks, provider, template?, resume? }` → `main.py --benchmark-task … --provider …`; `resume: { source, ref }` (jedno zadanie) dodaje `--resume-from <folder stanu albo zip migawki>` (`resume.snapshot` = plik z `logs/snapshots/`): z dysku (`results`, `live` — odmowa, gdy przebieg pisał w ostatnich 2 min) albo wypakowany z commita (`git archive`). Przyciski „Wznów od tego stanu” (nagłówek przebiegu), „Wznów stąd” przy zadaniu na osi czasu i przy replayu hipergrafu (ostatnia migawka sprzed wybranego momentu; zielony = bez błędów) |
| `DELETE /api/launch` | stop procesu |

`:source` ∈ `git | results | live`. Każda trasa waliduje parametry (`zod` z `h3` `getValidatedRouterParams`), ścieżki plików nie mogą wyjść poza przebieg.

## 6. Model danych (`shared/types/`)

- `RunEvent` — linia `events.jsonl` (`ts`, `event`, pola zdarzenia). Typy zdarzeń jako unia literałów.
- `TaskSummary` — status (`RUN_END`), czas, zadania gotowe/wszystkie, wywołania LLM, porażki weryfikacji, odrzucone zapisy, wersje planu, przeplanowania.
- `CommitSummary` — sha, data, wiadomość, `TaskSummary[]`.
- `Hypergraph` — `vertices` (`kind`, `state`, `attempts`, `failures`, `history`, `last_writer`, `files`), `edges` (`type`, `members` z rolami, `spec`, `fingerprint`, `observed`), `order`.
- `AgentCallSummary` / `AgentCallDetail` — z `agent_trace.jsonl` (`phase` request/answer/error) połączone z `LLM_CALL_END` po `step`.
- `TimelineEntry` — pozycja osi czasu (rozdz. 7).

## 7. Oś czasu (plan jako timeline)

Główny widok przebiegu. Pokazuje plan i jego wykonanie w kolejności, w jakiej się działo.

**Na górze: pasek faz** (`v-timeline direction="horizontal"`, `density="compact"`):

`Planowanie → Budowanie → Naprawy → Przeplanowania → Gate 3 → Koniec`

Każda faza z liczbą pozycji i kolorem stanu (zielona: przeszła, czerwona: padła, niebieska: trwa). Klik przewija do fazy.

**Pod spodem: oś pionowa** (`v-timeline side="end" density="compact"`), jedna pozycja na wydarzenie istotne dla człowieka:

| Pozycja | Z jakich zdarzeń | Kropka | Rozwinięcie (`v-expansion-panels`) |
|---|---|---|---|
| Etap planu (od 2026-11-21, §XVI harnessu) | `PLAN_OUTLINE_CHECKED`/`_ACCEPTED`/`_REVISED` („Szkic planu”, „Rewizja szkicu”), `PLAN_MODULE_CHECKED`/`_ACCEPTED`/`_REOPENED`/`_NEEDS` („Interfejs <moduł>”), `PLAN_FUSED` („Plan złożony”) | `error` po próbie z uwagami, `success` po przyjęciu | próby z problemami kodu i blokadami krytyka, zastrzeżenia przyjęte ponad krytykiem, powody ponownego otwarcia, czego moduł potrzebował od zależności |
| Wersja planu | `PLAN_CHECKED` (+ `PLAN_REVIEWED`, `PLAN_PATCHED` w przebiegach sprzed etapów) | `error` z blokadami, `success` bez | naruszenia kodu, uwagi krytyka (głównego od §XVI), co łatka zmieniła / naprawiła / zepsuła |
| Hipergraf zbudowany | `H_BUILT` | `primary` | liczba wierzchołków, worków |
| Nowy agent | `AGENT_CREATED` | `secondary` | specjalizacja |
| **Zadanie** | `TASK_START` … `TASK_DONE` / `TASK_FAILED` / `TASK_DEFERRED`, wszystkie `VERDICT` pomiędzy | stan końcowy zadania | **zagnieżdżona mini-oś prób**: każda próba = werdykt (błędy, ostrzeżenia), model, agent; odrzucone odpowiedzi; zmiana planu (`SPEC_AMENDED`/`SPEC_KEPT`) |
| Czekanie | `TASK_WAITING` | `grey` | na co czeka |
| Przeplanowanie | `REPLANNED` | `warning` | nieudane wierzchołki, nowe zadania, odrzucone propozycje, luki |
| Przeprojektowanie (od 2026-11-25, §XXVIII.8 harnessu) | `REDESIGN_STARTED`, `IMPLEMENTATION_AUDITED`, `REDESIGN_SOURCE_GRANTED` („Projektant czyta kod”), `REDESIGN_GUIDELINES`, `REDESIGN_APPLIED`, `REDESIGN_FALLBACK` (`shared/utils/timeline/redesign.ts`) | `running` / `info` / `ok`, `warning` przy problemach w odpowiedzi projektanta i przy wycofaniu | decyzja dla każdego modułu (zostaje / zmieniony / nowy / usunięty, z powodem) i diagnoza nieudanych, co zastosowano (od nowa, usunięte, zachowane), zadania `D<n>_…`; przy wycofaniu powód i problemy. Wszystkie w fazie „Przeplanowania”, tak jak zadania `D<n>_…` |
| Ewolucja | `AGENT_MUTATED`, `HARNESS_BUG_REPORTED` | `secondary` | reguła, agent |
| Dane | `DATA_PRODUCED`, `DATA_STALE`, `DATA_FAILED` | `info` / `warning` / `error` | błąd eksperymentu |
| Koniec | `RUN_END`, `RUN_STOPPED` | stan przebiegu | luki |

Zasady:
- Mapowanie zdarzeń → `TimelineEntry` to czysta funkcja `buildTimeline(events)` w `shared/utils/timeline/` (`builder.ts` stan przejścia, `plan.ts`, `planStages.ts` (etapy planowania: wywołania autorów i krytyków etapów liczone do wpisu ich części), `tasks.ts`, `misc.ts` obsługa zdarzeń, `index.ts` złożenie i fazy). Zadanie grupuje swoje naprawy (`T5_FIX1` → `T5`), ale `Q3_FIX1` z przebudowanej kolejki zostaje osobnym zadaniem. Testy: `shared/utils/timeline/timeline.test.ts` (przypadki) i `tests/timeline.real.test.ts` (prawdziwy przebieg 01).
- `LLM_CALL_*` nie są osobnymi pozycjami — zasilają liczniki i rozwinięcie zadania (który agent, ile razy, ile sekund).
- Filtry (`v-chip-group`): typy pozycji, „tylko problemy”. Wyszukiwanie po pliku/wierzchołku.
- Na żywo oś rośnie od dołu; ostatnia pozycja ma stan „trwa” i pokazuje bieżące wywołanie agenta.

## 8. Pozostałe widoki przebiegu

- **Przegląd** (nagłówek przebiegu, `v-card` + `v-chip`): status, czas, liczniki z `TaskSummary`.
- **Hipergraf**: dwa widoki — graf (Cytoscape w `ClientOnly`, klik w worek wygasza wszystko poza jego członkami) i macierz incydencji (`shared/utils/incidence.ts`: wiersze = wierzchołki, kolumny = worki, chip roli P/C/T/O/X, obrys = członek dopisany z obserwacji); wierzchołki = pliki/rozdziały (kolor stanu), worki = romby (I/R/N), krawędzie z rolą; panel szczegółów (`v-navigation-drawer location="end"`) dla klikniętego elementu; `v-slider` odtwarzania — stany wierzchołków po `VERTEX_STATE` do wybranej chwili.
- **Agenci**: `v-data-table` wywołań (krok, agent, model, czas, zadanie, werdykt, decyzja; na żywo domyślnie od najnowszego kroku na górze, wraz z aktualnie trwającym wywołaniem `request` ze statusem „w toku”); szczegóły w `v-dialog`: payload i odpowiedź jako drzewo (`v-treeview`), prompt systemowy zwinięty.
- **Praca**: `thesis.md` przez markdown-it z wyróżnionymi wskaźnikami `\ref_*` (`v-chip` w treści), `results.csv` w `v-data-table`, rysunki, link do PDF.

## 9. Na żywo i Uruchom

- **Na żywo**: SSE `/api/live/stream` — serwer obserwuje pliki piaskownicy (odczyt przyrostowy `events.jsonl` od ostatniego offsetu oraz znaczniki zmian hipergrafu/kolejki i `agent_trace.jsonl`), wysyła nowe `RunEvent`, stan hipergrafu/kolejki oraz sygnał `trace` dla nowych wywołań agentów. Klient: `useLiveRun()` aktualizuje `events`, `hypergraph`, `queue` i `traceStamp`, dzięki czemu oś czasu, hipergraf i zakładka **Agenci** (lista wywołań, rozwinięty podgląd i otwarte okno szczegółów) odświeżają się na żywo. Dodatkowo tablica zadań (`v-row` z kolumnami: czeka / w toku / gotowe / padło / odłożone) i karta „Teraz” (otwarty `LLM_CALL_START`: agent, zadanie, model, sekundy).
- **Uruchom**: formularz (`v-select` zadania 01–04 / cały pakiet, dostawca `mock`/`ollama`/`google`, szablon), Start/Stop, konsola (`v-sheet` z ostatnimi liniami). Serwer: jeden proces naraz (`child_process.spawn` z `.venv` Pythonem, `cwd` = korzeń repo), status w pamięci, `.env` nietykany (dostawca tylko flagą).

## 9a. Porównanie i nawigacja

**Porównanie** (`/compare?runs=git:362092f:01_rl_tictactoe,…`): wybór jest w adresie, więc link do porównania da się wysłać; przycisk „Porównaj” w nagłówku przebiegu otwiera je z tym przebiegiem, a „to samo zadanie w ostatnich commitach” wybiera jednym kliknięciem. `runProfile(events)` liczy z `events.jsonl` sumy (czas obliczeń `LLM_CALL_END.elapsed_s` ogółem i na tier, `LLM_CALL_START.prompt_chars`, wywołania i czas na agenta) i sumy narastające w minutach od startu. Modele są lokalne, więc „koszt” = czas obliczeń, a tokeny = znaki / 4 (podpisane jako szacunek; `prompt_chars` jest od 18.11). Przebiegi sprzed 17.11 nie mają zdarzeń: w tabeli mają tylko czas, wywołania i przebudowy z `benchmark_summary.json`, na wykresach ich nie ma.

**Planowanie na osi czasu** to trzy kroki z własnymi wpisami: „Plan początkowy” / „Poprawka planu N” (wywołanie `task_planner`, od startu ze statusem „w toku”), „Weryfikacja planu N” (wywołanie `plan_critic_guard` + `PLAN_CHECKED`). Wpis planisty pamięta numer wywołania (`entry.step`), a okno i rozwinięty kafelek pokazują sam plan z odpowiedzi w `agent_trace.jsonl` (`TimelinePlanView`: praca, zadania, interfejsy); adres przebiegu dostaje przez `provideRunAt`/`useRunAt`.

**Płynność:** strumień na żywo oddaje nowe zdarzenia paczką najwyżej raz na sekundę (`useLiveRun`), połączenie i ponawianie w `useEventStream`; karty commitów renderują się przy przewijaniu (`v-lazy`); układ grafu liczy się po animacji zakładki; bez przejść między stronami (czekanie 0,3 s przed każdym ciężkim montowaniem).

**Nawigacja:** na desktopie wąski pasek z ikonami po lewej, rozwijany po najechaniu; na telefonie dolny pasek. **Ctrl K** (albo przycisk w pasku) otwiera paletę: wszystkie strony i wszystkie przebiegi (commit × zadanie, wyniki na dysku), filtr po każdym wpisanym słowie, ↑ ↓ i Enter.

## 9b. Przepływ systemu

Strona `/flow` (tylko lokalnie, jak Na żywo: czyta `adk/agents/`): schemat blokowy od **Start** do **Koniec**, od góry do dołu — krok bez modelu (prostokąt), agent (zaokrąglony prostokąt), rozgałęzienie „jeśli” (romb) i strzałki; pętle (powrót do wcześniejszego kroku) są przerywane. Klik w blok otwiera boczny panel: opis kroku i, dla agenta, jego prompt (markdown).

- **Źródło prawdy o przepływie** to `shared/utils/flow/` (węzły z pozycją `col`/`row`, krawędzie z etykietą); teksty po polsku w `app/utils/labelParts/flow.ts`. To ręczny opis kodu harnessu (`orchestrator.run`, `plan_stages`, `building`, `verification`, `repair`, `fragment_replan`), nie generowany: zmiana przepływu w harnessie = zmiana tutaj.
- **Pilnuje go test** (`flow.test.ts`): każdy plik promptu w `adk/agents/` jest na schemacie i odwrotnie, krawędzie wskazują istniejące węzły, każdy węzeł ma tekst.
- **Prompt bazowy**, nie wyewoluowany: prompt konkretnego wywołania w przebiegu jest w widoku Agenci.
- Układ: Cytoscape z pozycjami z danych (`preset`), bez automatycznego układu — kolejność i kolumny są decyzją autora schematu.

## 10. Struktura katalogów

```
viewer/
  nuxt.config.ts            # vuetify-nuxt-module, @nuxt/eslint; ssr: false; 127.0.0.1:3000
  vuetify.config.ts         # motyw „adk” (granat + szmaragd), ikony mdi-svg, domyślne propsy (zaokrąglenia)
  eslint.config.mjs         # zakaz style, limity linii
  shared/                   # bez Vue: wspólne dla serwera i klienta, testy *.test.ts obok
    types/                  # run, hypergraph, timeline, calls, live, changelog
    utils/
      timeline/             # buildTimeline: builder, plan, tasks, misc
      events, json, summary, replay, graph, incidence, roles, states, colors, format,
      historyStats, audit, changelogDays, live, markdown, csv, jsonTree, compare (runProfile, valueAt, klucze, kolory)
  server/
    utils/sources/          # RunSource: gitSource (git show), fsSource (results, live), types, index
    utils/                  # repo (git), runLayout, runBundle, legacySummary, history, calls, changelog, live, launcher, params
    api/                    # history, changelog, runs/[source]/[ref]/[task]/{index,file,calls}, live/stream (SSE), launch
  app/
    app.vue                 # pasek z logo i wyszukiwaniem; boczny pasek (desktop) albo dolny (telefon); paleta Ctrl K
    pages/                  # index (Historia), compare (Porównanie), changelog (Postęp), live, launch, run/[source]/[ref]/[task]
    components/
      common/               # BrowseDialog, HoverCard, Chart (ECharts), PageHeader, StatusChip, CopyButton
      nav/                  # AppRail (ikony, rozwija się po najechaniu), BottomNav, CommandPalette (Ctrl K)
      compare/              # RunPicker, MetricTable, OverTimeCharts, AgentBars, TierSplit
      history/              # KpiTiles, HistoryFilters, TrendCard, RunList, TaskStatusRow, CommitCard
      changelog/            # ChangelogDay, AuditDialog
      run/                  # RunHeader
      timeline/             # RunTimeline, PhaseStrip, TimelineFilters, TimelineEntryCard, DetailList, TaskAttempts, EntryDialog
      graph/                # HypergraphPanel, HypergraphCanvas, IncidenceMatrix, ReplayControls, GraphLegend,
                            # ElementDetails, ElementDialog, ElementBody, VertexDetails, BagDetails
      agents/               # AgentsPanel, CallsTable, CallPreview, CallDialog, JsonTree
      thesis/               # ThesisPanel, ThesisDocument, ResultsTable, FigureGallery
      live/                 # NowCard, TaskBoard, TaskDialog
      launch/               # LaunchForm, ConsoleTail
    composables/            # useHistory, useHistoryDashboard, useChangelog, useRunBundle, useTimeline,
                            # useHypergraphReplay, useGraphElement, useGraphStyle, useCytoscape, useAgentCalls,
                            # useCallDetail, useThesis, useLiveRun, useLauncher, useListDialog, useArrowKeys, useSecondsSince,
                            # useCompare (wybór w ?runs=), useChartInk, useCommandPalette
    utils/                  # labels (+ labelParts/), icons, runUrls, nav (lista stron), chartOptions, compareMetrics, echarts
  stories/                  # Storybook: *.stories.ts, fixtures/ z przebiegu 18.11
  .storybook/               # main.ts (@storybook-vue/nuxt), preview.ts (ciemny v-app)
  tests/                    # timeline.real.test.ts: oś czasu z prawdziwych events.jsonl
```

Nazwy komponentów nadaje Nuxt: katalog + plik, ze zdublowanym przedrostkiem zwiniętym (`agents/AgentsPanel.vue` → `<AgentsPanel>`, `graph/ElementDialog.vue` → `<GraphElementDialog>`). Zła nazwa w szablonie nie daje błędu kompilacji, tylko ostrzeżenie w konsoli i pusty element — stąd zrzuty ekranu i Storybook przy każdej zmianie widoku.

## 11. Etapy

| Etap | Zakres | Gotowe, gdy |
|---|---|---|
| 1 | szkielet (Nuxt + Vuetify, motywy), źródła `git` i `results`, `/api/history`, Historia (kafelki), nagłówek przebiegu | kafelki 10 commitów z benchmarkami, przebieg otwiera się z każdego |
| 2 | `buildTimeline` + Oś czasu (pasek faz, oś, rozwinięcia, filtry) | oś przebiegu 01 z 18.11 pokazuje 3 wersje planu, 34 zadania z próbami, 4 przebudowy kolejki; testy `bun test` `buildTimeline` |
| 3 | Agenci (tabela + szczegóły) | wywołanie otwiera payload i odpowiedź |
| 4 | Hipergraf z odtwarzaniem | stany wierzchołków zmieniają się z suwakiem |
| 5 | źródło `live` + SSE + tablica zadań + „Teraz” | przebieg na mocku widać na żywo |
| 6 | Uruchom | start/stop przebiegu na mocku z przeglądarki |
| 7 | Praca; porównanie dwóch commitów | — |

**Stan (2026-11-18): wszystkie etapy 1–7 zrobione.** Historia (22 commity + wyniki na dysku); widok przebiegu: Oś czasu (pasek faz, filtry, próby zadań, chipy agentów, przejście do wywołań), Hipergraf (graf dwudzielny z podświetlaniem worka i jego członków, **macierz incydencji** wierzchołki × worki z chipami ról, odtwarzanie stanów, szczegóły), Agenci (tabela z rozwijanym podglądem, okno z odpowiedzią i payloadem jako drzewo, surowa odpowiedź, prompt), Praca (markdown z klasami Vuetify i wyróżnionymi wskaźnikami, przełącznik wskaźniki/wartości, wyniki CSV, rysunki, PDF); Na żywo (SSE, karta „Teraz”, tablica kolejki, oś/hipergraf/agenci trwającego przebiegu); Uruchom (formularz, start/stop `main.py`, konsola). Testy: `bun test` (10). **2026-11-19:** dashboard historii (kafelki, filtry dat — gotowe zakresy i `v-date-input`, zadań i statusów, trend `v-sparkline` dla wybranego zadania i metryki), karty commitów ze statystyką zmian i sekcjami audytu od poprzedniego commita, strona **Postęp** (`/changelog`: `audit_repairs.md` + commity dzień po dniu, `shared/utils/audit.ts`, `changelogDays.ts`), nawigacja ← → w oknach (wywołania agentów, rysunki, sekcje audytu) i w odtwarzaniu hipergrafu (`useArrowKeys`), kopiowanie promptów i odpowiedzi, nagłówki stron i okruszki. Testy: 13. Potem: zaokrąglenia w motywie (karty/arkusze `xl`, chipy/przyciski/pola `pill`), ikony w chipach, okna szczegółów z ← → dla pozycji osi czasu (`EntryDialog`), wierzchołków i worków (`ElementDialog`) i zadań na żywo (`TaskDialog`), zwijane długie komunikaty prób (tracebacki), **Storybook** z historiami komponentów. **Porządki:** wspólne okno `CommonBrowseDialog` + `useListDialog` (6 okien), `CommonHoverCard`, `useGraphElement` + `GraphElementBody`, `runUrls`, kolory werdyktów/tierów/kolejki w `colors.ts`, `shared/utils/json.ts`; usunięte `CallDialogHeader`, `ClientOnly` (ssr: false), zbędne eksporty; widok telefonu (zakładki-ikony, macierz zamiast grafu). Testy: 15. **Potem:** strona **Porównanie** (tabela z różnicami, 4 wykresy narastające w czasie, agenci, SML/LRM; ECharts), nawigacja: boczny pasek z ikonami, dolny pasek na telefonie, paleta Ctrl K, przycisk „Porównaj” w przebiegu. Testy: 19. **Potem:** ekran startowy, przejścia stron, szkielety, liczby odliczane, poświata zmian w grafie. **Ładowanie i błędy:** sprawdzone na każdej stronie przy API opóźnionym o 2,5 s i przy odpowiedziach 500 — wszędzie szkielet, potem treść albo komunikat z ponowieniem.

## 12. Decyzje otwarte

- Zakładka **Uruchom** startuje procesy na komputerze użytkownika (tylko localhost) — do potwierdzenia przed etapem 6.
- **Zakres historii**: wszystkie commity z `adk/workspace/benchmarks` (od 05.11); starsze bez `events.jsonl` pokazują tylko to, co mają.

## 13. Wersja wdrożona (Firebase Hosting, plan Spark)

Ten sam viewer, zbudowany z `NUXT_PUBLIC_DEPLOYED=true`: tylko historia z gita, statyczne pliki, bez serwera i bez logowania (to tylko podgląd).

| Lokalnie | Wdrożony |
|---|---|
| Nitro czyta git, dysk i piaskownicę | brak serwera: SPA z `nuxt generate` + paczki snapshotu w `/snapshot/*.json` |
| Historia, Porównanie, Postęp, Na żywo, Uruchom | bez Na żywo i Uruchom (`localOnly` w `nav.ts`, `LOCAL_ONLY` w middleware `local-only.global.ts`); „wyniki na dysku” puste |

**Dane = snapshot API.** `scripts/snapshot.ts` przechodzi po lokalnym API (`bun run dev` musi działać) i zapisuje w `.snapshot/` paczki JSON: `index` (`/api/history` + `/api/changelog`) i jedną na przebieg commita (`<sha>_<task>`: bundle, wywołania, szczegóły każdego wywołania, pliki jako base64). Typy w `shared/types/snapshot.ts`. Commit się nie zmienia, więc spakowany przebieg nie jest czytany drugi raz. `generate:deployed` kopiuje `.snapshot/` do `.output/public/snapshot/`; Hosting kompresuje w transferze, a `firebase deploy` wysyła tylko zmienione pliki. Całość ~47 MB / 70 paczek (2026-11-19), w limitach Spark.

**Klient bez zmian.** `app/plugins/deployed.client.ts` (lokalnie nic nie robi) podmienia `globalThis.fetch` dla `/api/*` (`app/utils/snapshot/fetchShim.ts` + `packs.ts`): ofetch woła `globalThis.fetch` przy każdym zapytaniu, więc `useFetch`/`$fetch` we wszystkich composables dostają odpowiedzi z paczek (`snapshotRoute` w `shared/utils/snapshot.ts`, testy obok). Jedyny wyjątek: rysunki i PDF w `<img>`/`href` idą przez `useFileUrls` (adresy `blob:`).

**Deploy robi tylko właściciel repo, ręcznie.** `viewer/.env` (poza repo, szablon `.env.example`) trzyma `FIREBASE_PROJECT_ID`. `bun run dev` w jednym terminalu, w drugim `bun run deploy` (snapshot → generate → `scripts/deploy.ts`: `firebase deploy --project <FIREBASE_PROJECT_ID> --only hosting`). Podgląd przed wysłaniem: `bunx firebase emulators:start --only hosting --project demo-viewer` (port 5000).
