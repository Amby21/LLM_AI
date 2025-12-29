from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import ollama

#Load embedding model(turns words into numbers)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

#Read knowledge
with open("knowledge.txt") as f:
    text = f.read()

#Cut into small pieces
chunks = text.split("/n")

#Turn chunks into vectors
vectors = embedder.encode(chunks)
vectors = np.array(vectors)

#Store in FAISS(smart memory)
index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)

def search_knowledge(question):
    q_vector = embedder.encode([question])
    _, idx = index.search(np.array(q_vector), 3)
    return [chunks[i] for i in idx[0]]

print(" Jarvis with Knowledge is ready! Type bye to stop.\n")

memory = []
print(type(memory))
while True:
    question = input("You:")

    if question.lower == "bye":
        break

    #Find helpful knowledge
    facts = search_knowledge(question)
    context = "/n".join(facts)

    memory.append = ({"role":"user","content":question})

    response = ollama.chat(
        model = "llama3",
        messages=[
            {
            "role":"system",
            "content": "You are Jarvis. Use ONLY the facts below to answer."
        },
        {
            "role":"system",
            "content":f"Facts:\n{context}"
        },
        *memory

        ]
    )

    answer = response["message"]["content"]
    memory.append({"role":"assistant","content":answer})

    print("Jarvis:",answer)
