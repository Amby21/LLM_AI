import anthropic
from documents import DOCUMENTS
from chunker import chunk_all_docs
from embedding import setup, search
from dotenv import load_dotenv, find_dotenv
import os

chunks = chunk_all_docs(DOCUMENTS)
setup(chunks)

load_dotenv(find_dotenv() or os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

def ask(question: str, threshold: float = 0.5, n_results: int = 3)-> dict:
    print(f"\n{'='*50}")
    print(f"QUESTION: {question}")

    results = search(question,n_results,threshold = 0.5)

    if not results:
        context = "No relevant documents found"

    else:
        parts = []
        
        for i, r in enumerate(results):
            parts.append(
                f"[Source {i+1}: {r['doc_title']} "
                f"({r['similarity']:.0%})]\n{r['text']}"
            )
        context = "\n\n".join(parts)
