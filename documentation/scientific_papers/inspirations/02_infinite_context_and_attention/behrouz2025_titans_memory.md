# Scientific Paper Dossier: Titans: Learning to Memorize at Test Time

> **Citation Key:** `@Behrouz2025Titans`  
> **Authors:** Ali Behrouz, Peilin Zhong, Vahab Mirrokni (Google Research)  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~190+  
> **Venue / Conference:** arXiv:2501.00663 / Google Research Jan 2025  
> **Link / DOI:** [https://arxiv.org/abs/2501.00663](https://arxiv.org/abs/2501.00663)

---

## 📌 Core Thesis and Research Motivation

Klasyczne modele Transformer podczas testowania posiadają zamrożone wagi – cała ich zdolność adaptacji opiera się na ulotnym oknie kontekstowym. Gdy okno się kończy, model bezpowrotnie traci wcześniejsze fakty.

Google Research przedstawia architekturę **Titans**, wprowadzającą **neuronowy moduł pamięci długoterminowej uczący się w czasie testowania (Test-Time Learning)**. Moduł ten traktuje historię konwersacji lub czytanego repozytorium jako dane do bieżącej aktualizacji wewnętrznej macierzy asocjacyjnej za pomocą spadku gradientu w locie.

---

## 💡 Key Theoretical Findings

1. **Uczenie się w locie (Neural Long-Term Memory):** Pamięć Titans nie jest zwykłym wektorowym indeksem k-NN, lecz miniaturową siecią neuronową, która uczy się faktów i zależności bezpośrednio podczas czytania tekstu.
2. **Bramkowanie uwagi (Surprise Metric):** Informacje zaskakujące (o wysokim gradiencie błędu) są trwale zapisywane w pamięci długoterminowej, podczas gdy rutynowe tokeny są ignorowane.
3. **Skuteczność na Needle-in-a-Haystack:** 100% odzyskiwania faktów przy sekwencjach przekraczających 2 miliony tokenów przy ułamku kosztu obliczeniowego Transformerów.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Test-Time Project Memory:** Wprowadzenie w `adk/memory/store.py` dynamicznie douczanej pamięci asocjacyjnej zapamiętującej decyzje architektoniczne użytkownika.
- [x] **Surprise-Based Commit Logger:** Automatyczne tworzenie commitów w repozytorium tylko wtedy, gdy metryka zaskoczenia modelu przekracza określony próg.
