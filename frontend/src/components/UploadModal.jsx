import React, { useState } from 'react';

const UploadModal = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle');

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleUpload = async () => {
    if (!file) return;
    setStatus('uploading');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const envUrl = import.meta.env.VITE_API_URL;
      const API_BASE = envUrl ? (envUrl.startsWith('http') ? envUrl : `https://${envUrl}`) : 'http://localhost:8000';
      const resp = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await resp.json();
      setStatus('success');
      onUploadSuccess(data.document_id);
    } catch (e) {
      console.error(e);
      setStatus('error');
    }
  };

  return (
    <div className="upload-modal">
      <input type="file" onChange={handleFileChange} accept=".pdf"/>
      <button onClick={handleUpload} disabled={!file || status === 'uploading'}>
        {status === 'uploading' ? 'Ingesting...' : 'Upload PDF'}
      </button>
      {status === 'error' && <p className="error">Upload failed. Make sure backend is running.</p>}
    </div>
  );
}

export default UploadModal;
