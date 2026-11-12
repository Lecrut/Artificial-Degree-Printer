"""Promotor gates (HITL), evolution history and the stop banner."""

from __future__ import annotations


from typing import Any, Callable

from adk.core.models import read_json_state, write_json_state


class GatesMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _record_evolution_event(self, event: dict[str, Any]) -> None:
        history = (
            read_json_state(self.evolution_history_path)
            if self.evolution_history_path.exists()
            else {"events": []}
        )
        history.setdefault("events", []).append(event)
        write_json_state(self.evolution_history_path, history)

    def _update_hitl_gate(
        self,
        gate_name: str,
        active: bool = False,
        question: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update state/hitl_flag.json with current promotor checkpoint gate status."""
        existing = read_json_state(self.hitl_flag_path) if self.hitl_flag_path.exists() else {}
        approved_gates: list[str] = list(existing.get("approved_gates", []))
        if not active and gate_name not in approved_gates:
            approved_gates.append(gate_name)
        hitl_state = {
            "active": active,
            "current_gate": gate_name,
            "approved_gates": approved_gates,
            "question": question,
            "context": context or {},
        }
        write_json_state(self.hitl_flag_path, hitl_state)
        return hitl_state

    def _check_hitl_gate(
        self,
        gate_name: str,
        context_payload: dict[str, Any],
        interactive_gates: bool | None = None,
        gate_approval_callback: Callable[[str, dict[str, Any]], bool] | None = None,
    ) -> bool:
        """Evaluate a Promotor HITL checkpoint gate automatically, via callback, or via interactive CLI input."""
        use_interactive = self.interactive_gates if interactive_gates is None else interactive_gates
        callback = gate_approval_callback if gate_approval_callback is not None else self.gate_approval_callback

        if not use_interactive and callback is None:
            self._update_hitl_gate(
                gate_name=gate_name,
                active=False,
                question=None,
                context=context_payload,
            )
            return True

        if callback is not None:
            approved = bool(callback(gate_name, context_payload))
        else:
            ans = input(f"Promotorze, czy zatwierdzasz bramkę {gate_name} [T/n]? ").strip().lower()
            approved = ans in ("", "t", "tak", "y", "yes")

        if approved:
            self._update_hitl_gate(
                gate_name=gate_name,
                active=False,
                question=None,
                context=context_payload,
            )
            return True

        question = f"Wymagana akceptacja promotora na bramce {gate_name}."
        self._update_hitl_gate(
            gate_name=gate_name,
            active=True,
            question=question,
            context=context_payload,
        )
        self._record_evolution_event({"type": "HITL_TRIGGERED", "gate": gate_name, "question": question})
        return False

    def _shout_problem_stop(self, reason: str) -> None:
        """Console and process log. A stop because of a problem must be impossible to miss."""
        banner = "\n".join(
            [
                "",
                "PPPP   RRRR   ZZZZZ  EEEEE  RRRR   Y   Y  W   W   AAA   M   M",
                "P   P  R   R     Z   E      R   R   Y Y   W   W  A   A  MM MM",
                "PPPP   RRRR     Z    EEEE   RRRR     Y    W W W  AAAAA  M M M",
                "P      R  R    Z     E      R  R     Y    WW WW  A   A  M   M",
                "P      R   R  ZZZZZ  EEEEE  R   R    Y    W   W  A   A  M   M",
                "",
                "BBBB    OOO        JJJ  EEEEE  SSSSS  TTTTT",
                "B   B  O   O         J  E      S        T",
                "BBBB   O   O         J  EEEE   SSSSS    T",
                "B   B  O   O     J   J  E          S    T",
                "BBBB    OOO       JJJ   EEEEE  SSSSS    T",
                "",
                "PPPP   RRRR    OOO   BBBBB  L      EEEEE  M   M",
                "P   P  R   R  O   O  B   B  L      E      MM MM",
                "PPPP   RRRR   O   O  BBBBB  L      EEEE   M M M",
                "P      R  R   O   O  B   B  L      E      M   M",
                "P      R   R   OOO   BBBBB  LLLLL  EEEEE  M   M",
                "",
                reason,
                "",
            ]
        )
        print(banner, flush=True)
        self.logger.log_step("PRZERWANIE", banner, {"reason": reason})
