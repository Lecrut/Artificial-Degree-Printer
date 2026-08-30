from adk.llm import LLMClient


def test_llm_client_fallback_completion():
    client = LLMClient()
    response = client.complete("Zaprojektuj architekturę mikroserwisów", system_prompt="Jesteś architektem.")
    assert "Syntetyczna odpowiedź analityczna" in response

