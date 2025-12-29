import ollama
import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

#FILES
MEMORY_FILE = "memory.json"
PROFILE_FILE = "profile.json"
KNOWLEDGE_FILE = "knowledge.txt"

#MEMORY HELPERS

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except json.JSONDecodeError:
            pass
    return []


def save_memory(memory):
    with open(MEMORY_FILE,"w") as f:
        json.dump(memory,f,indent=2)

def load_profile():
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except json.JSONDecodeError:
            pass
    return {}


def save_profile(profile):
    with open(PROFILE_FILE,"w") as f:
        json.dump(profile,f,indent=2)


#MEMORY FILTER
def is_important(message):
    keywords = ["my name is","i like","i prefer","my favorite","remember"]
    msg = message.lower()
    return any(k in msg for k in keywords)


#RAG SETUP - Knowledge layer
embedder = SentenceTransformer("all-MiniLM-L6-v2")
with open(KNOWLEDGE_FILE, "r") as f:
    documents = [line.strip() for line in f if line.strip()]


doc_vectors = embedder.encode(documents)
doc_vectors = np.array(doc_vectors)

index = faiss.IndexFlatL2(doc_vectors.shape[1])
index.add(doc_vectors)

def search_knowledge(question, k=3):
    q_vec = embedder.encode(question)
    q_vec = np.array(q_vec).reshape(1, -1)
    _, idx = index.search(q_vec, k)
    return [documents[i] for i in idx[0]]


#CHAT LOOP
memory = load_memory()
profile = load_profile()

print(" Jarvis is ready! Type 'bye' to exit \n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower()=="bye":
        print("Jarvis: Bye! I'll remember you")
        break

    #--store important facts--
    if is_important(user_input):
        profile.setdefault('facts',[]).append(user_input)
        save_profile(profile)

    memory.append({"role":"user","content":user_input})

    # RAG context
    facts = search_knowledge(user_input)
    knowledge_context = "\n".join(facts)

    profile_context = "\n".join(profile.get("facts",[]))

    messages = [ 
        {
            "role":"system",
            "content":(
                "You are Jarvis, a friendly personal AI"
                "Be clear,kind and simple."
            )
    },
    {
        "role":"system",
        "content":f"User profile facts:\n{profile_context}"

    },
    {
        "role" : "system",
        "content" : f"Knowledge facts \n{knowledge_context}"

    },
    *memory
    ]
    print("🧠 Thinking...")
    try:
        response = ollama.chat(
            model="llama3",
            messages=messages
        )
    except Exception as e:
        print("❌ LLM error:", e)
        

    answer = response["message"]["content"]
    memory.append({"role":"assistant","content":answer})
    save_memory(memory)
    print(f"Jarvis: {answer}\n")