import React, { useState } from 'react';

const ChatWindow = ({ documentId }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query.trim()) return;
    
    const userMsg = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const envUrl = import.meta.env.VITE_API_URL;
      const API_BASE = envUrl ? (envUrl.startsWith('http') ? envUrl : `https://${envUrl}`) : 'http://localhost:8000';
      
      const resp = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMsg.content, chat_history: messages })
      });
      
      // [Interview Design Note]: Stream Token Consumer
      // Reads Server-Sent Events dynamically to achieve the ChatGPT "typewriter" effect.
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      
      let aiMessage = { role: 'assistant', content: '', citations: [] };
      setMessages(prev => [...prev, aiMessage]);
      setLoading(false); // Stop spinner early since streaming starts immediately

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunkStr = decoder.decode(value, { stream: true });
        const lines = chunkStr.split('\n').filter(l => l.trim() !== '');
        
        for (const line of lines) {
            try {
                const parsed = JSON.parse(line);
                if (parsed.type === 'citations') {
                    aiMessage.citations = parsed.citations;
                } else if (parsed.type === 'chunk') {
                    aiMessage.content += parsed.content;
                }
                
                setMessages(prev => {
                   const newMsgs = [...prev];
                   newMsgs[newMsgs.length - 1] = { ...aiMessage };
                   return newMsgs;
                });
            } catch(e) {
                // Ignore partial chunks splitting during stream
            }
        }
      }
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Network Error.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-window">
      <div className="messages-area">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <p>{msg.content}</p>
            {msg.citations && msg.citations.length > 0 && (
              <div className="citations">
                <strong>Sources:</strong>
                <ul>
                  {msg.citations.map((cit, j) => (
                    <li key={j} title={cit.content_snippet}>Page {cit.page} ({cit.source})</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {loading && <div className="message assistant loading">...Thinking...</div>}
      </div>
      <div className="input-area">
        <input 
          type="text" 
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Ask a question about the document..."
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button onClick={handleSend} disabled={loading}>Send</button>
      </div>
    </div>
  );
}

export default ChatWindow;
