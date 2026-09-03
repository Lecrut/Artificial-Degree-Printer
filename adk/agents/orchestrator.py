from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import Requirement, ThesisMetadata
from adk.core.state import ADKProjectState


class DomainProfileGenerator:
    """Generates domain-specialized requirements, bilingual abstracts, and keywords."""

    @classmethod
    def analyze_domain(cls, topic: str) -> Dict[str, Any]:
        t = topic.lower()

        # 1. AI / Agentic Systems / Machine Learning
        if any(k in t for k in ["ai", "agent", "llm", "uczenie", "machine learning", "neural", "deep learning", "nlp", "rag"]):
            return {
                "domain": "AI & Agentic Systems",
                "keywords": ["Sztuczna Inteligencja", "Systemy Wieloagentowe", "LLM", "Inżynieria Promptów", "Autonomiczna Orkiestracja", "Artificial Intelligence", "Multi-Agent Systems"],
                "abstract_pl": (
                    f"Niniejsza praca przedstawia projekt, implementację oraz rygorystyczną ewaluację empiryczną "
                    f"zaawansowanego systemu sztucznej inteligencji '{topic}'. W ramach badań zintegrowano modele "
                    "wieloagentowe, dynamiczne mechanizmy kwerendowania wiedzy SOTA oraz mechanizmy refleksji i samonaprawy kodu. "
                    "Przeprowadzone eksperymenty wykazały wysoką precyzję działania oraz odporność na halucynacje modeli językowych."
                ),
                "abstract_en": (
                    f"This thesis presents the design, implementation, and rigorous empirical evaluation of an advanced "
                    f"artificial intelligence platform entitled '{topic}'. The system integrates multi-agent orchestration, "
                    "dynamic state-of-the-art literature grounding, and autonomous code self-reflection. Experimental results "
                    "confirm high reasoning precision, low latency, and robust mitigation of language model hallucinations."
                ),
                "reqs": [
                    ("REQ-F-01", "Wieloagentowy silnik decyzyjny", "System musi realizować autonomiczną dekompozycję zadań w oparciu o wyspecjalizowane role agentowe.", True, "MUST", "Testy jednostkowe przepływu decyzyjnego"),
                    ("REQ-F-02", "Mechanizm ugruntowania w wiedzy (Grounding)", "System musi weryfikować odpowiedzi w oparciu o bazę wiedzy SOTA i eliminować halucynacje.", True, "MUST", "Walidacja faktograficzna i wskaźnik zgodności"),
                    ("REQ-F-03", "Pętla samonaprawy (Verbal Reflection)", "W przypadku niezdania testu jednostkowego agent musi autonomicznie przeanalizować traceback i naprawić kod.", True, "SHOULD", "Testy mutacyjne i testy samonaprawy"),
                    ("REQ-NF-01", "Czas inferencji decyzyjnej", "P95 czasu planowania pojedynczego kroku agentowego nie może przekraczać 1500 ms.", False, "MUST", "Pomiary w module benchmarków"),
                    ("REQ-NF-02", "Determinizm i powtarzalność", "Wszystkie decyzje systemowe muszą być rejestrowane w niezmiennym dzienniku zdarzeń (Event Sourcing).", False, "MUST", "Audyt integralności dziennika EventLog"),
                ]
            }

        # 2. Embedded / IoT / Real-Time Systems
        if any(k in t for k in ["iot", "embedded", "wbudowan", "czujnik", "sensor", "zig", "mikrokontrol", "robot", "real-time"]):
            return {
                "domain": "IoT & Embedded Systems",
                "keywords": ["Systemy Wbudowane", "Internet Rzeczy", "Czas Rzeczywisty", "Optymalizacja Pamięci", "Protokoły Komunikacyjne", "Embedded Systems", "Internet of Things", "Real-Time"],
                "abstract_pl": (
                    f"Tematem pracy jest opracowanie, zaimplementowanie oraz przetestowanie wysokowydajnego systemu wbudowanego '{topic}'. "
                    "Zaprojektowano modułową architekturę o minimalnym narzucie pamięciowym (Zero-Cost Abstractions) oraz deterministycznym "
                    "czasie reakcji na zdarzenia sprzętowe. Badania laboratoryjne potwierdziły stabilność transmisji oraz spełnienie rygorów czasu rzeczywistego."
                ),
                "abstract_en": (
                    f"This thesis focuses on the architecture, implementation, and empirical testing of a high-performance "
                    f"embedded IoT platform entitled '{topic}'. The architecture guarantees deterministic event response times, "
                    "minimal memory footprint, and robust hardware sensor interfacing. Benchmarking results validate real-time operational constraints."
                ),
                "reqs": [
                    ("REQ-F-01", "Deterministyczny sterownik I/O", "System musi zapewniać deterministyczny odczyt i przetwarzanie danych telemetrycznych.", True, "MUST", "Testy symulatora sprzętowego"),
                    ("REQ-F-02", "Buforowanie i kompresja pakietów", "Pakiet danych przesyłanych magistralą musi podlegać kompresji celem redukcji pasma transmisyjnego.", True, "MUST", "Testy poprawności kodowania binarnego"),
                    ("REQ-NF-01", "Maksymalne zużycie pamięci RAM", "Zarządzanie pamięcią nie może przekraczać zadanego limitu bufora (Zero-Allocation policy).", False, "MUST", "Profilowanie zużycia sterty i stosu"),
                    ("REQ-NF-02", "Czas reakcji na przerwania (Latency)", "Maksymalne opóźnienie obsługi zdarzenia krytycznego musi być poniżej 20 ms.", False, "MUST", "Pomiary oscyloskopowe i benchmarkowe"),
                ]
            }

        # 3. Cybersecurity / Fintech / Cryptography
        if any(k in t for k in ["bezpiecz", "security", "kryptograf", "crypto", "blockchain", "bank", "fintech", "auth", "token"]):
            return {
                "domain": "Cybersecurity & Fintech",
                "keywords": ["Cyberbezpieczeństwo", "Kryptografia Asymetryczna", "Audyt Bezpieczeństwa", "Integralność Danych", "Idempotencja", "Cybersecurity", "Fintech", "Zero-Trust"],
                "abstract_pl": (
                    f"Praca poświęcona jest zagadnieniu bezpieczeństwa i niezawodności w architekturze '{topic}'. "
                    "W ramach projektu wdrożono rygorystyczny model Zero-Trust, kryptograficzne podpisywanie transakcji "
                    "oraz mechanizmy ochrony przed atakami typu Replay i Injection. Rygorystyczne testy penetracyjne potwierdziły "
                    "odporność opracowanego rozwiązania na wektory zagrożeń zgodne ze standardem OWASP."
                ),
                "abstract_en": (
                    f"This research addresses cybersecurity and resilience within the specialized architecture entitled '{topic}'. "
                    "The system implements a strict Zero-Trust security paradigm, cryptographic transaction verification, "
                    "and comprehensive defenses against injection and replay attacks. Rigorous automated security audits confirm conformance to OWASP guidelines."
                ),
                "reqs": [
                    ("REQ-F-01", "Kryptograficzna weryfikacja transakcji", "Każde żądanie modyfikujące stan musi być podpisane cyfrowo i walidowane pod kątem integralności.", True, "MUST", "Testy algorytmów kryptograficznych"),
                    ("REQ-F-02", "Kontrola dostępu RBAC/ABAC", "System musi wymuszać granularną autoryzację z zasadą najmniejszych uprawnień.", True, "MUST", "Automatyczne testy penetracyjne uprawnień"),
                    ("REQ-NF-01", "Odporność na ataki czasowe (Timing Attacks)", "Operacje porównywania skrótów kryptograficznych muszą wykonywać się w stałym czasie (constant-time execution).", False, "MUST", "Statystyczna analiza czasu wykonania"),
                    ("REQ-NF-02", "SLA Dostępności i Czasu Odpowiedzi", "P99 czasu autoryzacji tokenu nie może przekraczać 50 ms.", False, "MUST", "Testy obciążeniowe throughput/latency"),
                ]
            }

        # 4. Distributed Cloud / Microservices / General Enterprise (Default)
        return {
            "domain": "Distributed Cloud & Enterprise Systems",
            "keywords": ["Architektura Mikrousługowa", "Inżynieria Oprogramowania", "Skalowalność Horyzontalna", "Weryfikacja AST", "Testy Obciążeniowe", "Cloud Architecture", "Microservices", "Scalability"],
            "abstract_pl": (
                f"Niniejsza praca przedstawia projekt, implementację oraz kompleksowe badania empiryczne "
                f"nowoczesnego systemu informatycznego '{topic}'. W ramach opracowania zdefiniowano architekturę modularną, "
                "zaimplementowano serwisy biznesowe z zachowaniem czystej architektury (Clean Architecture) oraz przeprowadzono "
                "automatyczną weryfikację jakości z wykorzystaniem analizy AST i testów mutacyjnych. Wyniki testów obciążeniowych "
                "wykazały znakomitą skalowalność i stabilność czasów odpowiedzi."
            ),
            "abstract_en": (
                f"This thesis details the architectural design, implementation, and empirical performance evaluation "
                f"of a modern distributed software platform entitled '{topic}'. The project adheres to Clean Architecture principles, "
                "incorporating automated AST code verification and mutation testing. Comprehensive load testing demonstrates superior "
                "throughput and sub-millisecond response latency under concurrent client workloads."
            ),
            "reqs": [
                ("REQ-F-01", "Modularna warstwa logiki biznesowej", "System musi separować domenę biznesową od adapterów wejścia/wyjścia (Clean Architecture).", True, "MUST", "Testy jednostkowe komponentów"),
                ("REQ-F-02", "Automatyczny audyt jakości kodu i manifestów", "Kod musi przechodzić 100% testów jednostkowych oraz weryfikację składni i spójności symboli.", True, "MUST", "Bramki weryfikacyjne CodeVerificationGate"),
                ("REQ-F-03", "Interfejs API i serializacja danych", "Wymiana danych musi odbywać się za pośrednictwem zdefiniowanych schematów z walidacją typów.", True, "MUST", "Testy integracyjne endpointów"),
                ("REQ-NF-01", "Wydajność i skalowalność odpowiedzi (SLA)", "Czas odpowiedzi serwisu p95 nie może przekraczać 200 ms przy obciążeniu do 500 współbieżnych klientów.", False, "MUST", "Empiryczne pomiary w module benchmarków"),
                ("REQ-NF-02", "Bezpieczeństwo i izolacja wykonawcza", "Wykonywanie zadań musi odbywać się w izolowanym środowisku piaskownicy z kontrolowanym czasem życia.", False, "MUST", "Testy limitowania zasobów w SandboxRunner"),
            ]
        }


