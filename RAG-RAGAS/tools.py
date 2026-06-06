from langchain_core.tools import tool
from embedding import search
from graph_db import search_graph

@tool
def search_policies(query: str) -> str:
    """Search governance policy documents. Use for: GDPR, PII, retention, access control. Input: Policy question."""
    results = search(query, n_results=3, threshold=0.5)
    if not results:
        return "No relevant policies found"
    
    parts = []
    for r in results:
        parts.append(
            f"[{r['doc_title']} - {r['similarity']:.0%}]\n"
            f"{r['text']}"

        )
        return "\n\n".join(parts)

@tool
def search_terms(query: str) -> str:
    """
    Search insurance business terms and definitions.
    Use for: Loss Ratio, Premium, Claim Amount,
    business term definitions, data domains.
    Input: term or concept name.
    """
    return search_graph(query)


tools = [search_policies, search_terms]
