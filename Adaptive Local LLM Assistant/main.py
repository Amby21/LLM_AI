import re
import requests
import streamlit as st
from ingest import create_index
from sentence_transformers import SentenceTransformer
import numpy as np

# Dummy data (replace later)
texts = ["This is a sample document about AI.", "LLMs are powerful."]
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
index, stored_texts = create_index(texts)


def select_tool(query):
    if re.search(r'\d+[\+\-\*/]\d+', query):
        return "calculator"
    elif "summarize" in query.lower():
        return "summarizer"
    return "rag"

def select_model(query):
    if len(query.split()) < 15:
        return "mistral"
    return "llama3"

def calculator_tool(query):
    try: 
        return str(eval(query))
    except:
        return "invalid math expression"

def summarize_text(text):
    prompt = f"Summarize this:\n{text}"

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt}
    )

    return res.json().get("response", "")

def retrieve(query, model, index, texts, k=3):
    q_emb = model.encode([query])
    q_emb = np.array(q_emb)

    D, I = index.search(q_emb, k)
    return [texts[i] for i in I[0]]

# Windowing
MAX_TOKENS = 5000
def window_context(chunks):
    joined = " ".join(chunks)
    return joined[:MAX_TOKENS]

def compress_context(context):
    if len(context) > 500:
        return summarize_text(context)
    return context

def generate_answer(query, context):
    model = select_model(query)

    prompt = f"""Answer ONLY using context.Context: {context}Question: {query}"""

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "options": {"temperature": 0.2}
        }
    )

    return res.json().get("response", "")

def evaluate(answer,context):
    grounded = any(sent.strip() in context for sent in answer.split('.'))
    length = len(answer.split())
    return {
        "grounded": grounded,
        "length": length
    }

def handle_query(query,index,texts,embed_model):

    tool = select_tool(query)
    
    if tool == "calculator":
        return calculator_tool(query)
    
    elif tool == "summarizer":
        return summarize_text(query)
    
    else:
        chunks = retrieve(query,embed_model,index,texts)
        context = window_context(chunks)
        context = compress_context(context)
        answer = generate_answer(query, context)
        eval_metrics = evaluate(answer,context)

        return {"answer": answer, "evaluation": eval_metrics}
    
st.title(" Adaptive LLM Assistant")
query = st.text_input("Ask something")

if query:
    result = handle_query(query,index,texts,embed_model)
    if isinstance(result,dict):
        st.write("### Answer")
        st.write(result["answer"])
        st.write("### Evaluation")
        st.json(result["evaluation"])
    else:
        st.write(result)
