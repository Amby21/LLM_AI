import json
import os
import ollama
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

chat_friend = "JARVIS"
embedder = SentenceTransformer("all-MiniLm-L6-v2")
with open("knowledge.txt") as f:
    text = f.read()

chunks = text.split("/n")

vectors = embedder.encode(chunks)
vectors = np.array(vectors)

index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)

def search_knowledge(question):
    q_vec = embedder.encode([question])
    _,idx = index.search(np.array(q_vec),3)
    return [chunks[i] for i in idx[0]]


MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE,"r") as f:
            return json.load(f)
        return []

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory,f,indent=2)


memory = load_memory()

print(f"{chat_friend} is ready!. Type bye to stop!")

while True:

    question = input("You:")

    if question.lower() == "bye":
        break

    facts = search_knowledge(question)
    context = "\n".join(facts)

    memory.append({"role:":"user","content":question})

    response = ollama.chat(model="llama3",messages=[{"role":"system","content":("You are Jarvis, a kind teacher." "Explain step by step" "Only use provided facts")},
                                                    {"role":"system","content":f"Facts:\n{context}"}, *memory])
    answer = response["memory"]["content"]

    memory.append({"role":"assistant","content": answer})

    save_memory(memory)
