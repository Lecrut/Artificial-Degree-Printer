from adk.tools.literature_search import DynamicLiteratureSearchEngine


def test_dynamic_literature_search_discovers_papers_by_topic():
    engine = DynamicLiteratureSearchEngine()
    topic = "System detekcji anomalii w sieciach 5G z wykorzystaniem uczenia maszynowego"
    
    papers = engine.discover_papers_for_topic(topic, count=3)
    assert len(papers) == 3
    for p in papers:
        assert p.year >= 2023
        assert p.citations_count >= 100
        assert "5g" in p.title.lower() or "anomal" in p.title.lower() or "system" in p.title.lower() or len(p.actionable_implementation_items) > 0

    citations = engine.papers_to_citations(papers)
    assert len(citations) == 3
    for c in citations:
        assert c.year >= 2023
        assert "@article" in c.bibtex

