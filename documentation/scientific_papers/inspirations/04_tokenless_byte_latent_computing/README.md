# 💾 04. Tokenless & Byte-Latent Computing

Kategoria poświęcona przełamaniu dogmatu tokenizacji (BPE, SentencePiece) w modelach generatywnych dla inżynierii oprogramowania. 

Analizujemy architekturę **Byte Latent Transformer (BLT)** od Meta FAIR (2024/2026) oraz metody operowania bezpośrednio na strumieniach bajtów, bitów i reprezentacjach binarnych.

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

Wszystkie współczesne LLM polegają na słownikach tokenów (np. 32k, 128k tokenów). W kodzie źródłowym i analizie technicznej rodzi to ogromne problemy:
- Tokenizatory psują wcięcia, znaki specjalne, regexy i unikalne nazwy zmiennych (tzw. "tokenization tax").
- Modele nie rozumieją składni na poziomie pojedynczych znaków ani arytmetyki bitowej.
- Trudno przetwarzać skompilowany kod maszynowy, binarki czy skompresowane formaty AST.

Architektury beztokenowe (Byte-Level):
1. **Dynamiczne łatanie na podstawie entropii (Entropy-Guided Dynamic Patching):** Zamiast sztywnych tokenów, model grupuje bajty w elastyczne "łaty" w zależności od trudności ich przewidywania.
2. **Natywne zrozumienie kodu binarnego i bytecode:** Model może czytać i modyfikować pliki `.pyc`, bytecode WebAssembly czy pliki ELF bezpośrednio.
3. **Absolutna odporność na literówki i szum:** Brak problemu tokenów "out-of-vocabulary" (OOV).

---

## 📚 Publikacje w Klastrze:
- [`meta2024_byte_latent_transformer.md`](meta2024_byte_latent_transformer.md) (`@Meta2024BLT`) – *Byte Latent Transformer: Patches Scale Better Than Tokens (Meta FAIR 2024)*
- [`fast_blt2026_speculative_bytes.md`](fast_blt2026_speculative_bytes.md) (`@FastBLT2026`) – *Fast Byte Latent Transformer: Parallel Speculative Byte Generation (2026)*
- [`wang2024_mambabyte.md`](wang2024_mambabyte.md) (`@Wang2024MambaByte`) – *MambaByte: Token-free Selective State Space Model (COLM 2024)*
