from adk.tools.doc_scraper import WebDocumentationScraperTool
from adk.tools.env_tool import EnvSecretsManagerTool


def test_env_secrets_manager_tool(tmp_path):
    tool = EnvSecretsManagerTool(tmp_path)
    res = tool.execute(
        action="setup_env",
        required_keys=[
            {"key": "DB_PASS", "description": "Hasło bazy", "default": "CHANGE_ME"},
            {"key": "SECRET_KEY", "description": "Klucz secret", "default": "YOUR_SECRET"},
        ],
    )
    assert res.success is True
    assert (tmp_path / ".env.example").exists() is True
    assert (tmp_path / ".env").exists() is True


def test_web_documentation_scraper_tool():
    tool = WebDocumentationScraperTool()
    # Test pobierania przykładowej dokumentacji
    res = tool.execute(url="https://example.com")
    assert res.success is True
    assert len(res.output) > 0

