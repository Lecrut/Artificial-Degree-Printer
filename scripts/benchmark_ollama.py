"""Benchmark lokalnej instancji Ollama na bieżącej konfiguracji ADK (.env).

Mierzy dla obu skonfigurowanych modeli (SML i LRM):
- czas załadowania modelu (cold/switch load) oraz podział VRAM / RAM z `/api/ps`,
- czysty prefill (bez trafienia w KV-cache dzięki unikalnemu prefiksowi) w ms/s oraz tok/s,
- generację JSON (`format="json"`, `think=False`, identycznie jak w ADK) w s oraz tok/s,
- koszt przełączenia między modelami (`SML -> LRM -> SML`).

Użycie:
    .venv/Scripts/python.exe scripts/benchmark_ollama.py
    .venv/Scripts/python.exe scripts/benchmark_ollama.py --gen-tokens 256 --prompt-chars 1500,14000,28000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adk.core.connection import LLMConnectionManager  # noqa: E402

_FILLER_BLOCK = (
    "Module specification entry: signal processing pipeline with sliding window normalization, "
    "z-score thresholding, subspace projection, precision-recall integration, and deterministic RNG seeding. "
)


def _build_prompt(target_chars: int, gen_tokens: int) -> tuple[str, str]:
    """(system_prompt, user_prompt) z unikalnym prefiksem na samym początku, aby wymusić pełny prefill bez KV-cache."""
    nonce = uuid.uuid4().hex
    system_prompt = (
        f"[bench-session-{nonce}] You are a Python module benchmarking assistant. "
        "Always output strictly a valid JSON object."
    )
    task_tail = (
        "\n\nReturn a JSON object with keys \"module\", \"constants\" (list of 8 objects with name, type, value, note) "
        f"and \"functions\" (list of 8 detailed function descriptions so the response uses around {gen_tokens} tokens)."
    )
    body_budget = max(120, target_chars - len(system_prompt) - len(task_tail))
    repeats = (body_budget // len(_FILLER_BLOCK)) + 1
    filler = (_FILLER_BLOCK * repeats)[:body_budget]
    user_prompt = f"Nonce: {nonce}\nContext:\n{filler}{task_tail}"
    return system_prompt, user_prompt


def _ollama_ps(base_url: str, timeout: float = 5.0) -> list[dict[str, Any]]:
    try:
        req = urllib.request.Request(f"{base_url}/api/ps", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m for m in data.get("models", []) if isinstance(m, dict)]
    except Exception:
        return []


def _format_ps_entry(models_ps: list[dict[str, Any]], model_name: str) -> str:
    prefix = model_name.split(":")[0]
    match = next(
        (m for m in models_ps if m.get("name") == model_name or str(m.get("name", "")).startswith(prefix)),
        None,
    )
    if not match:
        return "brak w /api/ps"
    size = int(match.get("size") or 0)
    vram = int(match.get("size_vram") or 0)
    gb_total = size / (1024**3)
    gb_vram = vram / (1024**3)
    pct_gpu = (100.0 * vram / size) if size else 0.0
    ctx = match.get("context_length")
    ctx_info = f", ctx={ctx}" if ctx else ""
    return f"VRAM {gb_vram:.2f}/{gb_total:.2f} GiB ({pct_gpu:.0f}% GPU){ctx_info}"


def _call_generate(
    generate_url: str,
    model_name: str,
    tier: str,
    system_prompt: str,
    user_prompt: str,
    num_ctx: int,
    num_predict: int,
    timeout: int,
) -> dict[str, Any]:
    options: dict[str, Any] = {
        "num_ctx": num_ctx,
        "num_predict": num_predict,
        "temperature": 0.2,
    }
    num_gpu = os.environ.get(f"HARNESS_OLLAMA_{tier.upper()}_NUM_GPU")
    if num_gpu not in (None, ""):
        options["num_gpu"] = int(num_gpu)

    body = {
        "model": model_name,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": options,
    }
    req = urllib.request.Request(
        generate_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    wall_s = time.perf_counter() - t0

    load_s = int(raw.get("load_duration") or 0) / 1e9
    p_tok = int(raw.get("prompt_eval_count") or 0)
    p_s = int(raw.get("prompt_eval_duration") or 0) / 1e9
    g_tok = int(raw.get("eval_count") or 0)
    g_s = int(raw.get("eval_duration") or 0) / 1e9
    tot_s = int(raw.get("total_duration") or 0) / 1e9

    return {
        "tier": tier,
        "model": model_name,
        "load_s": load_s,
        "prompt_tok": p_tok,
        "prefill_s": p_s,
        "prefill_tps": (p_tok / p_s) if p_s > 0 else 0.0,
        "gen_tok": g_tok,
        "gen_s": g_s,
        "gen_tps": (g_tok / g_s) if g_s > 0 else 0.0,
        "total_s": tot_s,
        "wall_s": wall_s,
        "done_reason": str(raw.get("done_reason") or ""),
    }


def _print_row(label: str, r: dict[str, Any]) -> None:
    print(
        f"  {label:<18} | load={r['load_s']:5.2f}s | "
        f"prefill: {r['prompt_tok']:5d} tok w {r['prefill_s']:6.2f}s ({r['prefill_tps']:7.1f} tok/s) | "
        f"gen: {r['gen_tok']:4d} tok w {r['gen_s']:6.2f}s ({r['gen_tps']:6.1f} tok/s) | "
        f"wall={r['wall_s']:6.2f}s [{r['done_reason']}]",
        flush=True,
    )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Benchmark prefillu i generacji modeli SML i LRM w Ollama.")
    parser.add_argument("--gen-tokens", type=int, default=256, help="Limit tokenów generacji (num_predict) w teście.")
    parser.add_argument(
        "--prompt-chars",
        type=str,
        default="1500,14000,28000",
        help="Rozmiary promptów w znakach po przecinku (domyślnie: krótki ~400t, średni ADK ~4000t, duży ADK ~8000t).",
    )
    parser.add_argument("--tiers", type=str, default="SML,LRM", help="Tiery do przetestowania (domyślnie: SML,LRM).")
    parser.add_argument("--repeats", type=int, default=1, help="Liczba powtórzeń każdego rozmiaru promptu.")
    parser.add_argument("--skip-switch", action="store_true", help="Pomiń test przełączania SML <-> LRM na końcu.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout pojedynczego zapytania w sekundach.")
    args = parser.parse_args()

    conn = LLMConnectionManager(provider="ollama")
    generate_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    base_url = generate_url.split("/api/")[0].rstrip("/")
    env_num_ctx = int(os.environ.get("OLLAMA_NUM_CTX", "32768"))
    env_num_predict = int(os.environ.get("OLLAMA_NUM_PREDICT", "8192"))

    ollama_status = conn.check_llm_access()["ollama"]
    reachable, installed, err = ollama_status["reachable"], ollama_status["installed_models"], ollama_status["error"]
    if not reachable:
        print(f"[BŁĄD] Serwer Ollama pod {base_url} nie odpowiada: {err}", file=sys.stderr)
        return 1

    tiers = [t.strip().upper() for t in args.tiers.split(",") if t.strip()]
    sizes = [int(x.strip()) for x in args.prompt_chars.split(",") if x.strip()]
    tier_models = {tier: conn.resolve_model_name("ollama", tier) for tier in tiers}

    print("=" * 112)
    print("BENCHMARK OLLAMA (konfiguracja ADK)")
    print(f"  Endpoint        : {generate_url}")
    print(f"  OLLAMA_NUM_CTX  : {env_num_ctx} (w ADK num_predict={env_num_predict}; w teście generacji num_predict={args.gen_tokens})")
    for tier, model in tier_models.items():
        gpu_cfg = os.environ.get(f"HARNESS_OLLAMA_{tier}_NUM_GPU", "(domyślne Ollama)")
        present = "OK" if any(m == model or m.startswith(model.split(":")[0]) for m in installed) else "BRAK W /api/tags!"
        print(f"  Tier {tier:<10} : {model:<24} | NUM_GPU={gpu_cfg} | status={present}")
    print("=" * 112, flush=True)

    results: list[dict[str, Any]] = []

    for tier in tiers:
        model = tier_models[tier]
        print(f"\n>>> [{tier}] Model: {model}", flush=True)

        # 1. Rozgrzewka + pomiar załadowania modelu do pamięci
        w_sys, w_usr = _build_prompt(target_chars=300, gen_tokens=32)
        warmup = _call_generate(generate_url, model, tier, w_sys, w_usr, env_num_ctx, 32, args.timeout)
        ps_info = _format_ps_entry(_ollama_ps(base_url), model)
        print(f"  [Stan /api/ps] {ps_info}", flush=True)
        _print_row("warmup / load", warmup)
        results.append({"case": "warmup", "chars": 300, **warmup, "ps": ps_info})

        # 2. Pomiary prefill + generacja dla kolejnych rozmiarów kontekstu
        for chars in sizes:
            for rep in range(1, args.repeats + 1):
                sys_p, usr_p = _build_prompt(target_chars=chars, gen_tokens=args.gen_tokens)
                label = f"chars={chars}" if args.repeats == 1 else f"chars={chars} #{rep}"
                row = _call_generate(
                    generate_url, model, tier, sys_p, usr_p, env_num_ctx, args.gen_tokens, args.timeout
                )
                _print_row(label, row)
                results.append({"case": label, "chars": chars, **row, "ps": ps_info})

    # 3. Koszt przełączenia między modelami (czy oba mieszczą się jednocześnie w pamięci)
    switch_rows: list[dict[str, Any]] = []
    if not args.skip_switch and len(tiers) >= 2:
        t_a, t_b = tiers[0], tiers[1]
        print(f"\n>>> [PRZEŁĄCZANIE MODELI] {tier_models[t_b]} -> {tier_models[t_a]} -> {tier_models[t_b]}", flush=True)
        for step_tier in (t_a, t_b):
            m_name = tier_models[step_tier]
            s_sys, s_usr = _build_prompt(target_chars=600, gen_tokens=48)
            sw = _call_generate(generate_url, m_name, step_tier, s_sys, s_usr, env_num_ctx, 48, args.timeout)
            ps_after = _format_ps_entry(_ollama_ps(base_url), m_name)
            _print_row(f"switch->{step_tier}", sw)
            switch_rows.append({"step": f"switch->{step_tier}", "ps": ps_after, **sw})

    # 4. Zbiorcza tabela wyników
    print("\n" + "=" * 112)
    print("PODSUMOWANIE (PREFILL + GENERACJA)")
    print("-" * 112)
    header = (
        f"{'Tier':<5} | {'Model':<22} | {'Przypadek':<15} | {'Load [s]':>8} | "
        f"{'In [tok]':>8} | {'Prefill [s]':>11} | {'Prefill [t/s]':>13} | "
        f"{'Out [tok]':>9} | {'Gen [s]':>8} | {'Gen [t/s]':>9} | {'Wall [s]':>8}"
    )
    print(header)
    print("-" * 112)
    for r in [*results, *({"case": s["step"], **s} for s in switch_rows)]:
        print(
            f"{r['tier']:<5} | {r['model']:<22} | {r['case']:<15} | {r['load_s']:8.2f} | "
            f"{r['prompt_tok']:8d} | {r['prefill_s']:11.2f} | {r['prefill_tps']:13.1f} | "
            f"{r['gen_tok']:9d} | {r['gen_s']:8.2f} | {r['gen_tps']:9.1f} | {r['wall_s']:8.2f}"
        )
    print("=" * 112)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
