import { useRef, useEffect, useState } from 'react'
import { Send, Sparkles } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const STAGE_LABELS = {
  idle:              '⬤ Ready',
  user_intent:       '🎯 Intent',
  file_suggestion:   '📁 Files',
  schema_proposal:   '🔷 Schema',
  ner:               '🔍 NER',
  fact_extraction:   '🔗 Facts',
  kg_construction:   '🏗️ Building',
  complete:          '✅ Done',
  error:             '❌ Error',
}

const SUGGESTIONS = [
  'I want to build a supply chain graph for root-cause analysis.',
  'Help me make a product recommendation knowledge graph.',
  'Create a social network graph of friends and interests.',
  "I'd like a fraud detection graph over financial transactions.",
]

function TypingIndicator() {
  return (
    <div className="message assistant">
      <div className="typing-indicator">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  )
}

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}`}>
      {msg.role === 'assistant' && msg.stage && (
        <div className="stage-tag">
          <Sparkles size={9} />
          {STAGE_LABELS[msg.stage] || msg.stage}
        </div>
      )}
      <div className="message-bubble">
        {msg.role === 'assistant' ? (
          <ReactMarkdown>{msg.content || ' '}</ReactMarkdown>
        ) : (
          msg.content
        )}
      </div>
      <div className="message-meta">
        {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  )
}

export default function ChatPanel({ messages, stage, isConnected, isStreaming, onSend }) {
  const [input, setInput]     = useState('')
  const scrollRef             = useRef(null)
  const inputRef              = useRef(null)
  const isEmpty = messages.length === 0

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isStreaming])

  function handleSend() {
    if (!input.trim() || isStreaming || !isConnected) return
    onSend(input)
    setInput('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <main className="chat-panel">
      <div className="chat-messages" ref={scrollRef}>
        {isEmpty ? (
          <div className="chat-welcome">
            <div className="chat-welcome-glyph">🧠</div>
            <h2>Agentic Knowledge Graph Builder</h2>
            <p>
              A multi-agent AI system that guides you through building a Neo4j knowledge
              graph from your data — step by step.
            </p>
            <div className="chat-welcome-suggestions">
              {SUGGESTIONS.map(s => (
                <button key={s} className="suggestion-chip" onClick={() => { onSend(s) }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => <Message key={m.id} msg={m} />)
        )}
        {isStreaming && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
          <TypingIndicator />
        )}
      </div>

      <div className="chat-input-area">
        {!isConnected && (
          <div style={{ textAlign:'center', fontSize:'11px', color:'var(--accent-warning)', marginBottom:'8px' }}>
            ⚠️ Not connected to backend — start the FastAPI server
          </div>
        )}
        <div className="chat-input-wrapper">
          <textarea
            ref={inputRef}
            className="chat-input"
            rows={1}
            placeholder={isConnected ? 'Message the agent…' : 'Backend offline…'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={!isConnected || isStreaming}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!isConnected || isStreaming || !input.trim()}
            title="Send (Enter)"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </main>
  )
}
