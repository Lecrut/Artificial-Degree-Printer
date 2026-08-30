# Security, Safety & Sandboxing in ADK (2027)

> **Kategoria:** Bezpieczeństwo, Izolacja i Etyka Autonomicznego Systemu Agentowego  
> **Podstawa Naukowa:** Constitutional AI (Anthropic), AgentBench (Liu et al.), SWE-bench (Jimenez et al.)

---

## 1. Zagrożenia Specyficzne dla Systemów Generujących Kod (Threat Model)

System ADK generuje i uruchamia **nieznany wcześniej kod** na maszynie użytkownika. To odróżnia go od zwykłych chatbotów. Poniżej definiujemy model zagrożeń (Threat Model):

```
  [ ZAGROŻENIE 1 ] Prompt Injection          -> LLM generuje kod wykonujący działania poza zakresem tematu
  [ ZAGROŻENIE 2 ] Code Execution Escape     -> Generowany kod próbuje modyfikować pliki poza workspace
  [ ZAGROŻENIE 3 ] Infinite Loop / Resource  -> Generowany kod zawiera nieskończoną pętlę
  [ ZAGROŻENIE 4 ] Sensitive Data Exfil      -> Generowany kod odczytuje /etc/passwd lub zmienne środowiskowe
  [ ZAGROŻENIE 5 ] Dependency Confusion      -> Wygenerowany requirements.txt instaluje złośliwy pakiet
  [ ZAGROŻENIE 6 ] Hallucinated Citations    -> LLM cytuje nieistniejące artykuły z błędnymi DOI
  [ ZAGROŻENIE 7 ] AI Watermark Detection    -> Praca dyplomowa wykryta przez systemy antyplagiatowe JSA
```

---

## 2. Zaimplementowane Mechanizmy Ochronne

### Ochrona O1: Timeout Sandbox (Hard Time Limit)
`SandboxRunnerTool` uruchamia każdy generowany kod w subprocess z **twardym limitem czasowym** (domyślnie 30 sekund):

```python
process = subprocess.run(
    cmd, timeout=self.timeout_seconds, capture_output=True
)
```

- Jeśli kod przekroczy limit → `subprocess.TimeoutExpired` → `SandboxExecutionResult(passed=False)`
- Nieskończone pętle są automatycznie przerywane

### Ochrona O2: Workspace Isolation (Relative Path Enforcement)
`FileSystemTool` akceptuje wyłącznie **względne ścieżki** zrestryktowane do katalogu `workspace_dir`. Każda próba zapisu poza workspace jest blokowana:

```python
def _safe_path(self, relative_path: str) -> Path:
    resolved = (self.workspace_dir / relative_path).resolve()
    if not str(resolved).startswith(str(self.workspace_dir)):
        raise SecurityError("Path traversal attempt blocked")
```

### Ochrona O3: AST Syntax Gate (Pre-Execution Validation)
`CodeVerificationGate` parsuje kod przez Python `ast.parse()` **przed uruchomieniem** sandboxa. Kod z błędem składni nigdy nie jest wykonywany.

### Ochrona O4: Citation Hallucination Prevention (BibTeX Integrity)
`CitationVerificationGate` weryfikuje że:
- Każdy klucz `@cite` istnieje w `references.bib`
- Rok publikacji spełnia SOTA Horizon ($\ge 2023$)
- Format BibTeX jest parsowany i syntaktycznie poprawny

### Ochrona O5: English Naming Gate (Injection Prevention)
`EnglishNamingVerificationGate` blokuje ścieżki zawierające znaki specjalne lub nieanglojęzyczne znaki diakrytyczne, które mogłyby być wektorami path-injection.

### Ochrona O6: Stylometry Gate (AI Detectability Risk)
`StylometryAuditGate` szacuje ryzyko wykrycia przez systemy JSA na podstawie:
- Wskaźnika TTR (Type-Token Ratio)
- Wariancji długości zdań
- Rozkładu n-gramów typowych dla LLM

---

## 3. Znane Ograniczenia i Akceptowane Ryzyka

| Ryzyko | Poziom | Akceptacja i Uzasadnienie |
| :--- | :---: | :--- |
| Kod może odczytać zmienne środowiskowe `os.environ` | 🟡 MEDIUM | Subprocess dziedziczy env hosta. Zalecane: `env={}` w subprocess przy wrażliwych deploymentach. |
| Generowany `requirements.txt` nie jest weryfikowany | 🟡 MEDIUM | Użytkownik instaluje zależności manualnie; system nie uruchamia `pip install` automatycznie. |
| Bez Docker: brak pełnej izolacji systemu plików | 🟠 HIGH (Local) | Akceptowalne dla lokalnego developmentu. Milestone 2 (Roadmap) dodaje Docker driver. |
| LLM może generować biased content | 🟡 MEDIUM | `AcademicStyleGate` filtruje jawny bias. Ostateczna weryfikacja przez człowieka (promotora). |

---

## 4. Zasady Bezpieczeństwa Obowiązujące w ADK (Security Principles)

Opieramy się na filozofii **Constitutional AI** (Anthropic, 2022/2024):

1. **Zasada Minimalnych Uprawnień**: Każdy agent i narzędzie posiada tylko te uprawnienia, których bezwzględnie wymaga jego funkcja.
2. **Zasada Transparentności**: Każde wywołanie narzędzia jest logowane w Event Log z timestampem, agentem i wynikiem.
3. **Zasada Ograniczonego Zakresu**: Workspace jest ograniczony do jednego katalogu projektu. Poza nim system jest ślepy.
4. **Zasada Twardego Dowodu**: Żaden output nie jest "zaufany" bez przejścia przynajmniej jednej bramki walidacyjnej (exit_code == 0, AST parse success, citation key found).
5. **Zasada Ludzkiej Weryfikacji Końcowej**: System producuje dane wejściowe dla promotora i studenta — finalna odpowiedzialność akademicka spoczywa na człowieku.

