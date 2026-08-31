# Technology Dossier: Typst 0.11+ & CeTZ Canvas Engine

> **Tech ID:** `TECH-01`  
> **Category:** Document Composition & Vector Layout Engine  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Błyskawiczny kompilator dokumentów naukowych, prac dyplomowych i diagramów wektorowych

---

## 📌 Context and Motivation

Tradycyjny LaTeX jest powolny w kompilacji, podatny na trudne do zdebugowania błędy makr i wymaga skomplikowanego środowiska (TeXLive ~5GB). Z kolei zwykłe edytory WYSIWYG (Word) nie posiadają rygoru akademickiego ani automatyzacji wywołań kodowych.

**Typst 0.11+** w połączeniu z pakietem **CeTZ (Drawing Canvas)** reprezentuje nowoczesny standard 2026 r.:
- Kompilacja pliku 50-stronicowej pracy dyplomowej w mniej niż **50 milisekund** (napisany w Rust).
- Natywne rysowanie czystych diagramów wektorowych CeTZ bez konieczności generowania zewnętrznych plików PNG.
- Zintegrowany silnik bibliograficzny **Hayagriva** dla formatu BibTeX.

---

## 💡 Key Technical Features

- **Instant Hot-Reloading:** Możliwość bieżącego podglądu zmian podczas generowania tekstu przez agenta.
- **Code Listing Highlighting:** Zaawansowane podświetlanie składni Pythona, C++, Rust i Typst.
- **Mathematical Layout:** Przejrzysta i zwięzła składnia dla wzorów matematycznych (zamiast kłopotliwego `\frac{}{}`).

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/tools/typesetting.py` & `adk/templates/thesis.typ`.
- **Target App Output:** `artifacts/thesis/thesis.typ` z równoległym eksportem do LaTeX.

