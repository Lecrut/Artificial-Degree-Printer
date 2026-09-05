# 🎛️ 06. Explorable Explanations & Reactive Living Artifacts

Kategoria poświęcona idei **żywych, reaktywnych dokumentów naukowych** (Explorable Explanations w duchu Breta Victora) generowanych autonomicznie przez agentów AI. 

Zamiast traktować pracę magisterską jako martwy dokument PDF ze statycznymi wykresami, badamy generowanie **żywych artefaktów symulacyjnych**, w których czytelnik/recenzent może weryfikować tezy empiryczne w czasie rzeczywistym.

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

W klasycznej pracy inżynierskiej/magisterskiej:
- Wykresy w formacie PNG lub PDF są "martwe" – nie można sprawdzić, jak zmieniłby się wynik po zmianie parametrów wejściowych (np. obciążenia sieci czy wielkości partii).
- Istnieje pole do manipulacji lub fałszowania wyników (cherry-picking).

Paradygmat **ViviDoc (2026) / DocSpec**:
1. **Specyfikacja SRTC:** Rozbicie każdego elementu wizualnego na cztery formalne składowe: *State* (Stan), *Render* (Wygląd), *Transition* (Przejście) oraz *Constraint* (Więzy).
2. **Reaktywny silnik wykonawczy:** Wykres jest miniaturowym programem komputerowym. Zmiana pozycji suwaka wywołuje funkcję przeliczającą model w sandboksie.
3. **Prawdziwie interaktywna obrona pracy:** Recenzent na obronie przesuwa suwak i widzi natychmiastowe zachowanie algorytmu z Rozdziału 4!

---

## 📚 Publikacje w Klastrze:
- [`tang2026_vividoc.md`](tang2026_vividoc.md) (`@Tang2026ViviDoc`) – *ViviDoc: Generating Interactive Documents through Human-Agent Collaboration (2026)*
- [`plotgen2025_multiagent.md`](plotgen2025_multiagent.md) (`@PlotGen2025`) – *PlotGen: Multi-Agent Scientific Visualization with Multimodal Critics (2025)*
- [`matplotagent2024_scientific.md`](matplotagent2024_scientific.md) (`@MatPlotAgent2024`) – *MatPlotAgent: Method and Evaluation for Agentic Scientific Visualization (2024)*
- [`interactive_explorable2026_eval.md`](interactive_explorable2026_eval.md) (`@InteractiveExplorable2026`) – *Evaluating Interactivity: Automated Assessment of AI Explorable Explanations (2026)*
