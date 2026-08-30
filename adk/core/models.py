from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DegreeType(str, Enum):
    ENGINEERING = "engineering"  # Inżynierska
    MASTER = "master"            # Magisterska
    BACHELOR = "bachelor"        # Licencjacka
    RESEARCH_PAPER = "paper"     # Artykuł naukowy


class ThesisMetadata(BaseModel):
    title: str = Field(..., description="Tytuł pracy dyplomowej lub projektu")
    subtitle: Optional[str] = Field(None, description="Podtytuł lub opis rozszerzony")
    author: str = Field(default="Autor Projektu", description="Imię i nazwisko dyplomanta")
    supervisor: str = Field(default="dr inż. Promotor Akademicki", description="Promotor pracy")
    institution: str = Field(default="Politechnika / Uczelnia Techniczna", description="Uczelnia")
    faculty: str = Field(default="Wydział Informatyki", description="Wydział")
    field_of_study: str = Field(default="Informatyka Stosowana", description="Kierunek studiów")
    specialization: Optional[str] = Field(default="Inżynieria Oprogramowania i Systemy AI", description="Specjalność")
    year: int = Field(default=2027, description="Rok obrony/ukończenia")
    degree_type: DegreeType = Field(default=DegreeType.ENGINEERING, description="Typ pracy")
    language: str = Field(default="pl", description="Język pracy (pl/en)")
    keywords: List[str] = Field(default_factory=list, description="Słowa kluczowe")
    abstract_pl: Optional[str] = Field(None, description="Streszczenie w języku polskim")
    abstract_en: Optional[str] = Field(None, description="Streszczenie w języku angielskim")


class Requirement(BaseModel):
    id: str = Field(..., description="Identyfikator wymagania, np. REQ-F-01")
    title: str = Field(..., description="Krótki tytuł wymagania")
    description: str = Field(..., description="Dokładny opis wymagania")
    is_functional: bool = Field(default=True, description="Czy wymaganie jest funkcjonalne")
    priority: str = Field(default="MUST", description="Priorytet MoSCoW (MUST, SHOULD, COULD, WONT)")
    verification_method: str = Field(default="Test jednostkowy / Test integracyjny", description="Sposób weryfikacji")


class ArchitectureSpec(BaseModel):
    system_overview: str = Field(..., description="Opis koncepcji i architektury systemu")
    tech_stack: Dict[str, str] = Field(default_factory=dict, description="Technologie (np. Backend: Python/FastAPI)")
    modules: List[Dict[str, str]] = Field(default_factory=list, description="Lista modułów z opisem")
    data_models: List[Dict[str, Any]] = Field(default_factory=list, description="Główne modele danych i schemat bazy")
    diagram_mermaid: Optional[str] = Field(None, description="Diagram architektury w formacie Mermaid")
    security_considerations: List[str] = Field(default_factory=list, description="Aspekty bezpieczeństwa i skalowalności")


class CodeArtifact(BaseModel):
    path: str = Field(..., description="Względna ścieżka do pliku (wyłącznie po angielsku), np. src/core/engine.py")
    content: str = Field(..., description="Zawartość kodu źródłowego")
    language: str = Field(default="python", description="Język programowania")
    description: str = Field(..., description="Opis przeznaczenia pliku")
    is_test: bool = Field(default=False, description="Czy plik jest testem")


class BenchmarkMetric(BaseModel):
    name: str = Field(..., description="Nazwa metryki, np. Throughput (req/s), Latency p95 (ms)")
    value: float = Field(..., description="Wartość metryki")
    unit: str = Field(default="", description="Jednostka miary")
    target: Optional[float] = Field(None, description="Wartość docelowa / SLA")
    passed: bool = Field(default=True, description="Czy spełnia założenia projektowe")


class BenchmarkResult(BaseModel):
    scenario_name: str = Field(..., description="Nazwa scenariusza testowego/eksperymentu")
    description: str = Field(..., description="Opis warunków badania")
    metrics: List[BenchmarkMetric] = Field(default_factory=list, description="Wyniki pomiarów")
    raw_data_path: Optional[str] = Field(None, description="Ścieżka do pliku CSV/JSON z surowymi danymi")
    chart_image_path: Optional[str] = Field(None, description="Ścieżka do wygenerowanego wykresu SVG/PNG/PDF")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Citation(BaseModel):
    key: str = Field(..., description="Klucz cytowania BibTeX, np. Wu2023AutoGen")
    title: str = Field(..., description="Tytuł publikacji")
    authors: List[str] = Field(default_factory=list, description="Lista autorów")
    year: int = Field(..., ge=1900, description="Rok publikacji")
    venue: Optional[str] = Field(None, description="Konferencja, czasopismo lub wydawnictwo")
    doi: Optional[str] = Field(None, description="Identyfikator DOI")
    url: Optional[str] = Field(None, description="Adres URL publikacji")
    citations_count: Optional[int] = Field(default=None, description="Szacowana liczba cytowań publikacji")
    bibtex: str = Field(..., description="Pełny rekord BibTeX")
    relevance_note: Optional[str] = Field(None, description="Krótka notatka dlaczego praca jest cytowana")


