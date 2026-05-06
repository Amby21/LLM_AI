# 💬 DataDialogue — Natural Language to SQL

> Ask your database anything in plain English.
> DataDialogue writes the SQL, runs it, explains the results,
> and keeps a full audit trail of every query.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![LangGraph](https://img.shields.io/badge/LangGraph-0.1.5-purple)
![Claude](https://img.shields.io/badge/Claude-Sonnet-orange)
![Docker](https://img.shields.io/badge/Docker-ready-blue)

---

## 🎯 The Problem

Business teams have questions. Their data has answers.
But between them sits a wall called SQL.

Most people can't write SQL. Even those who can don't
know your specific database schema. DataDialogue removes
that wall entirely.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Natural Language Queries** | Ask in plain English, get SQL + results |
| ⚡ **SQL Transparency** | Every query shown in collapsible code block |
| 📊 **Dynamic Results Table** | Results rendered as a clean table |
| 💡 **Explain This** | Claude interprets results in business terms |
| 📋 **Schema Explorer** | Browse tables and columns in the sidebar |
| 🕐 **Session History** | All queries from current session in one panel |
| 🛡️ **3-Layer SQL Safety** | Prompt + validation + read-only connection |
| 📝 **Full Audit Trail** | Every query logged with SQL and timestamp |
| 📈 **MLFlow Tracking** | Every conversation tracked as experiment run |
| 🐳 **Docker Ready** | One command deployment |

---

## 🛡️ Safety Architecture

DataDialogue is read-only by design. Three independent
layers prevent any data modification:
---

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Claude Sonnet | Best reasoning for SQL generation |
| Agent | LangGraph | ReAct loop, reliable tool calling |
| Backend | FastAPI | Async, Pydantic validation, auto docs |
| Database | SQLite | Zero setup, file-based, portable |
| Safety | Custom (safety.py) | 3-layer SQL injection prevention |
| Tracking | MLFlow | Full query observability |
| Container | Docker | One-command deployment |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat` | Send question, get SQL + results |
| POST | `/explain` | Business interpretation of last result |
| GET | `/schema` | Database schema for explorer panel |
| GET | `/stats` | Table counts and row totals |
| GET | `/health` | Health check |
| GET | `/docs` | Auto-generated API documentation |



---

## 👤 Author

**Skandan Ganesh** — AI & Data Engineer
[LinkedIn](https://linkedin.com/in/skandan-ganesh) ·
[GitHub](https://github.com/Amby21) ·
[skandanganesh.com](https://skandanganesh.com)

---

## 📄 License

MIT — free to use, fork, and build on.