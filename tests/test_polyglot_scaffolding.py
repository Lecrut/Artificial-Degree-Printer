from __future__ import annotations

import pytest
from adk.agents.developer import DeveloperAgent, DynamicLanguageResolver
from adk.core.state import ADKProjectState
from adk.verification.code_gate import CodeVerificationGate
from adk.verification.cross_validator import CrossConsistencyValidator


def test_dynamic_language_resolver_profiles():
    # 1. Zig
    s_zig = ADKProjectState(request="Wydajny system przetwarzania w języku Zig")
    p_zig = DynamicLanguageResolver.resolve_profile(s_zig)
    assert p_zig.language == "Zig"
    assert p_zig.build_file_name == "build.zig"
    assert "zig test" in p_zig.test_framework

    # 2. Elixir
    s_ex = ADKProjectState(request="Rozproszony system współbieżny w Elixirze (Phoenix)")
    p_ex = DynamicLanguageResolver.resolve_profile(s_ex)
    assert p_ex.language == "Elixir"
    assert p_ex.build_file_name == "mix.exs"

    # 3. Haskell
    s_hs = ADKProjectState(request="Silnik weryfikacji finansowej w Haskellu")
    p_hs = DynamicLanguageResolver.resolve_profile(s_hs)
    assert p_hs.language == "Haskell"
    assert p_hs.build_file_name == "stack.yaml"

    # 4. Scala
    s_scala = ADKProjectState(request="System analityczny w Scala / Akka")
    p_scala = DynamicLanguageResolver.resolve_profile(s_scala)
    assert p_scala.language == "Scala"
    assert p_scala.build_file_name == "build.sbt"

    # 5. Julia
    s_jl = ADKProjectState(request="Obliczenia macierzowe w języku Julia")
    p_jl = DynamicLanguageResolver.resolve_profile(s_jl)
    assert p_jl.language == "Julia"
    assert p_jl.build_file_name == "Project.toml"

    # 6. Kotlin
    s_kt = ADKProjectState(request="Aplikacja serwerowa w języku Kotlin")
    p_kt = DynamicLanguageResolver.resolve_profile(s_kt)
    assert p_kt.language == "Kotlin"
    assert p_kt.build_file_name == "build.gradle.kts"

    # 7. Swift
    s_swift = ADKProjectState(request="Aplikacja backendowa w technologii Swift / Vapor")
    p_swift = DynamicLanguageResolver.resolve_profile(s_swift)
    assert p_swift.language == "Swift"
    assert p_swift.build_file_name == "Package.swift"

    # 8. Novel / Custom Language fallback (e.g. Mojo)
    s_mojo = ADKProjectState(request="Silnik uczenia maszynowego w języku Mojo")
    p_mojo = DynamicLanguageResolver.resolve_profile(s_mojo)
    assert p_mojo.language == "Mojo"
    assert "mojo" in p_mojo.build_file_name.lower()


@pytest.mark.parametrize("request_text,expected_files,expected_lang", [
    ("System mikrousług w języku Go", ["go.mod", "src/service.go", "tests/service_test.go", "Dockerfile"], "Go"),
    ("Silnik kryptograficzny w języku Rust", ["Cargo.toml", "src/lib.rs", "tests/integration_test.rs", "Dockerfile"], "Rust"),
    ("Platforma backendowa w TypeScript", ["package.json", "src/service.ts", "tests/service.test.ts", "Dockerfile"], "TypeScript"),
    ("Aplikacja mobilna we Flutter / Dart", ["pubspec.yaml", "lib/service.dart", "test/service_test.dart", "Dockerfile"], "Dart"),
    ("Silnik symulacji w C++", ["CMakeLists.txt", "src/service.cpp", "tests/test_service.cpp", "Dockerfile"], "C++"),
    ("System korporacyjny w C# .NET", ["Service.csproj", "src/Service.cs", "tests/ServiceTests.cs", "Dockerfile"], "C#"),
    ("Aplikacja w języku Zig", ["build.zig", "src/service.zig", "tests/service_test.zig", "Dockerfile"], "Zig"),
    ("System rozproszony w Elixirze", ["mix.exs", "lib/core_service.ex", "test/core_service_test.exs", "Dockerfile"], "Elixir"),
    ("Aplikacja w Haskellu", ["stack.yaml", "src/CoreService.hs", "test/Spec.hs", "Dockerfile"], "Haskell"),
    ("Projekt w języku Scala", ["build.sbt", "src/main/scala/CoreService.scala", "src/test/scala/CoreServiceTest.scala", "Dockerfile"], "Scala"),
    ("Obliczenia numeryczne w języku Julia", ["Project.toml", "src/CoreService.jl", "test/runtests.jl", "Dockerfile"], "Julia"),
    ("Platforma w języku Kotlin", ["build.gradle.kts", "src/main/kotlin/Service.kt", "src/test/kotlin/ServiceTest.kt", "Dockerfile"], "Kotlin"),
    ("Aplikacja w języku Swift", ["Package.swift", "Sources/Service.swift", "Tests/ServiceTests.swift", "Dockerfile"], "Swift"),
    ("Platforma uczenia maszynowego w Python", ["pyproject.toml", "src/core/service.py", "tests/test_service.py", "Dockerfile"], "Python"),
    ("Silnik w języku Mojo", ["mojo.config", "src/service.mojo", "tests/service_test.mojo", "Dockerfile"], "Mojo"),
])
def test_developer_scaffolds_open_ended_polyglot(request_text, expected_files, expected_lang):
    state = ADKProjectState(request=request_text)
    agent = DeveloperAgent()
    updated_state = agent.run(state)

    artifact_paths = [a.path for a in updated_state.code_artifacts]
    for expected_file in expected_files:
        assert expected_file in artifact_paths, f"Expected {expected_file} in {artifact_paths}"

    # Verify test artifact exists
    test_artifacts = [a for a in updated_state.code_artifacts if a.is_test]
    assert len(test_artifacts) >= 1

    # Verify Chapter 4 is generated and references the code files
    chap4 = next((c for c in updated_state.chapters if c.number == 4), None)
    assert chap4 is not None
    assert expected_lang in chap4.content_typst
    assert len(chap4.code_snippets_referenced) >= 2

    # Verify CodeVerificationGate passes (structural & brace checks)
    code_gate = CodeVerificationGate()
    issues = code_gate.verify_artifacts(updated_state.code_artifacts)
    assert len(issues) == 0, f"Unexpected code issues: {issues}"

    # Verify Universal CrossConsistencyValidator extracts symbols across any language
    cross_val = CrossConsistencyValidator()
    symbols = cross_val.extract_code_symbols(updated_state.code_artifacts)
    assert len(symbols) >= 1
