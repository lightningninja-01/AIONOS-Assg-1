import React, { useState, useRef, useEffect } from 'react'
import type { AnswerResponse } from '../api/client'
import { postQuery } from '../api/client'
import { AgentTrace } from './AgentTrace'
import { CommitmentCard } from './CommitmentCard'

const DEMO_QUERIES = [
  'What did I promise Raghav?',
  'What needs action today?',
  'Who owns the Mumbai office renewal?',
  'What am I waiting on?',
]

interface ChatMessage {
  id: string
  type: 'user' | 'agent' | 'error'
  text: string
  response?: AnswerResponse
}

export function ChatPanel({ asOfDate }: { asOfDate: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendQuery = async (question: string) => {
    if (!question.trim() || loading) return
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      text: question,
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const response = await postQuery(question, asOfDate)
      const agentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        text: response.answer,
        response,
      }
      setMessages((prev) => [...prev, agentMsg])
    } catch (err) {
      const errMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        text: 'Failed to contact agent. Ensure the backend is running at localhost:8001.',
      }
      setMessages((prev) => [...prev, errMsg])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Demo query chips */}
      <div className="flex flex-wrap gap-2 mb-3">
        {DEMO_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => sendQuery(q)}
            disabled={loading}
            className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white px-3 py-1.5 rounded-full border border-gray-600 transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Message area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 min-h-0">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-8">
            <p className="text-2xl mb-2">💬</p>
            <p>Ask the agent about your commitments.</p>
            <p className="text-xs mt-1 text-gray-600">Try one of the demo queries above.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.type === 'user' && (
              <div className="flex justify-end">
                <div className="bg-blue-600 text-white text-sm px-4 py-2 rounded-2xl rounded-tr-sm max-w-xs">
                  {msg.text}
                </div>
              </div>
            )}

            {msg.type === 'agent' && msg.response && (
              <div className="space-y-2">
                <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-tl-sm p-4">
                  <p className="text-sm text-gray-100 leading-relaxed">{msg.text}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs text-gray-500">Confidence:</span>
                    <span
                      className={`text-xs font-semibold ${
                        msg.response.confidence === 'high'
                          ? 'text-green-400'
                          : msg.response.confidence === 'medium'
                          ? 'text-yellow-400'
                          : 'text-red-400'
                      }`}
                    >
                      {msg.response.confidence.toUpperCase()}
                    </span>
                  </div>
                </div>

                <AgentTrace steps={msg.response.reasoning_steps} isLoading={false} />

                {msg.response.commitments_cited.length > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-2">Referenced commitments:</p>
                    <div className="space-y-2">
                      {msg.response.commitments_cited.map((c) => (
                        <CommitmentCard key={c.commitment_id} commitment={c} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {msg.type === 'error' && (
              <div className="bg-red-900/30 border border-red-700 rounded-xl p-3">
                <p className="text-red-400 text-sm">{msg.text}</p>
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div>
            <AgentTrace steps={[]} isLoading={true} />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendQuery(input)}
          placeholder="Ask about your commitments..."
          disabled={loading}
          className="flex-1 bg-gray-800 border border-gray-600 rounded-xl px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
        />
        <button
          onClick={() => sendQuery(input)}
          disabled={loading || !input.trim()}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white px-4 py-2.5 rounded-xl text-sm font-semibold transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  )
}
