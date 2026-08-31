from adk.tools.git_tool import GitProvenanceTool


def test_git_provenance_tool(tmp_path):
    git_tool = GitProvenanceTool(tmp_path)
    res_init = git_tool.execute(action="init")
    assert res_init.success is True

    # Sprawdź czy .gitignore został utworzony automatycznie
    gitignore_file = tmp_path / ".gitignore"
    assert gitignore_file.exists() is True

    # Utwórz plik testowy
    test_file = tmp_path / "test.txt"
    test_file.write_text("commit content", encoding="utf-8")

    res_commit = git_tool.execute(action="commit", stage="implementation", agent="Software Engineer", message="Add test file")
    assert res_commit.success is True

    # Test brakującego URL przy push
    res_push_no_url = git_tool.execute(action="push")
    assert res_push_no_url.success is False


def test_git_provenance_prompt_callback(tmp_path):
    prompts = []

    def mock_prompt(msg: str) -> str:
        prompts.append(msg)
        if "Imię" in msg:
            return "Test Student"
        return "student@example.com"

    git_tool = GitProvenanceTool(tmp_path / "custom_repo", prompt_callback=mock_prompt)
    res = git_tool.init_repo()
    assert res is True
