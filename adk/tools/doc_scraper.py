from __future__ import annotations

import re
import urllib.request
from typing import Any, Optional
from adk.tools.base import BaseTool, ToolResult


class WebDocumentationScraperTool(BaseTool):
    """
    Live Web Documentation Scraper Tool:
    Fetches latest documentation snippets and API specs directly from official web pages
    (e.g., Next.js, Typst, FastAPI, React 19, Rust docs) to prevent hallucination of deprecated APIs.
    """
    name = "doc_scraper"
    description = "Pobieranie najnowszej dokumentacji technicznej i specyfikacji API bezpośrednio ze stron internetowych"

    def __init__(self, timeout_sec: int = 10) -> None:
        self.timeout_sec = timeout_sec

    def fetch_url_markdown(self, url: str) -> str:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ADKDocScraper/2027"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                html = response.read().decode("utf-8", errors="ignore")
                
            # Prosty parser HTML do czystego tekstu/markdowna
            text = re.sub(r"<script.*?>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style.*?>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<h[1-6].*?>(.*?)</h[1-6]>", r"\n# \1\n", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<p.*?>(.*?)</p>", r"\1\n", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<code.*?>(.*?)</code>", r"`\1`", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<.*?>", "", text)
            
            # Wyszczyść wielokrotne znaki nowej linii
            clean_lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(clean_lines[:150])  # Zwróć pierwsze 150 najistotniejszych linii
        except Exception as e:
            return f"Nie udało się pobrać dokumentacji z {url}: {str(e)}"

    def execute(self, url: str, **kwargs: Any) -> ToolResult:
        if not url:
            return ToolResult(success=False, error="Wymagany parametr URL do pobrania dokumentacji.")
        content = self.fetch_url_markdown(url)
        return ToolResult(
            success=not content.startswith("Nie udało się"),
            output=content,
            metadata={"url": url},
        )

