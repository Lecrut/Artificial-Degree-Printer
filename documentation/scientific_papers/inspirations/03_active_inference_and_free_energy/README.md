# 🧠 03. Active Inference & Free Energy Principle (FEP)

Kategoria poświęcona zastosowaniu **Zasady Wolnej Energii (Free Energy Principle - FEP)** Karla Fristona oraz **Aktywnej Inferencji (Active Inference)** w systemach wieloagentowych. 

Jest to radykalna alternatywa dla klasycznego sterowania agentami za pomocą sztywnych promptów i deterministycznych maszyn stanów.

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

W standardowych systemach agentowych (np. AutoGen, CrewAI):
- Agenci wykonują polecenia "w ciemno", reagując na tekst wejściowy.
- Nie posiadają wewnętrznego modelu własnej niepewności (Self-Uncertainty).
- Często błądzą w nieskończonych pętlach lub halucynują, gdy brakuje im danych.

W podejściu **Active Inference**:
1. **Agent jako system homeostatyczny:** Głównym celem agenta jest minimalizacja wariacyjnej wolnej energii (czyli zaskoczenia i niepewności co do stanu środowiska/kodu).
2. **Eksploracja epistemiczna (Epistemic Foraging):** Jeśli agent nie jest pewien zachowania funkcji, nie "zgaduje", lecz autonomicznie pisze test jednostkowy lub benchmark, aby zredukować własną niepewność.
3. **Termodynamiczna stabilność roju:** Cały zespół agentów działa jak samoregulujący się organizm, w którym błędy kodu są traktowane jak zaburzenia homeostazy, które system natychmiast koryguje.

---

## 📚 Publikacje w Klastrze:
- [`friston2024_active_inference_agents.md`](friston2024_active_inference_agents.md) (`@Friston2024ActiveInference`) – *Active Inference for Self-Organizing Multi-LLM Systems (2024)*
- [`orchestrator2025_active_inference.md`](orchestrator2025_active_inference.md) (`@Orchestrator2025`) – *Orchestrator: Active Inference for Multi-Agent Systems (2025)*
- [`freia2025_free_energy_rl.md`](freia2025_free_energy_rl.md) (`@FREIA2025`) – *FREIA: Free Energy-Driven Reinforcement Learning for LLMs (2025)*
