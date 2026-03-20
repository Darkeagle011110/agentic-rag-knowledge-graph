import { useState, useEffect } from 'react'
import { Activity, Database, FileText } from 'lucide-react'

const STAGES = [
  { key: 'user_intent',      label: 'User Intent',       desc: 'Define your KG goal',      icon: '🎯' },
  { key: 'file_suggestion',  label: 'File Selection',    desc: 'Choose data files',        icon: '📁' },
  { key: 'schema_proposal',  label: 'Schema Design',     desc: 'Propose & refine schema',  icon: '🔷' },
  { key: 'ner',              label: 'Entity Recognition',desc: 'Find entity types in text', icon: '🔍' },
  { key: 'fact_extraction',  label: 'Fact Extraction',   desc: 'Extract knowledge triples', icon: '🔗' },
  { key: 'kg_construction',  label: 'KG Construction',   desc: 'Build Neo4j graph',        icon: '🏗️' },
]

function StageItem({ step, currentStage }) {
  const idx = STAGES.findIndex(s => s.key === currentStage)
  const myIdx = STAGES.findIndex(s => s.key === step.key)
  const isActive   = step.key === currentStage
  const isComplete = myIdx < idx || currentStage === 'complete'

  return (
    <div className={`pipeline-step ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''}`}>
      <div className="step-icon">
        {isComplete ? '✓' : step.icon}
      </div>
      <div className="step-info">
        <div className="step-name">{step.label}</div>
        <div className="step-desc">{step.desc}</div>
      </div>
    </div>
  )
}

export default function PipelineStatus({ stage, sessionId }) {
  const [files, setFiles] = useState([])

  useEffect(() => {
    fetch('/api/files')
      .then(r => r.json())
      .then(d => setFiles(d.files || []))
      .catch(() => {})
  }, [])

  const csvFiles = files.filter(f => f.type === 'csv')
  const mdFiles  = files.filter(f => f.type === 'markdown')

  return (
    <aside className="sidebar">
      {/* Pipeline steps */}
      <div>
        <div className="sidebar-section-title">Agent Pipeline</div>
        <div className="pipeline-steps">
          {STAGES.map(s => (
            <StageItem key={s.key} step={s} currentStage={stage} />
          ))}
        </div>
      </div>

      {/* Data files */}
      {files.length > 0 && (
        <div>
          <div className="sidebar-section-title">Data Files ({files.length})</div>
          <div className="file-list">
            {csvFiles.slice(0, 6).map(f => (
              <div key={f.path} className="file-item">
                <span className="file-type-badge">CSV</span>
                <span style={{ flex:1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{f.name}</span>
              </div>
            ))}
            {mdFiles.slice(0, 4).map(f => (
              <div key={f.path} className="file-item">
                <span className="file-type-badge md">MD</span>
                <span style={{ flex:1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{f.name}</span>
              </div>
            ))}
            {files.length > 10 && (
              <div style={{ fontSize:'10px', color:'var(--text-muted)', padding:'4px 8px' }}>
                +{files.length - 10} more files
              </div>
            )}
          </div>
        </div>
      )}

      {/* Session info */}
      {sessionId && (
        <div style={{ marginTop:'auto' }}>
          <div className="sidebar-section-title">Session</div>
          <div style={{ fontSize:'10px', color:'var(--text-muted)', fontFamily:"'JetBrains Mono', monospace" }}>
            {sessionId.slice(0, 8)}...
          </div>
        </div>
      )}
    </aside>
  )
}
