import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiUpload, FiFile, FiX } from 'react-icons/fi';
import { preventFormNavigation } from '../utils/helpers';
import './FileUpload.css';

// Allowed file types
const ALLOWED_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/csv'
];

// Max file size: 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function FileUpload() {
  const { authToken } = useAuth();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [error, setError] = useState('');

  const validateFile = useCallback((file) => {
    if (!file) return null;
    
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Invalid file type. Please upload PDF, TXT, MD, DOC, DOCX, or CSV files.';
    }
    
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return 'File is too large. Maximum size is 10MB.';
    }
    
    return null;
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    
    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 5000);
      return;
    }
    
    setFile(selectedFile);
    setMessage('');
    setError('');
  };

  const clearFile = () => {
    setFile(null);
    setError('');
    setMessage('');
  };

  const handleUpload = async (e) => {
    if (e) {
      preventFormNavigation(e);
    }
    
    if (!file || !authToken) return;
    
    setUploading(true);
    setError('');
    
    try {
      const result = await api.uploadFile(authToken, file);
      setMessage(`Successfully uploaded ${result.filename}`);
      setShowMessage(true);
      setTimeout(() => setShowMessage(false), 5000);
      setFile(null);
    } catch (error) {
      setError(error.message);
      setShowMessage(true);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="file-upload">
      <div className="file-input-container">
        <input 
          id="file-upload" 
          type="file" 
          onChange={handleFileChange} 
          className="file-input"
          accept=".pdf,.txt,.md,.doc,.docx,.csv"
        />
        
        {file ? (
          <div className="selected-file">
            <FiFile className="file-icon" />
            <span className="file-name">{file.name}</span>
            <button 
              type="button" 
              className="clear-file" 
              onClick={clearFile}
              aria-label="Clear selected file"
            >
              <FiX />
            </button>
          </div>
        ) : (
          <label htmlFor="file-upload" className="file-label">
            <FiFile />
            Choose file
          </label>
        )}
      </div>
      
      <button 
        type="button"
        onClick={handleUpload} 
        disabled={!file || uploading || !authToken || !!error}
        className="upload-button"
        aria-busy={uploading}
      >
        {uploading ? 'Uploading...' : <><FiUpload /> Upload</>}
      </button>
      
      {showMessage && (
        <div className={`upload-message ${error ? 'error' : 'success'}`}>
          {error || message}
        </div>
      )}
    </div>
  );
}
