from documents import DOCUMENTS
chunk_size = 100
overlap = 20
i = 0


def chunk_all_docs(documents: list,chunk_size: int = 100, overlap: int =  20) -> list:
    all_chunks = []
    for doc in DOCUMENTS:
        print(f"{doc['id']}")
        while i < chunk_size:
            words_list_doc = doc['content'].split()
            chunk_text = " ".join(words_list_doc[i:i+chunk_size])
            all_chunks.append({"doc_id": f"{doc['id']}_chunk_len({all_chunks})",
                            "doc_id": doc['id'],
                            "doc_title": doc['title'],
                            "text": chunk_text
                            })
            
            i = i+chunk_size - overlap

        print(f"  {doc['title']}: "
                f"{len([c for c in all_chunks if c['doc_id'] == doc['id']])} chunks")

    return all_chunks
