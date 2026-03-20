import { useState, useEffect } from 'react'
import Header from './components/Header.jsx'
import PipelineStatus from './components/PipelineStatus.jsx'
import ChatPanel from './components/ChatPanel.jsx'
import GraphView from './components/GraphView.jsx'
import { useWebSocket } from './hooks/useWebSocket.js'

async function createSession() {
  try {
    const res = await fetch('/api/chat/new-session')
    const data = await res.json()
    return data.session_id
  } catch {
    // Fallback ID for offline/demo mode
    return `demo-${Math.random().toString(36).slice(2, 8)}`
  }
}

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const { messages, stage, isConnected, isStreaming, sendMessage } = useWebSocket(sessionId)

  useEffect(() => {
    createSession().then(setSessionId)
  }, [])

  return (
    <div className="app-shell">
      <Header stage={stage} isConnected={isConnected} />

      <PipelineStatus stage={stage} sessionId={sessionId} />

      <ChatPanel
        messages={messages}
        stage={stage}
        isConnected={isConnected}
        isStreaming={isStreaming}
        onSend={sendMessage}
      />

      <GraphView />
    </div>
  )
}
