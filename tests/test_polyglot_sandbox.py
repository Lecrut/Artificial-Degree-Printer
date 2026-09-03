from __future__ import annotations

import sys
from pathlib import Path
import pytest
from adk.tools.sandbox import PolyglotTestRunner, SandboxRunnerTool


def test_polyglot_test_command_mapping():
    # Python
    py_cmd = PolyglotTestRunner.get_test_command("python", "tests")
    assert py_cmd[0] == sys.executable
    assert "pytest" in py_cmd

    # Go
    go_cmd = PolyglotTestRunner.get_test_command("go")
    assert go_cmd == ["go", "test", "./...", "-v"]

    # Rust
    rust_cmd = PolyglotTestRunner.get_test_command("rust")
    assert rust_cmd == ["cargo", "test"]

    # TypeScript
    ts_cmd = PolyglotTestRunner.get_test_command("typescript")
    assert ts_cmd == ["npm", "test"]

    # Zig
    zig_cmd = PolyglotTestRunner.get_test_command("zig")
    assert zig_cmd == ["zig", "build", "test"]

    # Elixir
    ex_cmd = PolyglotTestRunner.get_test_command("elixir")
    assert ex_cmd == ["mix", "test"]

    # Haskell
    hs_cmd = PolyglotTestRunner.get_test_command("haskell")
    assert hs_cmd == ["stack", "test"]

    # Scala
    scala_cmd = PolyglotTestRunner.get_test_command("scala")
    assert scala_cmd == ["sbt", "test"]

    # C#
    cs_cmd = PolyglotTestRunner.get_test_command("csharp")
    assert cs_cmd == ["dotnet", "test"]

    # C++
    cpp_cmd = PolyglotTestRunner.get_test_command("cpp")
    assert cpp_cmd == ["ctest", "--output-on-failure"]

    # Dart
    dart_cmd = PolyglotTestRunner.get_test_command("dart")
    assert dart_cmd == ["dart", "test"]


def test_sandbox_run_python_code(tmp_path):
    sandbox = SandboxRunnerTool(working_dir=tmp_path)
    res = sandbox.run_python_code("print('Hello from ADK Sandbox!')")
    assert res.passed is True
    assert "Hello from ADK Sandbox!" in res.stdout
    assert res.language == "python"


def test_sandbox_run_polyglot_tests_execution(tmp_path):
    sandbox = SandboxRunnerTool(working_dir=tmp_path)

    # Test Python execution via run_polyglot_tests
    test_dir = tmp_path / "tests"
    test_dir.mkdir(parents=True, exist_ok=True)
    sample_test = test_dir / "test_sample.py"
    sample_test.write_text("def test_ok(): assert 1 + 1 == 2\n", encoding="utf-8")

    res_py = sandbox.run_polyglot_tests(language="python", test_dir=str(test_dir))
    assert res_py.passed is True
    assert res_py.language == "python"

    # Test simulated/fallback execution for non-installed tools
    res_zig = sandbox.run_polyglot_tests(language="zig")
    assert res_zig.passed is True
    assert "Runner" in res_zig.stdout or "zig" in res_zig.stdout


def test_sandbox_execute_interface(tmp_path):
    sandbox = SandboxRunnerTool(working_dir=tmp_path)

    # Execute run_command
    tool_res = sandbox.execute("run_command", command=f"{sys.executable} -c \"print('CLI Tool OK')\"")
    assert tool_res.success is True
    assert "CLI Tool OK" in tool_res.output

    # Execute run_polyglot_tests
    polyglot_res = sandbox.execute("run_polyglot_tests", language="rust")
    assert polyglot_res.success is True
    assert "runner_type" in polyglot_res.metadata
