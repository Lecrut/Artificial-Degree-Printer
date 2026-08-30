# Przewodnik Użytkownika (ADK User Guide)

## Wprowadzenie

Framework **ADK (Artificial Degree Printer)** służy do automatyzacji pełnego cyklu wytwórczego:
1. Projektowania architektury i wymagań projektu IT,
2. Generowania działającego kodu, testów i konteneryzacji,
3. Przeprowadzania badań wydajnościowych i generowania wektorowych wykresów,
4. Złożenia gotowej pracy inżynierskiej lub magisterskiej w formatach **Typst** oraz **LaTeX** wraz z kompletną bibliografią **BibTeX**.

---

## 🛠️ Podstawowe Polecenia CLI

### 1. Generowanie pełnego projektu i pracy:
```bash
python main.py generate "System analizy wydajności mikrousług w architekturze chmurowej"
```
Po uruchomieniu:
- W folderze `generated_project/` znajdziesz gotowy kod i testy jednostkowe,
- W folderze `artifacts/thesis/` powstaną pliki `thesis.typ`, `thesis.tex` oraz `references.bib`,
- W folderze `artifacts/benchmarks/` powstaną wykresy SVG i PNG o jakości publikacyjnej,
- W konsoli zostanie wyświetlony dashboard z podsumowaniem i oceną jakości.

### 2. Sprawdzenie zgodności i audyt jakościowy:
```bash
python main.py verify
```
Uruchamia zestaw audytów:
- Walidację składni kodu (AST),
- Sprawdzenie czy wszystkie klucze `@cite` są zdefiniowane w pliku `.bib`,
- Weryfikację spójności między nazwami klas opisanymi w pracy a plikami w kodzie,
- Badanie stylometryczne i pre-check antyplagiatowy (estymacja JSA).

### 3. Wizualizacja Macierzy Identyfikowalności (Traceability Matrix):
```bash
python main.py graph
```
Generuje diagram Mermaid oraz podsumowanie pokrycia wymagań i testów.

---

## 📄 Kompilacja Pracy do formatu PDF

### Opcja A: Kompilacja za pomocą Typst (Zalecana)
Jeśli posiadasz zainstalowany kompilator Typst:
```bash
typst compile artifacts/thesis/thesis.typ artifacts/thesis/thesis.pdf
```

### Opcja B: Kompilacja za pomocą LaTeX / Tectonic / Overleaf
Plik `artifacts/thesis/thesis.tex` wraz z `references.bib` można bezpośrednio zaimportować do systemu Overleaf lub skompilować lokalnie:
```bash
cd artifacts/thesis
pdflatex thesis.tex
biber thesis
pdflatex thesis.tex
```

---

## ⚙️ Zaawansowana Konfiguracja

W pliku `adk/memory/session.json` przechowywany jest pełny stan projektu. Możesz go modyfikować lub wczytywać w celu kontynuacji pracy.

