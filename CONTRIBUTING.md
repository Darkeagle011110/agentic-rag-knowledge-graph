# Contributing to Agentic RAG — Knowledge Graph Builder

First off, thank you for considering contributing to Agentic RAG! It's people like you that make this tool great.

## How to Contribute

1. **Fork the repository.**
2. **Create a new branch** for your feature or bug fix: `git checkout -b feature/your-feature-name`
3. **Make your changes.** Be sure to follow the existing code style.
4. **Test your code.** Ensure that both the backend and frontend run locally without issues.
5. **Commit your changes:** `git commit -m 'Add some feature'`
6. **Push to the branch:** `git push origin feature/your-feature-name`
7. **Submit a pull request.**

## Setting up for Local Development

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- Docker (for Neo4j)

### Backend Setup
1. `cd backend`
2. Create virtual environment (recommended): `python -m venv venv`
3. Activate virtual environment.
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` in the project root and add API keys.
6. `uvicorn main:app --reload --port 8000`

### Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Access at `http://localhost:5173`

### Neo4j Setup
Use `docker-compose up -d neo4j` to start a local Neo4j instance as configured in `docker-compose.yml`.

## Code Style
- **Python:** We follow standard PEP 8 conventions. Use type hints where appropriate.
- **JavaScript/React:** Use functional components and hooks. Maintain the design system variables from `index.css`.

Please open an issue for major changes before opening a PR to discuss what you want to change.
