from adk.core.models import CodeArtifact
from adk.verification.mutation_gate import MutationTestingGate


def test_mutation_testing_gate_generates_and_evaluates():
    gate = MutationTestingGate()
    code_art = CodeArtifact(
        path="src/calc.py",
        content="def is_positive(x):\n    if x > 0:\n        return True\n    return False\n",
        description="calc",
        is_test=False,
    )
    test_art = CodeArtifact(
        path="tests/test_calc.py",
        content="from src.calc import is_positive\ndef test_calc():\n    assert is_positive(5) is True\n    assert is_positive(-5) is False\n    assert is_positive(0) is False\n",
        description="test",
        is_test=True,
    )

    mutations = gate.generate_mutations(code_art.content)
    assert len(mutations) >= 1

    res = gate.evaluate_artifacts([code_art, test_art])
    assert res["total_mutations"] > 0
    assert res["mutation_score"] >= 60.0
    assert res["passed"] is True

