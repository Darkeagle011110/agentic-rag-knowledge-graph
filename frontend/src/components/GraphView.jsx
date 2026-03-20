import { useEffect, useRef, useState } from 'react'
import { RefreshCw, ZoomIn, ZoomOut } from 'lucide-react'

export default function GraphView() {
  const containerRef = useRef(null)
  const networkRef   = useRef(null)
  const [stats, setStats]    = useState({ nodes: 0, relationships: 0 })
  const [loading, setLoading] = useState(false)
  const [hasGraph, setHasGraph] = useState(false)
  const [labels, setLabels]  = useState([])
  const [activeLabel, setActiveLabel] = useState(null)

  async function fetchAndRender(label) {
    if (!containerRef.current) return
    setLoading(true)
    try {
      const url = label ? `/api/graph/visualize?label=${label}&limit=300` : '/api/graph/visualize?limit=300'
      const [vizRes, statsRes] = await Promise.all([
        fetch(url).then(r => r.json()),
        fetch('/api/graph/stats').then(r => r.json()),
      ])

      setStats({ nodes: statsRes.nodes || 0, relationships: statsRes.relationships || 0 })

      if (!vizRes.nodes || vizRes.nodes.length === 0) {
        setHasGraph(false)
        setLoading(false)
        return
      }

      setHasGraph(true)

      // Build vis-network dataset
      const { DataSet, Network } = await import('vis-network/standalone')

      const COLOR_MAP = {
        Product:  { background: '#6366f1', border: '#818cf8' },
        Assembly: { background: '#06b6d4', border: '#22d3ee' },
        Part:     { background: '#10b981', border: '#34d399' },
        Supplier: { background: '#f59e0b', border: '#fbbf24' },
        Review:   { background: '#ec4899', border: '#f472b6' },
        Chunk:    { background: '#8b5cf6', border: '#a78bfa' },
        default:  { background: '#475569', border: '#64748b' },
      }

      const nodes = new DataSet(vizRes.nodes.map(n => ({
        id: n.id,
        label: n.title || n.label,
        group: n.label,
        color: COLOR_MAP[n.label] || COLOR_MAP.default,
        font: { color: '#e2e8f0', size: 11 },
        borderWidth: 2,
      })))

      const edges = new DataSet(vizRes.edges.map((e, i) => ({
        id: i,
        from: e.from,
        to: e.to,
        label: e.label,
        color: { color: '#334155', highlight: '#6366f1', opacity: 0.8 },
        font: { color: '#94a3b8', size: 9, align: 'middle' },
        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
        smooth: { type: 'curvedCW', roundness: 0.1 },
      })))

      const options = {
        physics: {
          enabled: true,
          barnesHut: { gravitationalConstant: -6000, springLength: 120, damping: 0.2 },
        },
        interaction: { hover: true, tooltipDelay: 200 },
        nodes: { shape: 'dot', size: 14, shadow: true },
        edges: { width: 1.5 },
      }

      if (networkRef.current) networkRef.current.destroy()
      networkRef.current = new Network(containerRef.current, { nodes, edges }, options)
    } catch {
      // Neo4j not connected — just show placeholder
    }
    setLoading(false)
  }

  useEffect(() => {
    fetch('/api/graph/labels')
      .then(r => r.json())
      .then(d => setLabels(d.labels || []))
      .catch(() => {})

    fetchAndRender(null)
  }, [])

  return (
    <section className="graph-panel">
      <div className="graph-header">
        <div>
          <div className="graph-header-title">Knowledge Graph</div>
          <div style={{ fontSize:'10px', color:'var(--text-muted)' }}>Neo4j live view</div>
        </div>
        <div style={{ display:'flex', gap:'6px', alignItems:'center' }}>
          {labels.slice(0, 4).map(l => (
            <button
              key={l}
              className={`btn btn-ghost`}
              style={{ padding:'2px 8px', fontSize:'10px', ...(activeLabel === l ? { borderColor:'var(--accent-primary)', color:'var(--accent-primary)' } : {}) }}
              onClick={() => { setActiveLabel(l === activeLabel ? null : l); fetchAndRender(l === activeLabel ? null : l) }}
            >
              {l}
            </button>
          ))}
          <button
            className="icon-btn"
            title="Refresh graph"
            onClick={() => fetchAndRender(activeLabel)}
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <div className="graph-container">
        {loading && (
          <div style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', background:'hsl(228,28%,8%/.5)', zIndex:10 }}>
            <div style={{ display:'flex', gap:'6px' }}>
              {[0,1,2].map(i => <div key={i} className="typing-dot" style={{ animationDelay:`${i*0.2}s` }} />)}
            </div>
          </div>
        )}

        {!hasGraph && !loading && (
          <div className="graph-placeholder">
            <div className="graph-placeholder-icon">🕸️</div>
            <p>Your knowledge graph will appear here once constructed.</p>
            <p style={{ fontSize:'10px', opacity:.6 }}>Start the agent pipeline in the chat →</p>
          </div>
        )}

        <div ref={containerRef} className="graph-canvas" style={{ background:'transparent' }} />
      </div>

      <div className="graph-stats">
        <div className="stat-item">
          <span className="stat-value" style={{ color:'var(--accent-primary)' }}>{stats.nodes.toLocaleString()}</span>
          <span className="stat-label">Nodes</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{ color:'var(--accent-secondary)' }}>{stats.relationships.toLocaleString()}</span>
          <span className="stat-label">Relationships</span>
        </div>
        <div className="stat-item">
          <span className="stat-value" style={{ color:'var(--accent-graph)', fontSize:'14px', marginTop:'3px' }}>
            {hasGraph ? '🟢 Live' : '⚫ Empty'}
          </span>
          <span className="stat-label">Status</span>
        </div>
      </div>
    </section>
  )
}
