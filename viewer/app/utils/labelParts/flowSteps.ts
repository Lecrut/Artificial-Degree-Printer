export interface FlowText {
  label: string
  note: string
}

const gaps: FlowText = {
  label: 'Koniec z listą braków',
  note: 'Przebieg kończy się statusem COMPLETED_WITH_GAPS: wszystko, czego nie udało się naprawić, trafia jako lista braków do pracy i raportu. Lista powstaje z danych, nie od modelu, więc niczego nie ukrywa.',
}
const queue: FlowText = {
  label: '↩ Kolejka zadań',
  note: 'Powrót do kolejki: harness bierze następne zadanie, którego zależności w hipergrafie są gotowe.',
}

/** Steps the harness does itself, branches ("if"), jumps back and ends: every block that is not an agent. */
export const flowSteps: Record<string, FlowText> = {
  start: {
    label: 'Start',
    note: 'Użytkownik podaje temat pracy i wybiera zadanie benchmarku (main.py --benchmark-task N). Dalej harness działa sam; człowiek może tylko zatwierdzać bramki.',
  },
  recon: {
    label: 'Rekonesans: literatura i konwencje dziedziny',
    note: 'Narzędzia harnessu zbierają literaturę i konwencje dziedziny. Wynik jest materiałem dla planisty; to nie jest agent z promptem.',
  },
  d_outline: {
    label: 'Zarys przyjęty?',
    note: 'Zarys sprawdza najpierw kod (spójność modułów, zależności), potem krytyk. Autor ma do 3 odpowiedzi, krytyk może blokować w najwyżej 2 rundach.',
  },
  j_outline: { label: '↩ Poprawka zarysu', note: 'Autor zarysu dostaje uwagi i poprawia go; nic poza zarysem nie jest cofane.' },
  d_module: {
    label: 'Interfejs modułu przyjęty?',
    note: 'Powtarzane dla każdego modułu, zależności najpierw. Moduł, który nie zbiega, raz odsyła dowody do zarysu. Przyjęty interfejs jest zamrożony.',
  },
  j_module: { label: '↩ Poprawka interfejsu modułu', note: 'Autor modułu poprawia tylko ten interfejs; zależne moduły sprawdza kod i cofa tylko te, które się zepsuły.' },
  s_tasks: {
    label: 'Zadania wyprowadza kod',
    note: 'Etap 3 planu bez modelu: z zarysu i interfejsów kod buduje listę zadań (badania, rozdziały wstępne, każdy moduł z testami, pozostałe rozdziały).',
  },
  d_plan: {
    label: 'Plan przeszedł krytyka głównego?',
    note: 'Uwaga wskazuje część planu i tylko ta część wraca. Po rundach krytyka wykonalny plan idzie dalej z zapisanymi zastrzeżeniami (PLAN_ACCEPTED_OVER_CRITIC).',
  },
  j_plan: { label: '↩ Wskazana część planu', note: 'Wraca zarys albo moduł, o którym mówi uwaga krytyka; reszta planu zostaje.' },
  s_gates: {
    label: 'Bramki 1–2: zatwierdzenie planu',
    note: 'W trybie interaktywnym plan zatwierdza człowiek (zarys i metodologia). W trybie nieinteraktywnym bramki przechodzą same.',
  },
  s_queue: {
    label: 'Następne gotowe zadanie',
    note: 'Zadania idą według stanu hipergrafu: zadanie czeka (WAITING), dopóki wierzchołki, od których zależy, nie są zweryfikowane. Rozdziały z wynikami czekają na results.csv.',
  },
  d_type: {
    label: 'Czyje to zadanie?',
    note: 'Decyduje plik docelowy: dokument do pisarza, test do testera, pozostały kod do kodera. Zadania badawcze mają przypisanych agentów w planie.',
  },
  s_verify: {
    label: 'Weryfikacja bez modelu',
    note: 'Kod sprawdzają py_compile, import, ruff, pytest, kontrakty i metryki; dokumenty kompilator wskaźników \\ref. Przy zadaniach pośrednich modele-audytorzy nie działają, bo wyniki są dokładne i same podpowiadają naprawę.',
  },
  d_pass: { label: 'Zadanie przeszło?', note: 'Weryfikacja przeszła bez błędów: wierzchołek dostaje stan verified.' },
  d_more: { label: 'Są kolejne zadania w kolejce?', note: 'Kolejka jest wykonywana do końca; zadanie nieudane nie zatrzymuje reszty, tylko blokuje swoje zależne.' },
  j_queue1: queue,
  d_failed: {
    label: 'Są nieudane wierzchołki?',
    note: 'Po przejściu kolejki harness sprawdza hipergraf: wierzchołek failed oznacza, że autor i naprawy nie dały rady.',
  },
  d_redesign: {
    label: 'Pora na przeprojektowanie?',
    note: 'Najpierw idzie jedna runda przeplanowania (task_planner). Dopiero gdy po niej żaden wierzchołek nie przybył jako zweryfikowany, a nie wyczerpano limitu 2 rund na przebieg, rewiduje się projekt: zweryfikowany plik przeszedł tylko własne testy, a przyczyna porażki bywa w sąsiedzie albo w podziale na moduły. Taka runda nie liczy się do limitów przeplanowania.',
  },
  s_revise: {
    label: 'Projektant rewiduje zarys',
    note: 'plan_outline w trybie rewizji dostaje zarys, audyt (deklaracje i opisy działania plików, bez ciał funkcji) i nierozwiązane błędy. Zwraca zarys i status każdego modułu: keep, change, new albo remove, z diagnozą nieudanych. Gdy opisy nie wystarczą, może raz poprosić o kod do trzech zaimplementowanych plików; taka prośba nie zużywa odpowiedzi.',
  },
  d_guidelines: {
    label: 'Wytyczne przeszły kontrolę kodu?',
    note: 'Kod sprawdza spójność statusów z zarysem (keep identyczny ze starym wpisem, zmieniony moduł oznaczony change, wolna nazwa nowego pliku) i zwykłe reguły zarysu. Jedna poprawka. Gdy nic się nie zmienia albo wytyczne nie przejdą, rundę przejmuje przeplanowanie nieudanych.',
  },
  j_replan: { label: '↩ Przeplanowanie nieudanych', note: 'Wytyczne odrzucone lub bez zmian: ta runda idzie jak dawniej do task_planner i liczy się do jego limitów.' },
  s_redesign_modules: {
    label: 'Zmienione i nowe moduły od nowa',
    note: 'Przez planowanie etapowe przechodzą tylko moduły change i new: plan_module (pierwsza odpowiedź mały model, poprawki duży), krytyk modułu, krytyk główny. Moduły keep zostają zaakceptowane i kod sprawdza je tylko na tle zmienionych sąsiadów; złamany wraca do projektowania.',
  },
  s_redesign_apply: {
    label: 'Nowy hipergraf i kolejka',
    note: 'H budowany od nowa z nowego planu. Zweryfikowane, niezmienione wierzchołki zachowują stan; nieudane zaczynają z zerowymi próbami (porażki zostają, od nich zależy model); testy modułów używających zmienionego są weryfikowane ponownie. Pliki usuniętych modułów znikają, nowe dostają stuby. Czekające zadania zastępuje kolejka D1, D2 dla wszystkiego, co nie jest zweryfikowane.',
  },
  j_queue4: { ...queue, label: '↩ Nowa kolejka (D1, D2)' },
  d_progress: {
    label: 'Był postęp?',
    note: 'Postęp to liczba wierzchołków, które kiedykolwiek były zweryfikowane. Przebieg kończy się po 3 rundach przeplanowania bez postępu albo po 6 rundach w ogóle.',
  },
  j_queue2: { ...queue, note: 'Nowe zadania z przeplanowania (R1, R2…) wchodzą do kolejki; reszta wierzchołków zostaje nietknięta.' },
  e_gaps1: gaps,
  s_fast: {
    label: 'Szybka naprawa (do 2 prób)',
    note: 'Ten sam agent poprawia tylko winny plik, z zawężonym kontekstem. Model zależy od liczby porażek wierzchołka i od rodzaju błędu: najpierw mały (SML), duży (LRM) od drugiej porażki kodu lub trzeciej rozdziału; usterkę mechaniczną (lint, składnia, import) mały model poprawia do czwartej.',
  },
  d_fastok: { label: 'Przeszło po naprawie?', note: 'Po każdej próbie harness weryfikuje zadanie od nowa.' },
  d_spec: {
    label: 'Powtarza się naruszenie interfejsu?',
    note: 'Gdy ten sam błąd mówi, że kod łamie interfejs z planu (σ), zamiast kolejnej próby pyta się sędziego interfejsu, czy to nie interfejs jest zły.',
  },
  j_fast: { label: '↩ Kolejna szybka naprawa', note: 'Decyzja sędziego (AMEND albo zostaje) trafia do następnej próby autora.' },
  d_pattern: {
    label: 'Ten sam błąd w ≥ 2 zadaniach?',
    note: 'Ewolucja promptu rusza tylko dla wzorca: ta sama kategoria błędu tego samego agenta w co najmniej dwóch zadaniach, jeszcze bez reguły w tym przebiegu. Kategorie, które egzekwuje harness, są pomijane.',
  },
  d_vertex: {
    label: 'Plik jest wierzchołkiem H?',
    note: 'Dla plików z hipergrafu (cały kod) planista napraw jest pomijany: autor miał już lokalne próby, a wierzchołek wraca w przeplanowaniu. Planista napraw działa tylko dla reszty, np. thesis.md.',
  },
  s_failed: {
    label: 'Zadanie nieudane',
    note: 'Po jednym cyklu napraw zadanie, które wciąż pada, jest luką: wierzchołek ma stan failed, a zależne od niego zadania czekają na przeplanowanie.',
  },
  j_next: { label: '↩ Czy są kolejne zadania?', note: 'Harness przechodzi do pytania o następne zadanie w kolejce.' },
  d_defense: {
    label: 'Obrona zaliczona?',
    note: 'Obrona końcowa (Gate 3) sprawdza cały kod, wyniki i każdy rozdział. Błędem jest to, co udowodnił harness; opinie audytorów-modeli są ostrzeżeniami i nie wymuszają napraw.',
  },
  s_rebuild: {
    label: 'Audyt stanu i nowa kolejka',
    note: 'Harness audytuje, co faktycznie leży w workspace, i buduje kolejkę zadań z ustaleń. Są cztery takie przebudowy; powtórzony ten sam audyt kończy przebieg wcześniej.',
  },
  j_queue3: { ...queue, label: '↩ Nowa kolejka zadań' },
  e_gaps2: gaps,
  s_pdf: {
    label: 'Kompilacja PDF',
    note: 'Po zaliczonej obronie harness buduje PDF. Jeśli się nie zbuduje, działa to jak porażka obrony: audyt i nowa kolejka.',
  },
  s_hitl: {
    label: 'Bramka 3: zatwierdzenie pracy',
    note: 'W trybie interaktywnym końcowe zatwierdzenie daje człowiek.',
  },
  end: {
    label: 'Koniec: paczka wyników',
    note: 'Wyniki są układane w folderze zadania: code/, thesis/ i results/, razem z logami i migawkami stanu (z nich można wznowić przebieg).',
  },
}
