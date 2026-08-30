from adk.tools.git_tool import GitProvenanceTool


def test_git_provenance_tool(tmp_path):
    git_tool = GitProvenanceTool(tmp_path)
    res_init = git_tool.execute(action="init")
    assert res_init.success is True

    # Utwórz plik testowy
    test_file = tmp_path / "test.txt"
    test_file.write_text("commit content", encoding="utf-8")

    res_commit = git_tool.execute(action="commit", stage="implementation", agent="Software Engineer", message="Add test file")
    assert res_commit.success is True

