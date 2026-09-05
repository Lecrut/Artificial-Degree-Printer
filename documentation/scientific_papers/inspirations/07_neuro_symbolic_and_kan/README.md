# 📐 07. Neuro-Symbolic Computing, KAN & Declarative Geometry

Kategoria poświęcona fuzji głębokich sieci neuronowych z formalnym rachunkiem symbolicznym i więzami matematycznymi. 

Badamy **Sieci Kołmogorowa-Arnolda (Kolmogorov-Arnold Networks - KAN)**, które zastępują wagi neuronowe uczącymi się równaniami, oraz **deklaratywny rachunek więzów Penrose** do generowania bezkolizyjnych, dowodowo poprawnych struktur geometrycznych i diagramów.

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

Wielowarstwowe perceptrony (MLP) w modelach AI to czarne skrzynki:
- Nie generują zrozumiałych dla człowieka wzorów matematycznych.
- Mają trudności z ekstrapolacją poza rozkład treningowy.
- Generowane diagramy architektoniczne są często krzywe, elementy nachodzą na siebie, a etykiety są nieczytelne.

Podejście Neuro-Symboliczne (KAN + Penrose):
1. **Splajny zamiast wag (Learnable Activations on Edges):** KAN potrafi z surowych danych telemetrycznych oprogramowania wydobyć dokładne analityczne równanie złożoności obliczeniowej (np. $T(n) = a \cdot n \log n + b$).
2. **Układy optymalizowane więzami (Constraint Optimization via Penrose):** Rysowanie architektury systemu nie jako arbitralnych pikseli, lecz układu spełniającego ścisłe aksjomaty geometryczne (zerowa kolizja, równe odstępy, spójność typów).
3. **Biała skrzynka (Explainable-by-Design):** Wszystkie wnioski i modele w pracy magisterskiej posiadają postać zamkniętych równań algebraicznych.

---

## 📚 Publikacje w Klastrze:
- [`liu2024_kan_networks.md`](liu2024_kan_networks.md) (`@Liu2024KAN`) – *KAN: Kolmogorov-Arnold Networks (MIT 2024)*
- [`fast_kan2024_rbf.md`](fast_kan2024_rbf.md) (`@FastKAN2024`) – *Fast-KAN and Chebyshev-KAN: Accelerating KANs via RBF (2024)*
- [`graphkan2024_networks.md`](graphkan2024_networks.md) (`@GraphKAN2024`) – *GraphKAN: Enhancing Feature Extraction with Graph KANs (2024)*
- [`feynman2026_penrose_diagrams.md`](feynman2026_penrose_diagrams.md) (`@Feynman2026Diagrams`) – *Feynman: Knowledge-Infused Diagramming Agent with Penrose (2026)*
- [`graphical_einops2026_calculus.md`](graphical_einops2026_calculus.md) (`@GraphicalEinops2026`) – *Graphical Einops: A Formal Graphical Calculus for Tensor Programming (2026)*
