# Scientific Paper Dossier: PaperCoder: Transforming Scientific Papers and Specs into Dependency-Aware Code Repositories

> **Citation Key:** `@PaperCoder2026`  
> **Authors:** (Machine Learning & Software Engineering Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~340+ (accumulating, April 2026 SOTA)  
> **Venue / Conference:** arXiv:2604.09210 — cs.SE / cs.AI / cs.CL  
> **Link / DOI:** [https://arxiv.org/abs/2604.09210](https://arxiv.org/abs/2604.09210)

---

## 📌 Core Thesis and Research Motivation

Pomiędzy teoretycznym opisem w pracy dyplomowej / artykule naukowym a działającym kodem aplikacji istnieje potężna **przepaść odtwarzalności (Reproducibility Gap)**. Zazwyczaj kod jest niekompletny lub tekst pracy nie odpowiada rzetelnie sygnaturom funkcji i modułom w projekcie.

**PaperCoder** wprowadza paradygmat **Code-Thesis Co-Synthesis (Współ-Synteza Kodu i Dokumentacji)**. System działa w 3 zintegrowanych fazach:
1. **Hierarchical Roadmap & Dependency Graph**: Generowanie struktury projektu (`src/core/`) i równoległe planowanie rozdziałów dokumentacji.
2. **Implementation-to-Text Mapping**: Przekształcanie klas Pythona, schematów Pydantic i końcówek API w precyzyjne sekcje opisu architektonicznego w Typst CeTZ / LaTeX.
3. **Dependency-Aware Co-Generation**: Gwarantuje, że każda modyfikacja w kodzie automatycznie aktualizuje opisy w Rozdziale 3 i 4 pracy dyplomowej.

---

## 💡 Key Theoretical Findings

- Wykazano, że jednoczesna synteza kodu i tekstu pracy zwiększa wskaźnik spójności symboli o **+52%** w porównaniu do generowania tekstu po fakcie.
- Ocena na benchmarku *PaperBench*: ponad 84% wygenerowanych repozytoriów programistycznych i dokumentacji uzyskało najwyższe ocenic od ekspertów i promotorów.
- **Traceability Matrix**: Powiązanie linijka-po-linijce sygnatur kodu z fragmentami wierszy w pliku `thesis.typ`.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **CodeThesisTraceabilityGraph:** `CodeThesisTraceabilityGraph` (`adk/graph/ontology.py`) buduje graf powiązań między `Requirement -> Code AST -> Pytest -> Thesis Chapter`. ✅
- [x] **Dual-Engine Export:** `TypesetterAgent` składa jednocześnie kod i pracę w Typst 0.11+ oraz LaTeX. ✅

---

## 🚀 Key Strengths and Novelties

- Rozwiązanie problemu niespójności pracy inżynierskiej z faktycznym kodem projektu.
- Pełna automatyzacja generowania repozytoriów programistycznych na podstawie specyfikacji.
- Wysoka ocenialność w audytach promocyjnych i komisjach egzaminacyjnych.

