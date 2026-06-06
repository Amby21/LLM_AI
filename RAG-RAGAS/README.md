# Insurance AI Assistant — RAG System

A production-style RAG (Retrieval Augmented Generation) system
for querying insurance governance policies and business terms.

## What It Does

- Answers natural language questions about governance policies
- Searches insurance business terms and their relationships
- Evaluates answer quality using RAGAS metrics
- Prevents hallucination by grounding answers in documents

## Architecture

User Question
↓
LangGraph Agent
↓
decides
↙       ↘
ChromaDB   Neo4j
(policies) (terms)
↓
LLM
↓
Answer
↓
RAGAS Evaluation
## File Structure
rag_project/
├── documents.py      ← source policy documents
├── chunker.py        ← splits documents into chunks
├── chroma_db.py      ← vector store (setup + search)
├── graph_db.py       ← Neo4j insurance knowledge graph
├── tools.py          ← LangGraph tools (search_policies, search_terms)
├── agent.py          ← LangGraph agent + context collector
└── ragas_eval.py     ← RAGAS quality evaluation

## Setup

### 1. Install dependencies

```bash
pip install chromadb sentence-transformers
pip install langgraph langchain-core langchain-ollama
pip install neo4j ragas datasets
```

### 2. Start Neo4j
Open Neo4j Desktop
→ Start your local database
→ Default: bolt://localhost:7687
### 3. Start Ollama

```bash
ollama pull llama3
ollama serve
```

### 4. Setup Neo4j graph

```bash
python graph_db.py
```

### 5. Run the agent

```bash
python agent.py
```

### 6. Run RAGAS evaluation

```bash
python ragas_eval.py
```

## How Each File Works

### documents.py
Raw policy documents stored as Python dicts.
Source of truth for the RAG system.
Add new documents here to expand knowledge base.

### chunker.py
Splits documents into overlapping chunks.
- chunk_size=100 words — specific enough for precise retrieval
- overlap=20 words — prevents losing context at boundaries

### chroma_db.py
Vector database handling embedding + storage + search.
- setup() — embeds and stores all chunks (runs once)
- search() — finds similar chunks for any query
- threshold=0.5 — filters irrelevant chunks

### graph_db.py
Neo4j knowledge graph of insurance terms and relationships.
Nodes: Term, Domain, Policy
Edges: BELONGS_TO, CALCULATED_FROM, GOVERNS

### tools.py
Two LangGraph tools the agent can choose from:
- search_policies — searches ChromaDB for governance rules
- search_terms — searches Neo4j for business term definitions

### agent.py
LangGraph agent with two nodes:
- agent_node — LLM decides which tool to call
- tool_node — executes the chosen tool
Collects contexts from tool calls for RAGAS evaluation.

### ragas_eval.py
Measures RAG quality across three metrics:
- Faithfulness — is answer grounded in retrieved context?
- Answer Relevancy — does answer address the question?
- Context Precision — are retrieved chunks relevant?

## RAGAS Scores Interpretation
Score > 0.8   ✅  Good
Score 0.6-0.8 ⚠️  Needs improvement
Score < 0.6   ❌  Fix required

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Ollama (llama3) — local inference |
| Agent Framework | LangGraph |
| Vector Database | ChromaDB |
| Embedding Model | all-MiniLM-L6-v2 |
| Graph Database | Neo4j |
| RAG Evaluation | RAGAS |
| API | FastAPI |