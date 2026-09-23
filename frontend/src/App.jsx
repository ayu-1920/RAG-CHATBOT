import React, { useState } from 'react';
import './index.css';
import UploadModal from './components/UploadModal';
import ChatWindow from './components/ChatWindow';

function App() {
  const [documentId, setDocumentId] = useState(null);

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Production RAG Interface</h1>
        {!documentId && (
          <UploadModal onUploadSuccess={(id) => setDocumentId(id)} />
        )}
        {documentId && (
           <span className="doc-badge">Document Session Active</span>
        )}
      </header>
      
      <main className="app-main">
        <ChatWindow documentId={documentId} />
      </main>
    </div>
  );
}

export default App;
