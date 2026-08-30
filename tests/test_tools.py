from pathlib import Path
from adk.core.models import Citation, ThesisMetadata, ChapterDraft
from adk.tools.benchmarks import BenchmarkTool
from adk.tools.filesystem import FileSystemTool
from adk.tools.literature import LiteratureTool
from adk.tools.sandbox import SandboxRunnerTool
from adk.tools.typesetting import TypesettingTool


def test_filesystem_tool(tmp_path):
    fs = FileSystemTool(tmp_path)
    res_write = fs.execute(action="write", path="sub/test.txt", content="Hello ADK")
    assert res_write.success is True

    res_read = fs.execute(action="read", path="sub/test.txt")
    assert res_read.success is True
    assert res_read.output == "Hello ADK"

    res_exists = fs.execute(action="exists", path="sub/test.txt")
    assert res_exists.output is True


def test_sandbox_runner_python_execution(tmp_path):
    sandbox = SandboxRunnerTool(tmp_path)
    res = sandbox.run_python_code("print('SANDBOX_OK')")
    assert res.passed is True
    assert "SANDBOX_OK" in res.stdout


def test_literature_tool_citations():
    lit = LiteratureTool()
    c = Citation(
        key="Wu2023AutoGen",
        title="AutoGen",
        authors=["Qingyun Wu", "Gagan Bansal"],
        year=2023,
        venue="Microsoft Research",
        bibtex="@article{Wu2023AutoGen,\n  title={AutoGen}\n}",
    )
    bib = lit.format_bibtex_entry(c)
    assert "@article{Wu2023AutoGen," in bib

    val = lit.validate_citations("W pracy @Wu2023AutoGen oraz @Unknown2025", [c])
    assert val["used_count"] == 2
    assert "Unknown2025" in val["missing_keys"]


def test_benchmark_tool_chart_generation(tmp_path):
    bench = BenchmarkTool(tmp_path)
    res = bench.record_benchmark(
        scenario_name="Test Scenario",
        description="Pomiary testowe",
        metrics_data=[{"name": "Throughput", "value": 1500.0, "unit": "req/s"}],
        chart_labels=["A", "B", "C"],
        chart_values=[10.0, 20.0, 30.0],
        chart_ylabel="Jednostka",
    )
    assert res.scenario_name == "Test Scenario"
    assert Path(res.chart_image_path).exists()


def test_typesetting_tool_export(tmp_path):
    typesetter = TypesettingTool(tmp_path)
    meta = ThesisMetadata(title="Test Thesis")
    chapters = [ChapterDraft(number=1, title="Wstęp", content_typst="Treść wstępu", summary="Wstęp")]
    citations = [Citation(key="TestKey2024", title="Test", authors=["Author"], year=2024, bibtex="@misc{TestKey2024, title={Test}}")]

    res = typesetter.export_thesis_package(meta, chapters, citations)
    assert Path(res["typst_file"]).exists()
    assert Path(res["latex_file"]).exists()
    assert Path(res["bib_file"]).exists()
