# Scientific Paper Dossier: Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward

> **Citation Key:** `@AgentSkills2026`  
> **Authors:** (Survey — multiple authors, scienceaix team)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~350+ (accumulating, February 2026)  
> **Venue / Conference:** arXiv:2602.12430 — cs.AI / cs.CL  
> **Link / DOI:** [https://arxiv.org/abs/2602.12430](https://arxiv.org/abs/2602.12430)  
> **Project Repo:** [https://github.com/scienceaix/agentskills](https://github.com/scienceaix/agentskills)

---

## 📌 Core Thesis and Research Motivation

Monolityczne modele LLM ewoluują w kierunku **modularnych agentów wyposażonych w umiejętności (skills)** — composable packages zawierające instrukcje, kod i zasoby, które agent ładuje dynamicznie bez potrzeby retrainingu. Praca mapuje ten ekosystem wzdłuż 4 osi: architektura, akwizycja, deployment i bezpieczeństwo. Kluczowy wkład: formalizacja standardu **SKILL.md** i **Skill Trust and Lifecycle Governance Framework**.

---

## 💡 Key Theoretical Findings

- **26.1%** publicznie dostępnych community skills zawiera luki bezpieczeństwa — model governance jest krytyczny, nie opcjonalny.
- **Progressive context loading** — skills ładowane są do kontekstu tylko gdy potrzebne, co drastycznie redukuje zużycie tokenów i problem "Lost in the Middle".
- **SKILL.md specification** — standardowy format opisu skill: YAML frontmatter (name, description, prerequisites) + Markdown instrukcje + opcjonalne scripts/resources.
- **Skill Trust Governance — 4-poziomowy model dostępu:**
  - Tier 1: Certified (audited, signed)
  - Tier 2: Community-reviewed
  - Tier 3: Unreviewed community
  - Tier 4: User-local (untrusted)
- MCP i Skills są komplementarne: MCP opisuje *jak* tool jest wywoływany (protokół), skill opisuje *co* agent powinien zrobić z tym toolem (strategia i wiedza).

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **SKILL.md Format:** ADK posiada własną implementację SKILL.md — każde narzędzie (`BaseTool`) ma `name` i `description` zgodne z duchem SKILL.md specification. ✅
- [x] **Progressive Loading:** `StateGraphEngine` aktywuje tylko te narzędzia, które są potrzebne w danej fazie — `Researcher` nie ładuje `TypesettingTool`, `Typesetter` nie ładuje `BenchmarkTool`. ✅
- [x] **MCP Complementarity:** Narzędzia ADK implementują MCP-compatible kontrakt równolegle z logiką skill. ✅
- [ ] **Future (Skill Governance):** Implementacja `SkillTrustGate` — weryfikacja przed załadowaniem zewnętrznego SKILL.md (hash signature, YAML schema validation, sandbox dry-run). Odpowiada Tier 1/2 z governance frameworku.
- [ ] **Future (Skill Library):** Persistent `SkillLibrary` analogiczna do Voyager — ADK zapamiętuje skuteczne strategie rozwiązania podobnych tematów prac i reużywa je w nowych projektach.

---

## 🚀 Key Strengths and Novelties

- Pierwsza systematyczna formalizacja SKILL.md jako standardu branżowego 2026.
- Empiryczne odkrycie: 26.1% community skills = podatności bezpieczeństwa — uzasadnia nasz `ToolCallAuditGate` (planowany Milestone).
- Czterostopniowy model zaufania skills doskonale mapuje się na ADK: nasze built-in tools = Tier 1 (Certified), zewnętrzne MCP servers = Tier 2-3.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

AgentSkills 2026 opisuje ekosystem skills ogólnie. ADK stosuje te zasady w **zamkniętej, akademicko-inżynierskiej domenie** z dodatkową warstwą: każda skill jest powiązana z konkretną bramką weryfikacyjną (`MasterVerificationSuite`), co tworzy feedback loop między skill execution a quality measurement — nieobecny w ogólnym modelu z przeglądu.

