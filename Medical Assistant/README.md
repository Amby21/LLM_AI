# 🏥 Medical Diagnosis Assistant
### Graph RAG Powered Clinical Decision Support System
---
## 🎯 Project Overview

An intelligent medical diagnosis assistant that combines 
**Knowledge Graph reasoning** with **Large Language Model explanation** 
to provide differential diagnosis from natural language symptom descriptions.

This is a **Graph RAG (Retrieval Augmented Generation)** system where:
- Knowledge Graph handles structured medical reasoning
- LLM (Claude) provides clinical narrative explanation
- Every diagnosis is traceable to graph data — no hallucination

---

## 🏗️ Architecture
Doctor types symptoms (free text)
↓
Named Entity Extraction
"mild fever" → "fever" node
↓
Knowledge Graph Traversal

Symptom → [INDICATES] → Disease

Disease → [PRECAUTION] → Action
↓
Weighted Coverage Scoring

score = Σ(severity × match) × coverage_ratio
↓
LLM Clinical Explanation (Claude)

Structured data → Clinical narrative
↓
Real-time Streamlit Interface
---

## 📊 Knowledge Graph Stats

| Component | Count |
|-----------|-------|
| Total Nodes | 270 |
| Disease Nodes | 41 |
| Symptom Nodes | 131 |
| Precaution Nodes | 97 |
| INDICATES Edges | 321 |
| PRECAUTION Edges | 162 |
| Total Edges | 483 |

---

## 🔑 Key Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| **Knowledge Graph** | NetworkX DiGraph with typed nodes + edges |
| **Graph RAG** | Graph traversal replaces vector retrieval |
| **Named Entity Extraction** | Fuzzy matching + substring matching |
| **Entity Normalization** | Canonical symptom node mapping |
| **Weighted Scoring** | Severity × match confidence × coverage ratio |
| **Multi-hop Reasoning** | Symptom → Disease → Precaution traversal |
| **LLM Grounding** | Claude constrained to graph data only |
| **Prompt Engineering** | Structured context prevents hallucination |

---

## 🆚 Graph RAG vs Standard RAG

| | Standard RAG | Graph RAG (This Project) |
|--|-------------|------------------------|
| **Retrieval** | Vector similarity | Graph traversal |
| **Context** | Text chunks | Structured entities + relationships |
| **Reasoning** | LLM reads paragraphs | LLM reasons over graph paths |
| **Explainability** | Hard to trace | Every hop traceable ✅ |
| **Multi-hop** | Difficult | Natural ✅ |
| **Hallucination** | Possible | Constrained to graph data ✅ |

---

## 🗂️ Dataset

**Source:** [Disease Symptom Dataset](https://github.com/itachi9604/Disease-Symptom-dataset)

| File | Purpose | Used For |
|------|---------|----------|
| `dataset.csv` | Disease-symptom mappings | Graph edges (INDICATES) |
| `symptom_severity.csv` | Symptom severity weights | Edge properties |
| `symptom_Description.csv` | Disease descriptions | Node properties + LLM context |
| `symptom_precaution.csv` | Clinical precautions | Graph edges (PRECAUTION) |

---

## ⚙️ Tech Stack
Knowledge Graph:    NetworkX (DiGraph)
NLP Matching:       difflib (SequenceMatcher)
LLM:                Claude (Anthropic API)
Interface:          Streamlit
Data:               Pandas, NumPy
Visualization:      Matplotlib

---
## 🚀 Quick Start
### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/medical-knowledge-graph
cd medical-knowledge-graph
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Add Dataset Files
Place these in project root:
├── dataset.csv
├── symptom_Description.csv
├── symptom_precaution.csv
└── symptom_severity.csv

### 4. Run Application
```bash
streamlit run app.py
```
### 5. Open Browser
http://localhost:8501
Enter Anthropic API key in sidebar
Type symptoms → Get diagnosis

## 💡 Sample Results

**Input:** `"high fever, chills, sweating and headache"`
---

## 🔬 How The Scoring Works

```python
# For each matched symptom → traverse graph → find diseases

# Raw Score (accumulate per disease):
raw_score += symptom_severity × match_confidence

# Coverage Ratio (how complete is the match?):
coverage = matched_symptoms / total_disease_symptoms

# Final Score (balanced ranking):
final_score = raw_score × coverage

# Why coverage matters:
# Disease A: 2/4 symptoms matched  = 50% coverage → ranked higher
# Disease B: 2/17 symptoms matched = 12% coverage → ranked lower
# Even if Disease B has higher raw score
```

---

## ⚠️ Limitations & Disclaimer

> **⚠️ MEDICAL DISCLAIMER:** This system is for 
> educational and research purposes only. 
> It is NOT a substitute for professional medical advice, 
> diagnosis, or treatment. Always consult a qualified 
> physician for medical decisions.

---

## 📦 Requirements

```txt
streamlit
networkx
pandas
numpy
anthropic
matplotlib
difflib
```

---

## 🗺️ Portfolio Context

This is **Day 3** of my AI/ML Engineering journey:

| Day | Project | Type | Key Skills |
|-----|---------|------|-----------|
| 1 | Credit Risk Scoring | ML Classification | SMOTE, AUC, SHAP, LightGBM |
| 2 | Sales Forecasting | Time Series | Lag features, Walk-Forward CV |
| **3** | **Medical Knowledge Graph** | **AI Engineering** | **Graph RAG, Knowledge Graph, LLM** |

---

## 📬 Connect

Built as part of a daily AI/ML engineering portfolio.
Follow my journey on LinkedIn and GitHub.