<div align="center">

# 🧠 Agentic RAG — Knowledge Graph Builder

### A multi-agent AI system that constructs Neo4j knowledge graphs from structured and unstructured data

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.x-008CC1?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-Agent%20Dev%20Kit-4285F4?style=flat-square&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## ✨ What Is This?

**Agentic RAG — Knowledge Graph Builder** is a production-ready full-stack application where a team of AI agents — orchestrated by **Google's Agent Development Kit (ADK)** — collaboratively guide you through building a rich **Neo4j property graph** from your own data files.

Instead of writing Cypher by hand, you simply **chat with the agents**. They will:

1. 🎯 **Understand your intent** — What kind of graph do you need?
2. 📁 **Select the right files** — Which CSVs and markdown documents to process?
3. 🔷 **Design the schema** — Propose and refine nodes/relationships with a built-in critic loop
4. 🔍 **Recognize entities** — Identify named entity types in unstructured text
5. 🔗 **Extract facts** — Build subject-predicate-object triples from text
6. 🏗️ **Construct the graph** — Automatically load domain data + build lexical/subject graphs

Every step is visible in a real-time **knowledge graph visualization** powered by `vis-network`.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser (React + Vite)                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────┐   │
│  │ Chat Panel   │  │  Graph Visualizer │  │  Pipeline   │   │
│  │ (WebSocket)  │  │  (vis-network)    │  │  Sidebar    │   │
│  └──────┬───────┘  └────────┬─────────┘  └──────┬──────┘   │
└─────────┼───────────────────┼────────────────────┼──────────┘
          │WebSocket           │REST                │REST
┌─────────▼───────────────────▼────────────────────▼──────────┐
│                    FastAPI Backend                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Agent Coordinator                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │  Intent  │ │  Files   │ │  Schema  │ │  KG Bld  │  │ │
│  │  │  Agent   │→│  Agent   │→│ Loop+   │→│  Engine  │  │ │
│  │  │          │ │          │ │ Critic   │ │          │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  │                    ↕ Google ADK (LiteLLM / OpenAI)     │ │
│  └─────────────────────────────────────────────────────────┘ │
└────────────────────────────┬─────────────────────────────────┘
                             │Bolt / Cypher
                   ┌─────────▼──────────┐
                   │    Neo4j 5.x        │
                   │  (Property Graph)   │
                   └────────────────────┘
```

---

## 🚀 Quick Start

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/agentic-rag-knowledge-graph.git
cd agentic-rag-knowledge-graph

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY and NEO4J_PASSWORD

# 3. Start Neo4j (and optionally the backend)
docker compose up -d neo4j

# 4. Install & run the backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 5. Install & run the frontend
cd ../frontend && npm install && npm run dev

# 6. Open the app → http://localhost:5173
```

### Option B — Manual (Neo4j Desktop)

1. Install [Neo4j Desktop](https://neo4j.com/download/) and create a local database
2. Enable the APOC plugin from the Desktop UI
3. Follow steps 4–6 above

---

## 📁 Project Structure

```
agentic-rag-knowledge-graph/
├── backend/
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Environment settings
│   ├── neo4j_client.py           # Neo4j driver wrapper
│   ├── agents/
│   │   ├── base.py               # AgentCaller helper
│   │   ├── user_intent.py        # Goal ideation agent
│   │   ├── file_suggestion.py    # File selection agent
│   │   ├── schema_proposal.py    # Schema + Critic loop
│   │   ├── schema_unstructured.py# NER + Fact extraction
│   │   ├── kg_construction.py    # Domain & subject graph builder
│   │   └── coordinator.py        # Pipeline state machine
│   ├── tools/
│   │   ├── file_tools.py         # list_files, sample_file, search_file
│   │   ├── goal_tools.py         # set/approve goal
│   │   └── schema_tools.py       # propose/approve schema
│   ├── routes/
│   │   ├── chat.py               # WebSocket endpoint
│   │   ├── graph.py              # Graph viz & Cypher API
│   │   └── pipeline.py           # Health & file routes
│   └── data/
│       ├── *.csv                 # Structured supply-chain data
│       └── product_reviews/*.md  # Unstructured review text
├── frontend/
│   └── src/
│       ├── App.jsx               # Root component
│       ├── index.css             # Design system
│       ├── components/
│       │   ├── ChatPanel.jsx     # AI chat UI
│       │   ├── GraphView.jsx     # vis-network graph
│       │   ├── PipelineStatus.jsx# Sidebar agent tracker
│       │   └── Header.jsx        # Navigation bar
│       └── hooks/
│           └── useWebSocket.js   # WS + streaming hook
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🤖 The Agent Pipeline

| Stage | Agent | Tools | Output |
|-------|-------|-------|--------|
| 1 | **User Intent** | `set_perceived_user_goal`, `approve_perceived_user_goal` | `approved_user_goal` |
| 2 | **File Suggestion** | `list_available_files`, `sample_file`, `approve_suggested_files` | `approved_files` |
| 3 | **Schema Proposal** (+ Critic) | `propose_node_construction`, `propose_relationship_construction` | `approved_construction_plan` |
| 4 | **NER** | `get_well_known_types`, `set_proposed_entities` | `approved_entity_types` |
| 5 | **Fact Extraction** | `add_proposed_fact`, `approve_proposed_facts` | `approved_fact_types` |
| 6 | **KG Construction** | `construct_domain_graph`, `build_subject_graph` | Neo4j graph |

> **Critic Pattern**: Step 3 uses Google ADK's `LoopAgent` where a proposal agent and a critic agent iterate up to 3 times before fixing the schema as "valid".

---

## 🔌 API Reference

Once the backend is running, visit **http://localhost:8000/docs** for the full OpenAPI documentation.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/new-session` | GET | Create a new pipeline session |
| `/api/chat/ws/{session_id}` | WS | Real-time agent chat |
| `/api/chat/status/{session_id}` | GET | Current pipeline stage |
| `/api/graph/visualize` | GET | Graph data for rendering |
| `/api/graph/stats` | GET | Node/relationship counts |
| `/api/graph/labels` | GET | All node labels |
| `/api/graph/query` | POST | Read-only Cypher endpoint |
| `/api/files` | GET | Available data files |
| `/api/health` | GET | System health check |

---

## ⚙️ Environment Variables

Copy `.env.example` → `.env` and fill in:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | — |
| `OPENAI_MODEL` | Model for agents | `gpt-4o` |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | `text-embedding-3-large` |
| `NEO4J_URI` | Neo4j Bolt URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | — |
| `DATA_DIR` | Data files directory | `data` |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Agent Framework** | Google Agent Development Kit (ADK) |
| **LLM** | OpenAI GPT-4o via LiteLLM |
| **Graph Database** | Neo4j 5.x with APOC |
| **Graph RAG** | neo4j-graphrag `SimpleKGPipeline` |
| **Backend** | FastAPI + Uvicorn + WebSockets |
| **Frontend** | React 18 + Vite 5 |
| **Graph Viz** | vis-network |
| **Containerisation** | Docker Compose |

---

## 🤝 Contributing

Contributions are welcome! Please read the project conventions, open an issue first to discuss what you'd like to change, and submit a pull request.

```bash
# Fork → Create feature branch → Commit → Push → Pull Request
git checkout -b feature/my-new-agent
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.

---

<div align="center">
  Made with ❤️ by leveraging Google ADK, Neo4j, and OpenAI
</div>
