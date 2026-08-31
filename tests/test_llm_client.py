from adk.llm.client import (
    FallbackDeterministicProvider,
    GoogleGeminiProvider,
    HeterogeneousRouterLLMClient,
    LLMClient,
    OllamaLocalProvider,
    OpenAICompatibleProvider,
)


def test_fallback_provider():
    client = LLMClient(provider_type="fallback")
    res = client.complete("Napisz specyfikację architektury")
    assert "Syntetyczna odpowiedź" in res


def test_ollama_provider_init():
    client = LLMClient(provider_type="ollama", model_name="qwen2.5-coder:7b")
    assert isinstance(client.provider, OllamaLocalProvider)
    assert client.provider.model_name == "qwen2.5-coder:7b"


def test_gemini_provider_init():
    client = LLMClient(provider_type="gemini", model_name="gemini-2.5-pro")
    assert isinstance(client.provider, GoogleGeminiProvider)


def test_openai_provider_init():
    client = LLMClient(provider_type="openai", model_name="gpt-4o")
    assert isinstance(client.provider, OpenAICompatibleProvider)


def test_heterogeneous_router_client():
    router = HeterogeneousRouterLLMClient()
    dev_provider = router.get_provider_for_agent("developer")
    typesetter_provider = router.get_provider_for_agent("typesetter")

    assert isinstance(dev_provider, OllamaLocalProvider)
    assert isinstance(typesetter_provider, GoogleGeminiProvider)
    assert typesetter_provider.model_name == "gemini-2.5-pro"


def test_topaz_complexity_routing():
    router = HeterogeneousRouterLLMClient()
    
    # Low complexity task
    c1 = router.estimate_task_complexity("Format this file")
    # Coding task
    c2 = router.estimate_task_complexity("Implement a FastAPI class to handle users database")
    # High complexity architectural task
    c3 = router.estimate_task_complexity("Write C4 architecture thesis document and verify cross_consistency")
    
    assert c1 < c2
    assert c2 < c3
    assert c3 >= 0.70
    
    p1 = router.get_provider_for_agent("developer", c1)
    p2 = router.get_provider_for_agent("developer", c2)
    p3 = router.get_provider_for_agent("developer", c3)
    
    assert p1.model_name == "gemini-2.5-flash"
    assert p2.model_name == "qwen2.5-coder:7b"
    assert p3.model_name == "gemini-2.5-pro"

