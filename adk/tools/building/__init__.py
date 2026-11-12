"""Building domain tools (Layer 2): AST node editor, document section editor, literature engine, and hypergraph bridges."""

from adk.tools.building.ast_editor import edit_ast_node
from adk.tools.building.doc_editor import edit_document_section
from adk.tools.building.hypergraph_sync import ensure_node, sync_hypergraph_matrix
from adk.tools.building.import_sync import extract_hyperedge_exports
from adk.tools.building.literature_engine import (
    extract_paper_card_from_abstract,
    fetch_live_or_curated_papers,
    format_bibtex,
    get_domain_bibtex,
    get_domain_papers,
    search_arxiv,
    search_openalex,
)

__all__ = [
    "edit_ast_node",
    "edit_document_section",
    "extract_hyperedge_exports",
    "extract_paper_card_from_abstract",
    "fetch_live_or_curated_papers",
    "format_bibtex",
    "get_domain_bibtex",
    "get_domain_papers",
    "search_arxiv",
    "search_openalex",
    "ensure_node",
    "sync_hypergraph_matrix",
]

