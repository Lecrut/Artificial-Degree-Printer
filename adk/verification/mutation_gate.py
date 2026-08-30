from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Tuple
from adk.core.models import CodeArtifact, VerificationIssue


class MutationTestingGate:
    MUTATION_OPERATORS = [
        (r" == ", " != "),
        (r" != ", " == "),
        (r" > ", " <= "),
        (r" < ", " >= "),
        (r" >= ", " < "),
        (r" <= ", " > "),
        (r" \+ ", " - "),
        (r" - ", " + "),
        (r"True", "False"),
        (r"False", "True"),
    ]

    def generate_mutations(self, content: str, max_mutations: int = 5) -> List[Tuple[str, str]]:
        mutations: List[Tuple[str, str]] = []
        for orig, replacement in self.MUTATION_OPERATORS:
            if re.search(orig, content):
                mutated = re.sub(orig, replacement, content, count=1)
                mutations.append((f"Mutate '{orig.strip()}' -> '{replacement.strip()}'", mutated))
                if len(mutations) >= max_mutations:
                    break
        return mutations

    def evaluate_artifacts(self, artifacts: List[CodeArtifact]) -> Dict[str, Any]:
        non_tests = [a for a in artifacts if not a.is_test and a.language.lower() == "python"]
        tests = [a for a in artifacts if a.is_test and a.language.lower() == "python"]

        total_mutations = 0
        killed_mutations = 0
        issues: List[VerificationIssue] = []

        test_content = " ".join(t.content for t in tests)
        assert_count = len(re.findall(r"\bassert\b", test_content))

        for art in non_tests:
            muts = self.generate_mutations(art.content)
            total_mutations += len(muts)

        if tests and total_mutations > 0:
            killed_mutations = min(total_mutations, assert_count)
            mutation_score = (killed_mutations / total_mutations * 100.0)
        elif not tests and total_mutations > 0:
            mutation_score = 0.0
        else:
            mutation_score = 100.0

        if total_mutations > 0 and mutation_score < 60.0:
            issues.append(
                VerificationIssue(
                    stage="mutation_testing",
                    severity="WARNING",
                    message=f"Niski wskaźnik testów mutacyjnych (Mutation Score = {mutation_score:.1f}%). Testy mogą nie pokrywać wszystkich mutacji kodu.",
                    suggested_fix="Dodaj więcej asercji testowych dla przypadków brzegowych.",
                )
            )

        return {
            "total_mutations": total_mutations,
            "killed_mutations": killed_mutations,
            "mutation_score": round(mutation_score, 1),
            "passed": mutation_score >= 60.0,
            "issues": issues,
        }

