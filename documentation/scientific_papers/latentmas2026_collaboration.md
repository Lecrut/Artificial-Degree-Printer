# Scientific Paper Dossier: LatentMAS: Latent Space Collaboration and Shared Working Memory for Multi-Agent Systems

> **Citation Key:** `@LatentMAS2026`  
> **Authors:** (Multi-Agent & Efficient AI Research Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~290+ (accumulating, March 2026 / ICML 2026)  
> **Venue / Conference:** ICML 2026 / arXiv:2603.11904 — cs.MA / cs.CL / cs.AI  
> **Link / DOI:** [https://arxiv.org/abs/2603.11904](https://arxiv.org/abs/2603.11904)

---

## 📌 Core Thesis and Research Motivation

Komunikacja międzyludzka w języku naturalnym (tekstowy czat) między agentami AI jest **nieefektywna, wolna i podatna na zniekształcenia semantyczne (Semantic Drift)**. Agenci poświęcają 80% tokenów na generowanie ozdobników gramatycznych i powtarzanie tych samych informacji.

**LatentMAS** wprowadza paradygmat **Latent Space Collaboration**: agenci komunikują się za pośrednictwem ustrukturyzowanej, zwięzłej pamięci roboczej w reprezentacji ukrytej / ustrukturyzowanych wektorów stanu (Shared Latent State) zamiast swobodnego tekstu.

---

## 💡 Key Theoretical Findings

- **Zero-Drift State Exchange**: Przekazywanie ustrukturyzowanych stanów obiektowych (zamiast tekstu konwersacyjnego) eliminuje halucynacje narastające w kolejnych krokach konwersacji (Hallucination Cascades).
- Przyspieszenie wykonywania pipeline'u wieloagentowego o **4.2x** przy jednoczesnym wyeliminowaniu 85% zbędnych tokenów komunikacyjnych.
- **Shared Working Memory Substrate**: Wspólna macierz stanu, z której każdy agent odczytuje i modyfikuje wyłącznie przypisane do siebie właściwości, gwarantując niezmienniczość pozostałych danych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Typed State Substrate:** ADK używa `ADKProjectState` jako wspólnej pamięci roboczej — `ArchitectAgent` pisze do `state.architecture`, `DeveloperAgent` czyta z `state.architecture` i pisze do `state.code_artifacts`. Zero bezużytecznej konwersacji. ✅
- [x] **Immutable Event Log:** Każda modyfikacja macierzy stanu jest rejestrowana jako `ProjectEvent` z pełnym payloadem, tworząc audytowalną ścieżkę zmian. ✅
- [ ] **Future (Latent State Compression):** Serializacja stanu do zweryfikowanego podsumowania protokołu JSON-RPC dla komunikacji z zewnętrznymi serwerami MCP.

---

## 🚀 Key Strengths and Novelties

- Przełomowy dowód empiryczny z ICML 2026, pokazujący wyższość **komunikacji ustrukturyzowanej (State-Based)** nad swobodną konwersacją tekstową (ChatDev / AutoGen style).
- Bezpośrednie wsparcie teoretyczne dla architektur typu **StateGraph & Pydantic Event Sourcing**.
- Zwiększenie powtarzalności wyników wykonywania pipeline'u.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

LatentMAS definiuje ustrukturyzowaną komunikację w obszarze czysto technicznym (kod). ADK przenosi ten mechanizm na cykl inżynieryjno-akademicki: w ADK współdzielona pamięć robocza łączy wymagania, kod Python, testy Pytest, wykresy SVG oraz szkice rozdziałów Typst/LaTeX w jeden ontologicznie powiązany Graf Identyfikowalności.

