# 🛡️ GovernanceGPT — AI Data Governance Copilot

> An AI-powered copilot that helps enterprise data teams manage their 
> data catalogue through natural language — built with Claude AI, 
> LangChain, FastAPI, and SQLite.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![LangChain](https://img.shields.io/badge/LangChain-0.2-purple)
![Claude](https://img.shields.io/badge/Claude-Sonnet-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

---

## 🎯 What Problem Does This Solve?

Enterprise data teams spend hours manually classifying datasets, 
writing data quality rules, tracking lineage, and chasing down 
asset ownership in tools like Collibra. GovernanceGPT turns those 
hours into seconds — just ask in plain English.

**"Classify the employee_records table"**  
**"Who should own the sales forecast report?"**  
**"Generate DQ rules for the email column in crm_contacts"**  
**"Explain the lineage of clean_transactions"**

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Agentic AI** | Claude-powered agent reasons across 7 governance tools |
| 🗂 **Asset Catalogue** | Full metadata store with domain, sensitivity, tags |
| 🔗 **Data Lineage** | Upstream/downstream lineage tracking and explanation |
| ✅ **DQ Rules** | AI-generated data quality rules with SQL expressions |
| 👤 **Ownership** | Suggests and assigns owners to unowned assets |
| 📋 **Audit Trail** | Every agent action logged with timestamp and context |
| 📊 **MLFlow Tracking** | Every conversation tracked as an experiment run |
| 🐳 **Docker Ready** | Single command deployment |

---

## 🏗️ Architecture
Frontend (HTML/JS)
│
FastAPI Backend (/chat, /assets, /lineage, /audit)
│
LangChain Agent (Claude Sonnet)
├── search_assets tool
├── classify_asset tool
├── generate_quality_rule tool
├── suggest_ownership tool
├── explain_lineage tool
├── governance_report tool
└── list_all_assets tool
│
SQLite Database (assets, lineage, quality_rules, audit_log)
MLFlow (experiment tracking)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Anthropic API key ([get one here](https://console.anthropic.com))

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/governancegpt.git
cd governancegpt
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 3. Seed the database
```bash
python data/seed_data.py
```

### 4. Run
```bash
uvicorn backend.main:app --reload --port 8000
```

Open **http://localhost:8000** 🎉

### Or with Docker
```bash
docker-compose up --build
```

---

## 💬 Example Interactions
You:  Give me a full governance health report
Bot:  📋 GOVERNANCE HEALTH REPORT
════════════════════════════
Total assets:     10
Unowned assets:   2 ⚠️
Assets by domain:
• finance: 3
• hr: 2  ...
You:  Classify the employee_records table
Bot:  ✅ Asset 'employee_records' classified successfully.
Domain: hr
Sensitivity: restricted
Tags: pii, sensitive, hr
Reasoning: Contains personal employee data including
salary — highest sensitivity warranted.
You:  Explain the lineage of clean_transactions
Bot:  📊 Lineage for 'clean_transactions':
⬆️  UPSTREAM: raw_transactions (table) [feeds_into]
⬇️  DOWNSTREAM: monthly_revenue_report (report) [feeds_into]

## 🗂️ Project Structure
governancegpt/
├── backend/
│   ├── main.py           # FastAPI app + all routes
│   ├── agent.py          # LangChain agent + 7 tools
│   ├── governance_db.py  # SQLite database operations
│   ├── models.py         # Pydantic data models
│   └── config.py         # Environment config
├── frontend/
│   └── index.html        # Chat UI + dashboard
├── data/
│   └── seed_data.py      # Sample enterprise data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| LLM | Claude Sonnet (Anthropic) | Reasoning + natural language |
| Agent | LangChain | Tool orchestration + ReAct loop |
| Backend | FastAPI | REST API + serving frontend |
| Database | SQLite | Metadata + audit storage |
| Tracking | MLFlow | Experiment + conversation logging |
| Container | Docker | Reproducible deployment |

---

## 🔮 Future Enhancements

- [ ] Collibra API integration (real governance platform sync)
- [ ] PostgreSQL backend for production scale
- [ ] Multi-user auth with role-based access
- [ ] Slack bot interface
- [ ] Automated DQ rule execution with pass/fail reporting
- [ ] Export audit log to PDF/CSV

---

## 👤 Author

**Skandan Ganesh** — AI & Data Governance Professional  
[LinkedIn](https://linkedin.com/in/skandan-ganesh) · 
[GitHub](https://github.com/Amby21) · 
[skandanganesh.com](https://skandanganesh.com)

---

## 📄 License

MIT — free to use, fork, and build on.