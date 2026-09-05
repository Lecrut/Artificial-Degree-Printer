# Scientific Paper Dossier: FREIA: Free Energy-Driven Reinforcement Learning for Adaptive LLM Self-Improvement

> **Citation Key:** `@FREIA2025`  
> **Authors:** L. Chen, T. Baldwin, H. Zhang et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~85+  
> **Venue / Conference:** NeurIPS 2025 Workshop / arXiv:2502.13411  
> **Link / DOI:** [https://arxiv.org/abs/2502.13411](https://arxiv.org/abs/2502.13411)

---

## 📌 Core Thesis and Research Motivation

Tradycyjne nagrody w RLHF (Reinforcement Learning from Human Feedback) są podatne na tzw. reward hacking – modele uczą się schlebiać preferencjom oceniających lub pisać długie, kwieciste, lecz bezwartościowe teksty.

**FREIA** wprowadza funkcję nagrody opartą na **Zasadzie Wolnej Energii**. Zamiast zewnętrznego modelu nagrody, model nagradza samego siebie za akcje, które maksymalizują kompresję wiedzy i redukują wariancję przewidywań w warunkach niepewności środowiska wykonawczego.

---

## 💡 Key Theoretical Findings

1. **Samoistne dążenie do prostoty:** Zasada wolnej energii w naturalny sposób faworyzuje brzytwę Ockhama – kod zwięzły, czytelny i o niskiej złożoności cyklomatycznej.
2. **Odporność na overfitting:** Model nie zapętla się w generowaniu frazesów syntetycznych, ponieważ frazesy nie niosą informacji redukującej niepewność.
3. **Dynamiczna kalibracja temperatury:** W miarę spadku wolnej energii model autonomicznie obniża temperaturę próbkowania, przechodząc od fazy burzy mózgów do fazy precyzyjnego kodowania.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Ockham Simplicity Gate:** Implementacja weryfikacji zwięzłości kodu i eliminacji zbędnego narzutu abstrakcji w `adk/verification/code_gate.py`.
- [x] **Adaptive Sampling Temperature:** Dynamiczna kontrola temperatury w `adk/llm/client.py` w zależności od etapu prac.
