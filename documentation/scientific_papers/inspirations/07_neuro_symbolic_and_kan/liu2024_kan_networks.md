# Scientific Paper Dossier: KAN: Kolmogorov-Arnold Networks

> **Citation Key:** `@Liu2024KAN`  
> **Authors:** Ziming Liu, Yixuan Wang, Sachin Vaidya et al. (MIT)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~1800+  
> **Venue / Conference:** arXiv:2404.19756 / MIT Tech Report  
> **Link / DOI:** [https://arxiv.org/abs/2404.19756](https://arxiv.org/abs/2404.19756)

---

## 📌 Core Thesis and Research Motivation

Od czasów powstania głębokiego uczenia niemal wszystkie architektury neuronowe opierają się na twierdzeniu o uniwersalnej aproksymacji i warstwach MLP (Multilayer Perceptrons), gdzie neurony sumują ważone wejścia i przepuszczają je przez stałą nieliniowość. 

Autorzy z MIT proponują **Kolmogorov-Arnold Networks (KAN)** oparte na twierdzeniu Kołmogorowa-Arnolda o reprezentacji. W sieci KAN wagi są zastąpione jednowymiarowymi, uczącymi się funkcjami aktywacji (B-splajnami) umieszczonymi na krawędziach grafu sieci, podczas gdy węzły realizują jedynie proste sumowanie.

---

## 💡 Key Theoretical Findings

1. **Przełomowa interpretowalność (White-Box Symbolic Distillation):** KAN potrafi po zakończeniu treningu zwinąć wyuczone splajny w proste, zamknięte formuły symboliczne ($x^2$, $\sin(x)$, $\exp(x)$), odkrywając nieznane prawa fizyczne i matematyczne z danych.
2. **Wyższa dokładność przy mniejszej liczbie parametrów:** Mała sieć KAN z kilkunastoma parametrami potrafi osiągnąć dokładność aproksymacji funkcji wyższą niż gigantyczna sieć MLP z setkami tysięcy wag.
3. **Odporność na katastrofalne zapominanie (Catastrophic Forgetting):** Dzięki lokalnemu charakterowi splajnów baza wiedzy sieci może być aktualizowana punktowo bez niszczenia wcześniej wyuczonych wzorców.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Symbolic Performance Modeler:** Użycie modułu KAN do analizy wyników benchmarków w `adk/tools/benchmarks.py` i automatycznego wyprowadzania funkcji złożoności do Rozdziału 4 pracy dyplomowej.
- [x] **Neuro-Symbolic Gate:** Weryfikacja spójności twierdzeń matematycznych w tekście pracy z wyuczonymi modelami KAN.

---

## 🚀 Key Strengths and Novelties

- Fundamentalna alternatywa dla 50-letniego paradygmatu MLP.
- Natywna konwersja sieci neuronowej w równanie symboliczne LaTeX.
