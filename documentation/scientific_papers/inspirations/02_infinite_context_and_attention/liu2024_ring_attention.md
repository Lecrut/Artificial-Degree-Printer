# Scientific Paper Dossier: RingAttention with Blockwise Transformers for Near-Infinite Context

> **Citation Key:** `@Liu2024RingAttention`  
> **Authors:** Hao Liu, Matei Zaharia, Pieter Abbeel (UC Berkeley)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~600+  
> **Venue / Conference:** ICLR 2024 / arXiv:2310.01889  
> **Link / DOI:** [https://arxiv.org/abs/2310.01889](https://arxiv.org/abs/2310.01889)

---

## 📌 Core Thesis and Research Motivation

Główną barierą w trenowaniu i wnioskowaniu na sekwencjach rzędu milionów tokenów jest to, że nawet przy zastosowaniu FlashAttention bufor pamięci pojedynczego akceleratora GPU ulega wyczerpaniu (Out-Of-Memory).

Zespół z UC Berkeley wprowadza **RingAttention** – technikę, która rozprasza obliczenia warstwy atencji pomiędzy wiele urządzeń GPU połączonych w strukturę pierścienia (Ring Topology). Obliczenia bloków nakładają się w czasie rzeczywistym na komunikację peer-to-peer (P2P), umożliwiając skalowanie kontekstu wprost proporcjonalnie do liczby GPU.

---

## 💡 Key Theoretical Findings

1. **Komunikacja w Pierścieniu:** Tokeny kluczy i wartości (KV) krążą po pierścieniu urządzeń, podczas gdy zapytania (Q) pozostają lokalne, co eliminuje konieczność gromadzenia całej sekwencji w jednym węźle.
2. **Skalowanie do 10 000 000+ tokenów:** Dowiedziono empirycznie możliwości przetworzenia książek, wielogodzinnych nagrań wideo oraz całych repozytoriów kodu bez utraty jakości.
3. **Zero Overhead:** Idealne ukrycie czasu przesyłu danych za czasem obliczeń na Tensor Cores.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Distributed Artifact Verification:** Koncepcja rozproszonej bramki audytowej przetwarzającej równolegle wszystkie rozdziały pracy i moduły oprogramowania.
- [x] **Ring Traceability Engine:** Przesyłanie wektorów spójności pomiędzy agentami w deterministycznym pierścieniu.

---

## 🚀 Key Strengths and Novelties

- Praktyczne zniesienie fizycznego limitu pamięci dla ultra-długich kontekstów.
