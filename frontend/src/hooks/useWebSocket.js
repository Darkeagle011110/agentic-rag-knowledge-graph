import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * WebSocket hook for real-time agent communication.
 * @param {string} sessionId - The pipeline session ID
 */
export function useWebSocket(sessionId) {
  const [messages, setMessages] = useState([])
  const [stage, setStage] = useState('idle')
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const wsRef = useRef(null)
  const streamBufferRef = useRef('')
  const streamMsgIdRef = useRef(null)

  useEffect(() => {
    if (!sessionId) return

    const ws = new WebSocket(`ws://localhost:8000/api/chat/ws/${sessionId}`)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onerror = () => setIsConnected(false)

    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data)

      if (msg.type === 'status') {
        setStage(msg.data)
      } else if (msg.type === 'token') {
        streamBufferRef.current += msg.data
        const currentBuffer = streamBufferRef.current
        const msgId = streamMsgIdRef.current

        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.id === msgId) {
            return [...prev.slice(0, -1), { ...last, content: currentBuffer }]
          }
          return prev
        })
      } else if (msg.type === 'done') {
        setIsStreaming(false)
        streamBufferRef.current = ''
        streamMsgIdRef.current = null
      } else if (msg.type === 'error') {
        setIsStreaming(false)
        setMessages(prev => [...prev, {
          id: Date.now(),
          role: 'assistant',
          content: `❌ Error: ${msg.data}`,
          stage,
          timestamp: new Date(),
        }])
      }
    }

    return () => ws.close()
  }, [sessionId])

  const sendMessage = useCallback((text) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    if (!text.trim()) return

    const userMsg = { id: Date.now(), role: 'user', content: text, timestamp: new Date() }
    const assistantMsgId = Date.now() + 1
    const assistantMsg = { id: assistantMsgId, role: 'assistant', content: '', stage, timestamp: new Date() }

    streamMsgIdRef.current = assistantMsgId
    streamBufferRef.current = ''

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)
    wsRef.current.send(JSON.stringify({ message: text }))
  }, [stage])

  return { messages, stage, isConnected, isStreaming, sendMessage }
}
