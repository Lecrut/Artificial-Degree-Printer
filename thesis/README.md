# 🎓 Praca Magisterska: Artificial Degree Printer (ADK)
# 🎓 Master of Science Thesis: Artificial Degree Printer (ADK)
### Lodz University of Technology (Politechnika Łódzka)

Modułowa praca dyplomowa w standardzie **LaTeX (BibLaTeX + IEEE)** zsynchronizowana z repozytorium kodu systemu ADK.
Modular Master of Science Thesis written in **English** adhering to Lodz University of Technology (TUL / PŁ) editorial standards and LaTeX typesetting best practices (BibLaTeX + IEEE / numeric style).

---

## 📁 Struktura Katalogu `thesis/`
## 📁 Repository Structure (`thesis/`)

```text
thesis/
├── main.tex                  # Główny dokument (spina metadane, style, spisy i rozdziały)
├── references.bib            # Baza literatury BibTeX (ponad 15 pozycji SOTA 2023-2026)
├── config/
│   ├── metadata.tex          # Tytuł, autor, promotor, uczelnia, streszczenie PL/EN (Szybka edycja!)
│   └── styles.tex            # Marginesy, geometria, czcionki, pakiety, styl listingów kodu
├── chapters/                 # Modułowe rozdziały pracy
│   ├── 01_wstep.tex          # Motywacja, paradygmat Code-First, teza i cele pracy
│   ├── 02_stan_wiedzy.tex    # SOTA: MetaGPT, ChatDev, SWE-bench, Reflexion, DSPy
│   ├── 03_architektura.tex   # Architektura roju ADK, role agentów, graf stanów, Pydantic v2
│   ├── 04_implementacja.tex  # Implementacja: sandbox wykonawczy, wyszukiwarka literatury
│   ├── 05_weryfikacja.tex    # 7 Bramek Jakościowych (MasterVerificationSuite, mutacje, TTR)
│   ├── 06_eksperymenty.tex   # Badania empiryczne, benchmarki SLA p95, wyniki audytu
│   └── 07_podsumowanie.tex   # Podsumowanie celów, weryfikacja tezy, wnioski i rozwój
├── figures/                  # Wektorowe schematy C4, wykresy i diagramy (PDF/SVG/PNG)
└── compile.bat               # Skrypt 1-kliknięcia do kompilacji do pliku PDF
|-- main.tex                          # Main compilation entrypoint (bilingual title page, TOC, chapters)
|-- references.bib                    # BibTeX literature database (SOTA 2023-2026 with valid DOIs)
|-- config/
|   |-- metadata.tex                  # Title EN/PL, author, student ID, supervisor, bilingual abstracts
|   `-- styles.tex                    # TUL margins (inner 35mm, outer 25mm), 1.5 line spacing, listings
|-- chapters/                         # Modular English chapters
|   |-- 01_introduction.tex           # Motivation, Code-First paradigm, thesis statement, objectives
|   |-- 02_state_of_the_art.tex       # SOTA: MetaGPT, ChatDev, SWE-bench, Reflexion, DSPy, MCP
|   |-- 03_system_architecture.tex    # ADK multi-agent swarm, Pydantic v2 schemas, state machine
|   |-- 04_implementation.tex         # Execution sandbox, dynamic literature search, typesetting
|   |-- 05_verification_gates.tex     # 7 Quality Gates (MasterVerificationSuite, mutation, stylometry)
|   |-- 06_experiments_and_evaluation.tex # Case study, benchmark results, mutation scores, SLA latency
|   `-- 07_conclusions.tex            # Verification of thesis, contributions, limitations, future work
|-- figures/                          # Vector diagrams, C4 charts, and benchmark latency plots
`-- compile.bat                       # One-click Windows compilation script (Tectonic / latexmk / pdflatex)
```

---

## 🚀 Jak kompilować dokument do PDF
## 🚀 How to Compile to PDF

### Opcja A: Wtyczka w VS Code (LaTeX Workshop)
1. Otwórz plik `thesis/main.tex` w VS Code.
2. Wciśnij `Ctrl + Alt + B` (Build LaTeX project) lub kliknij ikonę **LaTeX** w bocznym pasku.
3. Kliknij `View LaTeX PDF` (`Ctrl + Alt + V`), aby otworzyć podgląd na żywo obok kodu.
### Option A: VS Code (LaTeX Workshop Extension)
1. Open `thesis/main.tex` in VS Code.
2. Press `Ctrl + Alt + B` (Build LaTeX project) or click the **LaTeX** icon on the sidebar.
3. Press `Ctrl + Alt + V` to view the compiled PDF side-by-side.

### Opcja B: Jedno polecenie przez Tectonic (Zalecane lokalnie)
Jeśli zainstalujesz lekki kompilator Tectonic (`winget install Tectonic.Tectonic`):
### Option B: Local Fast Compilation via Tectonic (~30 MB)
If you install the lightweight Tectonic compiler (`winget install Tectonic.Tectonic`):
```powershell
cd thesis
tectonic main.tex
```
Plik `main.pdf` zostanie wygenerowany w ułamku chwili.
The file `main.pdf` will be built cleanly in seconds.

### Opcja C: Overleaf (w chmurze)
Możesz spakować folder `thesis` do archiwum `.zip` lub połączyć repozytorium GitHub bezpośrednio z darmowym kontem [Overleaf](https://www.overleaf.com) i kompilować w przeglądarce.
### Option C: Overleaf Cloud
You can zip the `thesis/` folder or sync the GitHub repository directly with [Overleaf](https://www.overleaf.com) to compile online with real-time preview.

---

## ✏️ Jak edytować dane formalne
## ✏️ Modifying Formal University Data

Wszystkie dane uczelniane znajdują się w jednym pliku: [config/metadata.tex](config/metadata.tex):
- `\ThesisTitle` – Tytuł pracy po polsku
- `\ThesisAuthor` – Twoje imię i nazwisko
- `\ThesisAlbumNumber` – Numer indeksu
- `\ThesisSupervisor` – Tytuł i nazwisko promotora
- `\UniversityName`, `\FacultyName`, `\FieldOfStudy` – Dane wydziału i kierunku
- `\AbstractPL`, `\AbstractEN` – Streszczenia
- `\KeywordsPL`, `\KeywordsEN` – Słowa kluczowe

Każda zmiana w `metadata.tex` automatycznie aktualizuje stronę tytułową, oświadczenie, streszczenia oraz metadane PDF.

All administrative and formal parameters required by Politechnika Łódzka are located in [config/metadata.tex](config/metadata.tex):
- `\ThesisTitle` – English title (Primary)
- `\ThesisTitlePL` – Polish title (Mandatory translation as per TUL regulations)
- `\ThesisAuthor` – Your full name
- `\ThesisAlbumNumber` – Your student ID (nr albumu)
- `\ThesisSupervisor` – Supervisor's title and full name
- `\FacultyName` & `\InstituteName` – Faculty and Institute (e.g. WEEIA / FTIMS)
- `\FieldOfStudy` & `\Specialization` – Program and specialization
- `\AbstractEN` & `\AbstractPL` – Bilingual abstracts
- `\KeywordsEN` & `\KeywordsPL` – Bilingual keywords
