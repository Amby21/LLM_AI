import ollama
import streamlit as st

st.title("Jarvis the AI friend")

if "memory" not in st.session_state:
    st.session_state.memory = []

user_input = st.text_input("You:")

if user_input:
    st.session_state.memory.append({"role": "user","content": user_input})

    response = ollama.chat(model="llama3",messages=[{"role":"system","content": "You are a friendly robot named Jarvis"},
                                                    *st.session_state.memory] )
    
    answer = response["message"]["content"]
    st.session_state.memory.append({"role": "system","content": answer })

for msg in st.session_state.memory:
    if msg["role"] == "user":
        st.write("You:", msg["content"])
    else:
        st.write("Jarvis:",msg["content"])