class AnalyzedPaper(BaseModel):
    key: str = Field(..., description="Identyfikator / klucz cytowania, np. Wu2023AutoGen")
    title: str = Field(..., description="Pełny tytuł artykułu naukowego")
    authors: List[str] = Field(default_factory=list, description="Autorzy pracy")
    year: int = Field(..., ge=1900, description="Rok wydania")
    url_or_doi: str = Field(..., description="Link do publikacji lub identyfikator DOI")
    venue: Optional[str] = Field(None, description="Czasopismo / Konferencja")
    citations_count: int = Field(default=100, description="Liczba cytowań (wysoki autorytet)")
    core_idea: str = Field(..., description="Główna idea i teza artykułu")
    key_takeaways: List[str] = Field(default_factory=list, description="Najważniejsze wnioski teoretyczne")
    actionable_implementation_items: List[str] = Field(
        default_factory=list, description="Konkretne mechanizmy i rozwiązania do wdrożenia w naszym projekcie"
    )
    strengths: List[str] = Field(default_factory=list, description="Mocne strony i innowacje opisane w artykule")
    limitations_addressed_by_us: List[str] = Field(
        default_factory=list, description="Ograniczenia artykułu, które nasz projekt rozwiązuje lub ulepsza"
    )


class ChapterDraft(BaseModel):
    number: int = Field(..., description="Numer rozdziału (1, 2, 3...)")
    title: str = Field(..., description="Tytuł rozdziału")
    content_typst: str = Field(..., description="Treść rozdziału w składni Typst")
    content_latex: Optional[str] = Field(None, description="Treść rozdziału w składni LaTeX")
    summary: str = Field(..., description="Podsumowanie zawartości rozdziału")
    citations_used: List[str] = Field(default_factory=list, description="Klucze BibTeX użyte w rozdziale")
    figures_referenced: List[str] = Field(default_factory=list, description="Identyfikatory rysunków")
    code_snippets_referenced: List[str] = Field(default_factory=list, description="Ścieżki do kodu zacytowane w rozdziale")


class VerificationIssue(BaseModel):
    stage: str = Field(..., description="Etap, na którym wystąpił problem")
    severity: str = Field(default="ERROR", description="Poziom istotności: INFO, WARNING, ERROR, CRITICAL")
    message: str = Field(..., description="Opis problemu")
    location: Optional[str] = Field(None, description="Plik / rozdział / linia")
    suggested_fix: Optional[str] = Field(None, description="Zalecany sposób naprawy")


class VerificationReport(BaseModel):
    passed: bool = Field(..., description="Czy projekt spełnił wszystkie bramki jakościowe")
    score: float = Field(default=100.0, description="Ogólna ocena jakości w skali 0-100%")
    code_verification_passed: bool = Field(default=True, description="Wynik testów i linterów kodu")
    citations_verified: bool = Field(default=True, description="Wynik weryfikacji bibliografii")
    english_naming_passed: bool = Field(default=True, description="Weryfikacja angielskich nazw plików")
    cross_consistency_passed: bool = Field(default=True, description="Zgodność tekstu z kodem źródłowym")
    style_verified: bool = Field(default=True, description="Poprawność stylu akademickiego")
    issues: List[VerificationIssue] = Field(default_factory=list, description="Wykryte uwagi i błędy")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HarnessPatch(BaseModel):
    id: str = Field(..., description="Unikalny identyfikator poprawki, np. HP-DEV-001")
    target_agent: str = Field(..., description="Nazwa agenta, dla którego poprawka obowiązuje, np. developer, researcher")
    trigger_condition: str = Field(..., description="Warunek wyzwalający poprawkę (np. błąd składni AST, niski TTR)")
    patch_instruction: str = Field(..., description="Proceduralna instrukcja naprawcza wstrzykiwana do promptu/kontekstu")
    verification_gate: str = Field(..., description="Bramka weryfikacyjna, która zatwierdziła patch (GSME gate)")
    success_count: int = Field(default=1, description="Liczba pomyślnych zastosowań tej poprawki")
    is_active: bool = Field(default=True, description="Czy poprawka jest aktywna")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HarnessRepairRegistry(BaseModel):
    patches: List[HarnessPatch] = Field(default_factory=list, description="Lista udokumentowanych i zweryfikowanych poprawek harnessu")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

