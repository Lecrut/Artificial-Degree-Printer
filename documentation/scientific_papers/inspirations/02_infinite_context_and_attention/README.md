# ⚡ 02. Infinite Context & Novel Attention Mechanisms

Kategoria dedykowana przełamaniu wąskiego gardła tradycyjnej atencji $O(N^2)$ (Quadratic Attention) oraz eliminacji naiwnego dzielenia dokumentów i repozytoriów na małe fragmenty (batching / chunking). 

Badamy mechanizmy pozwalające modelowi przetworzyć **całą 80-stronicową pracę dyplomową oraz kompletny kod projektu za jednym zamachem (Single-Pass)** w stałym narzucie pamięciowym $O(1)$.

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

Dotychczasowe systemy RAG (Retrieval-Augmented Generation) dzielą dokumentację na małe kawałki (np. 500 tokenów) i szukają podobieństwa cosinusowego. Skutek:
- Model traci całościowy obraz zależności architektonicznych.
- Nie potrafi zweryfikować, czy twierdzenie z Rozdziału 1 nie stoi w sprzeczności z dowodem w Rozdziale 5.
- Występuje efekt "Lost-in-the-Middle".

Nowe mechanizmy atencji (Infini-attention od Google oraz Native Sparse Attention od DeepSeek):
1. **Pojedynczy przebieg (Single-Pass Omnipresence):** Analiza 1 000 000+ tokenów bez rozbijania na batche.
2. **Pamięć kompresyjna (Compressive Memory):** Reprezentowanie milionów tokenów przeszłości w zwartej macierzy skumulowanej pamięci.
3. **Sprzętowa rzadkość (Hardware-Aligned Sparsity):** Dynamiczny dobór kluczowych tokenów z zachowaniem 10-krotnie większej przepustowości GPU.

---

## 📚 Publikacje w Klastrze:
- [`google2024_infini_attention.md`](google2024_infini_attention.md) (`@Google2024InfiniAttention`) – *Leave No Context Behind: Efficient Infinite Context with Infini-attention (Google 2024)*
- [`deepseek2025_nsa.md`](deepseek2025_nsa.md) (`@DeepSeek2025NSA`) – *Native Sparse Attention: Hardware-Aligned and Natively Trainable Sparse Attention (DeepSeek 2025)*
- [`dao2024_mamba2_ssd.md`](dao2024_mamba2_ssd.md) (`@Dao2024Mamba2`) – *Transformers are SSMs: State Space Duality & Mamba-2 (ICML 2024)*
- [`liu2024_ring_attention.md`](liu2024_ring_attention.md) (`@Liu2024RingAttention`) – *RingAttention with Blockwise Transformers for Near-Infinite Context (ICLR 2024)*
- [`behrouz2025_titans_memory.md`](behrouz2025_titans_memory.md) (`@Behrouz2025Titans`) – *Titans: Learning to Memorize at Test Time (Google Research 2025)*
