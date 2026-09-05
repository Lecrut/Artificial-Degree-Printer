# 🌪️ 01. Diffusion Models & Discrete Flow for Code and Structures

Kategoria poświęcona nieszablonowemu wykorzystaniu modeli dyfuzyjnych (Diffusion Models) oraz dopasowywania przepływów (Flow Matching) w zadaniach innych niż generowanie obrazu – w szczególności w inżynierii oprogramowania, syntezie kodu źródłowego oraz generowaniu hierarchicznych drzew składniowych (AST).

---

## 💡 Dlaczego to Przełom dla Pracy Magisterskiej?

Tradycyjne modele językowe generują kod **autoregresyjnie** (od lewej do prawej, token po tokenie). W kodzie programistycznym jest to z definicji ułomne: deklaracja zmiennej na początku funkcji zależy od jej użycia na końcu, a typy muszą być spójne globalnie.

Modele dyfuzyjne dla kodu wprowadzają:
1. **Globalne planowanie przestrzenne:** Program zaczyna się jako zaszumiony szkic (szum dyskretny) i w kolejnych krokach odszumiania krystalizuje się jednocześnie we wszystkich liniach.
2. **Świadomość drzewa składniowego (AST-guided Denoising):** Odszumianie operuje na węzłach gramatycznych, uniemożliwiając powstawanie błędów składniowych.
3. **Natywną edycję i refaktoryzację:** Modyfikacja kodu polega na dodaniu szumu tylko do modyfikowanej funkcji i ponownym jej odszumieniu przy zachowaniu reszty programu w stanie nienaruszonym.

---

## 📚 Publikacje w Klastrze:
- [`treediff2025_ast_diffusion.md`](treediff2025_ast_diffusion.md) (`@TreeDiff2025`) – *AST-Guided Code Generation with Diffusion LLMs (2025)*
- [`diffucoder2025_masked_diffusion.md`](diffucoder2025_masked_diffusion.md) (`@DiffuCoder2025`) – *Understanding and Improving Masked Diffusion Models for Code Generation (2025)*
- [`ancoder2026_anchored_diffusion.md`](ancoder2026_anchored_diffusion.md) (`@AnCoder2026`) – *AnCoder: Anchored Code Generation via Discrete Diffusion Models (2026)*
- [`cdc2026_constrained_diffusion.md`](cdc2026_constrained_diffusion.md) (`@CDC2026`) – *Constrained Code Generation with Discrete Diffusion (CDC) (2026)*
