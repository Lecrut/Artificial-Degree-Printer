# Scientific Paper Dossier: TreeDiff: AST-Guided Code Generation with Diffusion LLMs

> **Citation Key:** `@TreeDiff2025`  
> **Authors:** Z. Chen, H. Wang, L. Zhang et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~85+  
> **Venue / Conference:** Preprints 2025 / arXiv:2502.04891  
> **Link / DOI:** [https://arxiv.org/abs/2502.04891](https://arxiv.org/abs/2502.04891)

---

## 📌 Core Thesis and Research Motivation

Dominujący paradygmat generowania kodu oparty na modelach autoregresywnych cierpi na brak globalnej spójności strukturalnej – błąd popełniony w linii 5 propaguje się kaskadowo na kolejne linie. 

Autorzy **TreeDiff** proponują wykorzystanie dyskretnego modelu dyfuzyjnego, w którym proces dodawania i usuwania szumu jest bezpośrednio sprzężony z **abstrakcyjnym drzewem rozbioru gramatycznego (AST)**. Zamiast losowego maskowania pojedynczych tokenów, TreeDiff maskuje całe poddrzewa AST, zmuszając sieć do jednoczesnego wnioskowania o typach, zasięgu zmiennych i strukturze bloków.

---

## 💡 Key Theoretical Findings

1. **Strukturalne maskowanie poddrzew:** Dyfuzja ukierunkowana na AST redukuje liczbę błędów parsowania składniowego (Syntax Errors) o ponad **78%** w porównaniu z autoregresywnymi modelami o zbliżonej liczbie parametrów.
2. **Nieliniowe uzupełnianie kodu (In-Filling):** Model bez problemu rozwiązuje zadania typu "uzupełnij brakujące ciało metody w środku istniejącej klasy", zachowując zgodność z sygnaturami zdefiniowanymi powyżej i poniżej.
3. **Konwergencja odszumiania:** Proces odszumiania stabilizuje się w zaledwie 12–20 krokach dyskretnego próbkowania, co pozwala na generowanie z szybkością porównywalną z modelami spekulatywnymi.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **AST-Informed State Representation:** Wprowadzenie w `adk/engine/` reprezentacji stanu opartej na węzłach AST zamiast czystych ciągów tekstowych.
- [x] **Denoising Refactoring Tool:** Koncepcja nowego narzędzia `adk/tools/diff_repair.py`, które zamiast przepisywać plik, traktuje fragmenty kodu z błędami jako zaszumione i wykonuje ich iteracyjną krystalizację.

---

## 🚀 Key Strengths and Novelties

- Zastąpienie losowego szumu tokenowego szumem strukturalnym na poziomie gramatyki języka programowania.
- Naturalna zdolność do dwukierunkowej (bidirectional) analizy kontekstu kodu.
- Potężna baza pod innowację w pracy magisterskiej: generator oprogramowania odporny na halucynacje składniowe.

---

## 🎯 How our Project Overcomes and Advances Beyond this Work

TreeDiff operuje na izolowanych funkcjach. W ramach pracy magisterskiej w ADK możemy rozszerzyć tę koncepcję na **wieloplikowe drzewo zależności projektu (Project-Wide Dependency AST)**, odszumiając jednocześnie interfejsy modułów oraz pliki testów jednostkowych.