class OrchestratorAgent(BaseAgent):
    name = "promotor_ai"
    role_description = "Główny planista i opiekun naukowy projektu/pracy dyplomowej"
    capabilities = ["planning", "decomposition", "governance", "human_review", "domain_specialization"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="intake_and_planning",
            agent_name=self.name,
            payload={"request": state.request},
        )

        title = state.request.strip() or "Zaawansowany System Informatyczny i Platforma Agentowa"
        state.metadata.title = title

        # Inteligentna analiza dziedziny i generacja profili
        profile = DomainProfileGenerator.analyze_domain(title)

        if not state.metadata.abstract_pl:
            state.metadata.abstract_pl = profile["abstract_pl"]
        if not state.metadata.abstract_en:
            state.metadata.abstract_en = profile["abstract_en"]
        if not state.metadata.keywords:
            state.metadata.keywords = profile["keywords"]

        # Wygeneruj dedykowane wymagania dziedzinowe jeśli puste
        if not state.requirements:
            state.requirements = [
                Requirement(
                    id=r[0],
                    title=r[1],
                    description=r[2],
                    is_functional=r[3],
                    priority=r[4],
                    verification_method=r[5],
                )
                for r in profile["reqs"]
            ]

        state.notes.append(f"[{self.name}] Zainicjalizowano strukturę pracy w dziedzinie '{profile['domain']}' ({len(state.requirements)} wymagań) dla tematu: {title}")
        state.current_stage = "research"
        if "intake_and_planning" not in state.completed_stages:
            state.completed_stages.append("intake_and_planning")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="intake_and_planning",
            agent_name=self.name,
            payload={"domain": profile["domain"], "requirements_count": len(state.requirements)},
        )
        return state
