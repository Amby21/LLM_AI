import ollama
import logging
import time
from enum import Enum
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s | %(levelname)s | %(message)s"
)

#Embedding model definition
EMBEDDING_MODEL = SentenceTransformer("all-MiniTM-L6-v2")

CHEAP_MODEL = "mistral"
STRONG_MODEL = "llama3"

#Knowledge Base (RAG)
DOCUMENTS =["RAG stands for Retrieval-Augmented Generation.",
    "Model switching reduces cost by using cheaper models when possible.",
    "State machines help control AI behavior.",
    "Multi-agent systems separate concerns."]

DOC_EMBEDDINGS = EMBEDDING_MODEL.encode(DOCUMENTS,normalize_embeddings=True)

# Retrieval Tool (Similarity Threshold)

SIM_THRESHOLD = 0.6

def retrieve_context(query: str, top_k = 2):
    query_emb = EMBEDDING_MODEL.encode([query],normalize_embeddings=True)
    sims = cosine_similarity(query_emb, DOC_EMBEDDINGS)[0]

    ranked = sorted(
        zip(DOCUMENTS,sims),key=lambda x:x[1],reverse=True
    )

    return [ doc for doc,score in ranked 
            if score >= SIM_THRESHOLD
            ][:top_k]

#Memory & Profile Management

class MemoryManager:
    def __init__(self,window_size = 5):
        self.messages = []
        self.window_size = window_size
        self.summary = ""

    def summarize(self):
        text = " ".join(m[1] for m in self.messages)
        self.summary = ollama.chat(
            model = CHEAP_MODEL,
            messages=[{"role":"user", "content": f"Summarize the conversation {text}"}]
        )["message"]["content"]
        self.messages = []

    def context(self):
        return self.summary + " " + " ".join(m[1] for m in self.messages)
    
class State(Enum):
    PLAN = 1
    RETRIEVE = 2
    ANSWER = 3
    CRITIQUE = 4
    DONE = 5


class Agent:
    def __init__(self,name,model):
        self.name = name
        self.model = model
    
    def run(self, prompt):
        logging.info(f"{self.name} using {self.model}")
        response = ollama.chat(
            model = self.model,
            messages=[{"role":"user","content": prompt}]
        )
        return response["message"]["content"]
    
class PlannerAgent(Agent):
    def plan(self,query):
        return self.run(f"Decide if retrieval is needed for: {query}. Answer yes or no.")
    
class AnswerAgent(Agent):
    def answer(self,query, context):
        model = CHEAP_MODEL if context else STRONG_MODEL
        self.model = model
        prompt = f""" Answer using ONLY the context below. If no context, say 'I Don't know'. Context: {context} Question: {query}"""
        return self.run(prompt)
    
class CriticAgent(Agent):
    def critique(self, answer):
        return self.run(f"Is this answer factual and frounded? {answer}")
    
class Orchestrator:
    def __init__(self):
        self.state = State.PLAN
        self.memory = MemoryManager()
        self.planner = PlannerAgent("Planner", STRONG_MODEL)
        self.answerer = AnswerAgent("Answerer",CHEAP_MODEL)
        self.critic = CriticAgent("Critic",CHEAP_MODEL)

        def run(self, query):
            retries = 0
            context = []

            while self.state != State.DONE:
                try:
                    if self.state == State.PLAN:
                        decision = self.planner.plan(query)
                        self.state = State.RETRIEVE if "yes" in decision.lower() else State.ANSWER

                    elif self.state == State.RETRIEVE:
                        context = retrieve_context(query)
                        self.state == State.ANSWER
                    
                    elif self.state == State.ANSWER:
                        answer = self.answerer.answer(query,context)
                        self.state = State.CRITIQUE
                    
                    elif self.state == State.CRITIQUE:
                        verdict = self.critic.critique(answer)
                        if "yes" in verdict.lower():
                            self.memory.add("user", query)
                            self.memory.add("assistant",answer)
                            self.state = State.DONE
                            return answer
                        else:
                            retries += 1
                            if retries > 1:
                                return "I am not confident enought to answer."
                            self.state = State.ANSWER

                except Exception as e:
                    logging.error(e)
                    return "System failure."
                


if __name__ == "__main__":
    system = Orchestrator()

    while True:
        q = input("\nUser:")
        if q.lower() in ["exit","quit"]:
            break
        response = system.run(q)
        print("AI:" response)