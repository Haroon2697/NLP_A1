import { useEffect, useRef, useState } from 'react';

const createSessionId = () => `session-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

function App() {
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('fitzone_vite_session') || createSessionId();
  });
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState('Connected to Local CPU');
  const [streaming, setStreaming] = useState(false);
  const [theme, setTheme] = useState('light');
  const [telemetry, setTelemetry] = useState(null);

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const streamBufferRef = useRef('');

  useEffect(() => {
    localStorage.setItem('fitzone_vite_session', sessionId);
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  useEffect(() => {
    // Setup WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://127.0.0.1:8000/ws/chat`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('Connected to Local CPU (Qwen 2.5 3B)');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'start') {
          setStreaming(true);
          streamBufferRef.current = '';
          setStatus('Generating response on CPU...');
          setMessages((prev) => [...prev, { role: 'assistant', content: '', metrics: null }]);
        } else if (data.type === 'token') {
          streamBufferRef.current += data.content;
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === 'assistant') {
              last.content = streamBufferRef.current;
            }
            return next;
          });
        } else if (data.type === 'done') {
          setStreaming(false);
          setStatus('Ready');
          const finalMetrics = {
            ttft: data.ttft || 1.0,
            tokens: data.tokens || 0,
            elapsed: data.elapsed || 0,
            tps: data.tps || 4.1,
          };
          setTelemetry(finalMetrics);
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last && last.role === 'assistant') {
              last.metrics = finalMetrics;
            }
            return next;
          });
        } else if (data.type === 'error') {
          setStreaming(false);
          setStatus(`Error: ${data.message}`);
          setMessages((prev) => [...prev, { role: 'assistant', content: `⚠️ ${data.message}` }]);
        }
      } catch (err) {
        console.error('WS parse error', err);
      }
    };

    ws.onerror = () => {
      setStatus('Connection error. Is FastAPI running on port 8000?');
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (textToSend = null) => {
    const text = (textToSend !== null ? textToSend : input).trim();
    if (!text || streaming) return;

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      alert('WebSocket is not connected. Ensure FastAPI is running at http://127.0.0.1:8000.');
      return;
    }

    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setInput('');
    wsRef.current.send(JSON.stringify({ session_id: sessionId, message: text }));
  };

  const newSession = () => {
    if (streaming) return;
    const newId = createSessionId();
    setSessionId(newId);
    setMessages([]);
    setStatus('New session started');
  };

  const starterPrompts = [
    'What are the differences between Basic, Standard, and Premium membership plans?',
    'What days and times are Yoga and HIIT classes offered?',
    'How does the 30-day membership freeze policy work?',
    'Who are the personal trainers at FitZone and what are their specialties?',
  ];

  return (
    <div className={`app-shell ${theme}`}>
      <header className="topbar">
        <div className="topbar-brand">
          <span className="brand-badge">FitZone Gym</span>
          <h1>FitAssist AI</h1>
          <span className="engine-pill">CPU Local Engine</span>
        </div>
        <div className="topbar-actions">
          <button className="theme-btn" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
            {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
          </button>
          <button className="new-btn" onClick={newSession}>
            ＋ New Chat
          </button>
        </div>
      </header>

      <main className="chat-panel">
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="hero-box">
              <div className="hero-badge">🏋️ Welcome to FitZone</div>
              <h2>How can I help you reach your goals?</h2>
              <p>Ask anything about gym memberships, fitness classes, certified trainers, and club policies.</p>
              <div className="starter-grid">
                {starterPrompts.map((prompt, i) => (
                  <button key={i} className="starter-card" onClick={() => sendMessage(prompt)}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-row ${msg.role}`}>
                <div className="avatar">{msg.role === 'assistant' ? '⚡' : '👤'}</div>
                <div className="message-bubble">
                  <div className="message-text">{msg.content}</div>
                  {msg.metrics && (
                    <div className="telemetry-bar">
                      ⚡ TTFT: {msg.metrics.ttft}s | {msg.metrics.tps} tok/s | {msg.metrics.tokens} tokens
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {streaming && <div className="typing-indicator">⚡ Generating tokens on CPU...</div>}
          <div ref={messagesEndRef} />
        </div>

        <div className="composer-row">
          <input
            value={input}
            placeholder="Ask about memberships, classes, trainers, or gym timings..."
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') sendMessage();
            }}
            disabled={streaming}
          />
          <button onClick={() => sendMessage()} disabled={streaming || !input.trim()}>
            Send
          </button>
        </div>
        <div className="status-bar">{status}</div>
      </main>
    </div>
  );
}

export default App;
