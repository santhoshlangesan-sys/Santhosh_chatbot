import { useEffect, useRef, useState } from 'react'
import './App.css'

const suggestions = [
  {
    title: 'Meet the squad',
    prompt: 'List all Jaguars players and their stats.',
    icon: '♧',
  },
  {
    title: 'Player profile',
    prompt: 'Show me Aarav Patel’s player details.',
    icon: '◎',
  },
  {
    title: 'Compare players',
    prompt: 'Compare the players by total runs.',
    icon: '↗',
  },
]

function createConversationId() {
  return crypto.randomUUID()
}

async function readJsonResponse(response) {
  const body = await response.text()
  if (!body) return null

  try {
    return JSON.parse(body)
  } catch {
    return null
  }
}

function App() {
  const [conversationId, setConversationId] = useState(createConversationId)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [apiStatus, setApiStatus] = useState('checking')
  const endOfMessagesRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    let isCurrent = true

    fetch('/api/health')
      .then((response) => {
        if (!response.ok) throw new Error('Assistant API is unavailable.')
        return readJsonResponse(response)
      })
      .then((data) => {
        if (!data) throw new Error('Assistant API returned an invalid response.')
        if (isCurrent) setApiStatus('online')
      })
      .catch(() => {
        if (isCurrent) setApiStatus('offline')
      })

    return () => {
      isCurrent = false
    }
  }, [])

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function startNewChat() {
    if (isLoading) return
    setConversationId(createConversationId())
    setMessages([])
    setDraft('')
    setError('')
    inputRef.current?.focus()
  }

  async function sendMessage(messageText) {
    const message = messageText.trim()
    if (!message || isLoading) return

    setMessages((current) => [...current, { role: 'user', content: message }])
    setDraft('')
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, message }),
      })
      const data = await readJsonResponse(response)

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            `Assistant API returned HTTP ${response.status}. Check that the backend is running and review its terminal for errors.`,
        )
      }

      if (typeof data?.reply !== 'string') {
        throw new Error('Assistant API returned an invalid response. Check the backend logs.')
      }

      setMessages((current) => [...current, { role: 'assistant', content: data.reply }])
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to reach the assistant. Check that the backend is running.',
      )
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendMessage(draft)
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage(draft)
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">J</div>
          <div>
            <strong>Jaguars</strong>
            <span>CRICKET CLUB</span>
          </div>
        </div>

        <button className="new-chat-button" onClick={startNewChat} disabled={isLoading}>
          <span aria-hidden="true">＋</span>
          New chat
        </button>

        <div className="sidebar-section-label">YOUR ASSISTANT</div>
        <div className="sidebar-chat selected-chat">
          <span className="chat-glyph" aria-hidden="true">◌</span>
          <span>Squad &amp; player stats</span>
        </div>

        <div className="sidebar-footer">
          <div className={`online-indicator ${apiStatus}`} />
          <div>
            <strong>{apiStatus === 'online' ? 'Assistant connected' : 'Assistant unavailable'}</strong>
            <span>{apiStatus === 'online' ? 'Ready for team questions' : 'Start the backend API'}</span>
          </div>
        </div>
      </aside>

      <section className="chat-panel">
        <header className="topbar">
          <div>
            <span className="mobile-brand">JAGUARS</span>
            <h1>Club assistant</h1>
          </div>
          <div className="model-badge">
            <span className="status-dot" />
            AI assistant
          </div>
        </header>

        <section className="conversation" aria-label="Chat conversation">
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-emblem" aria-hidden="true">J</div>
              <p className="eyebrow">JAGUARS CRICKET CLUB</p>
              <h2>What would you like<br />to know?</h2>
              <p className="welcome-copy">
                Would you like Jaguars team records or cricket records? Ask about
                player profiles, squad statistics, or ODI run rankings.
              </p>
              <div className="suggestion-grid">
                {suggestions.map((suggestion) => (
                  <button
                    className="suggestion-card"
                    key={suggestion.title}
                    onClick={() => sendMessage(suggestion.prompt)}
                    disabled={isLoading}
                  >
                    <span className="suggestion-icon" aria-hidden="true">{suggestion.icon}</span>
                    <span>
                      <strong>{suggestion.title}</strong>
                      <small>{suggestion.prompt}</small>
                    </span>
                    <span className="suggestion-arrow" aria-hidden="true">↗</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="message-list" role="log" aria-live="polite">
              {messages.map((message, index) => (
                <article className={`message-row ${message.role}`} key={`${index}-${message.role}`}>
                  <div className={`message-avatar ${message.role}`} aria-hidden="true">
                    {message.role === 'user' ? 'Y' : 'J'}
                  </div>
                  <div className="message-body">
                    <div className="message-author">
                      {message.role === 'user' ? 'You' : 'Jaguars assistant'}
                    </div>
                    <p>{message.content}</p>
                  </div>
                </article>
              ))}
              {isLoading && (
                <article className="message-row assistant">
                  <div className="message-avatar assistant" aria-hidden="true">J</div>
                  <div className="message-body">
                    <div className="message-author">Jaguars assistant</div>
                    <div className="typing-indicator" aria-label="Assistant is responding">
                      <span /><span /><span />
                    </div>
                  </div>
                </article>
              )}
              <div ref={endOfMessagesRef} />
            </div>
          )}
        </section>

        <footer className="composer-area">
          {error && <p className="error-message" role="alert">{error}</p>}
          <form className="composer" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about the Jaguars..."
              aria-label="Message the Jaguars assistant"
              rows="1"
              maxLength="4000"
              disabled={isLoading}
            />
            <button
              className="send-button"
              type="submit"
              disabled={isLoading || !draft.trim()}
              aria-label="Send message"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 12h14M13 5l7 7-7 7" />
              </svg>
            </button>
          </form>
          <p className="composer-hint">Enter to send · Shift + Enter for a new line</p>
        </footer>
      </section>
    </main>
  )
}

export default App
