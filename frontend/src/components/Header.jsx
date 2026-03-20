import { GitBranch, ExternalLink } from 'lucide-react'

export default function Header({ stage, isConnected }) {
  const stageLabel = isConnected ? stage?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) : 'Offline'

  return (
    <header className="header">
      <div className="header-brand">
        <div className="header-logo">🧠</div>
        <div>
          <div className="header-title">Agentic RAG — Knowledge Graph</div>
          <div className="header-subtitle">Google ADK · Neo4j · OpenAI</div>
        </div>
      </div>

      <div className="header-status">
        <div className="status-badge">
          <div className={`status-dot ${isConnected ? '' : 'offline'}`} />
          {stageLabel || 'Ready'}
        </div>
        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="icon-btn"
          title="GitHub repository"
        >
          <GitBranch size={14} />
        </a>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="btn btn-ghost"
          title="Backend API docs"
        >
          <ExternalLink size={12} />
          API
        </a>
      </div>
    </header>
  )
}
