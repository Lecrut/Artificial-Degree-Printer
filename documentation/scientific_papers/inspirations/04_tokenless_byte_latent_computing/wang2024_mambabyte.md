# Scientific Paper Dossier: MambaByte: Token-free Selective State Space Model for Byte-Level Text Processing

> **Citation Key:** `@Wang2024MambaByte`  
> **Authors:** Junxiong Wang, Tushaar Gangavarapu, Jing Nathan Yan, Alexander M. Rush (Cornell University)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~290+  
> **Venue / Conference:** COLM 2024 / arXiv:2401.13660  
> **Link / DOI:** [https://arxiv.org/abs/2401.13660](https://arxiv.org/abs/2401.13660)

---

## 📌 Core Thesis and Research Motivation

Sekwencje na poziomie bajtów są znacznie dłuższe niż sekwencje tokenowe (często 4-5x dłuższe), co dla kwadratowej atencji Transformerów oznacza 16–25x wyższy koszt obliczeniowy. Z tego powodu beztokenowe modele Transformer były uznawane za niepraktyczne.

Zespół z Cornell University pod kierunkiem prof. Alexandra Rusha proponuje **MambaByte** – połączenie paradygmatu beztokenowego ze stanem selektywnym Mamba o **ściśle liniowym skalowaniu $O(N)$**. 

---

## 💡 Key Theoretical Findings

1. **Liniowy koszt długich sekwencji bajtów:** MambaByte przetwarza miliony bajtów bez wybuchu pamięciowego charakterystycznego dla atencji.
2. **Zwycięstwo nad subword Transformerami:** Na benchmarkach modelowania języka MambaByte osiąga niższy perplexity niż modele ze słownikiem tokenów przy tym samym budżecie parametrów.
3. **Niewrażliwość na zniekształcenia danych:** Model zachowuje bezbłędną zdolność wnioskowania w obecności zaszumionych danych wejściowych, znaków kontrolnych i niestandardowych formatów plików.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Byte-Level File Ingestion:** Moduł w `adk/tools/filesystem.py` odczytujący surowe strumienie binarne bez ryzyka błędów dekodowania `UnicodeDecodeError`.
- [x] **Robust Code Repair:** Naprawa uszkodzonych skryptów poprzez bezpośrednią manipulację bajtową.
