# Scientific Paper Dossier: Byte Latent Transformer: Patches Scale Better Than Tokens

> **Citation Key:** `@Meta2024BLT`  
> **Authors:** Meta Fundamental AI Research (FAIR) Team  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~320+  
> **Venue / Conference:** arXiv:2412.09871 / Meta FAIR Research  
> **Link / DOI:** [https://arxiv.org/abs/2412.09871](https://arxiv.org/abs/2412.09871)

---

## 📌 Core Thesis and Research Motivation

Tokenizacja oparta na stałym słowniku (subword tokenization) jest jedną z największych ukrytych słabości nowoczesnego AI: wprowadza nierówności językowe, podatność na ataki adwersarialne i uniemożliwia precyzyjne operowanie na poziomie pojedynczych znaków kodu źródłowego. 

Meta FAIR wprowadza **Byte Latent Transformer (BLT)** – pierwszą architekturę beztokenową, która dorównuje wydajnością i skalowalnością standardowym modelom tokenowym (skalowanie do modeli 8B parametrów i 4 bilionów bajtów), oferując przy tym wyższą odporność i elastyczność obliczeniową.

---

## 💡 Key Theoretical Findings

1. **Segmentacja sterowana entropią:** BLT wykorzystuje lekki model lokalny do obliczania entropii kolejnego bajtu. Fragmenty o niskiej entropii (np. przewidywalne słowa kluczowe `def`, `class`, wcięcia) są kompresowane w duże łaty (patches), natomiast trudne identyfikatory i złożona logika są rozbijane na drobne segmenty.
2. **Efektywność pamięci i przepustowości:** Dzięki dynamicznemu łataniu BLT redukuje liczbę kroków atencji w głębokiej sieci, osiągając przepustowość wyższą niż klasyczne modele tokenowe przy sekwencjach kodu.
3. **Niewrażliwość na zniekształcenia tekstu:** BLT zachowuje ponad **92%** skuteczności w sytuacjach, gdy kod zawiera drobne błędy zapisu lub specyficzne kodowania UTF-8, podczas gdy standardowe modele gwałtownie degradują swoje odpowiedzi.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Byte-Level Stylometry Gate:** Wykorzystanie analizy entropii na poziomie bajtów w `adk/verification/stylometry.py` do wykrywania sztucznych wzorców generacji LLM.
- [x] **Raw Byte Artifact Storage:** Architektura zapisu artefaktów odporna na uszkodzenia kodowania znaków w wielojęzycznych pracach magisterskich.

---

## 🚀 Key Strengths and Novelties

- Całkowite wyeliminowanie słownika tokenów (Tokenizer-Free).
- Dynamiczny przydział mocy obliczeniowej zależny od stopnia skomplikowania bajtów w kodzie.
