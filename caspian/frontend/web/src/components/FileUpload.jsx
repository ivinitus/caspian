import { useState, useCallback } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { FiUpload, FiFile, FiX, FiEye } from 'react-icons/fi';
import { preventFormNavigation } from '../utils/helpers';
import './FileUpload.css';

// Allowed file types
const ALLOWED_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/csv',
  'application/octet-stream', // For handling binary files
  'application/x-binary' // For other binary formats
];

// Max file size: 10MB
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function FileUpload() {
  const { authToken } = useAuth();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [message, setMessage] = useState('');
  const [showMessage, setShowMessage] = useState(false);
  const [error, setError] = useState('');
  const [extractedContent, setExtractedContent] = useState(null);

  const validateFile = useCallback((file) => {
    if (!file) return null;
    
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return 'File is too large. Maximum size is 10MB.';
    }
    // Check file type
    if (!ALLOWED_TYPES.includes(file.type) && file.type !== '') {
      return `File type ${file.type || 'unknown'} may not be supported.`;
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
        setExtractedContent(null);
      };

      const handleExtractContent = async (e) => {
        if (e) {
          preventFormNavigation(e);
        }
        if (!file || !authToken) return;
        setExtracting(true);
        setError('');
        setExtractedContent(null);
        try {
          const result = await api.extractFileContent(authToken, file);
          setExtractedContent(result);
        } catch (error) {
          setError(`Failed to extract content: ${error.message}`);
          setShowMessage(true);
        } finally {
          setExtracting(false);
        }
      };

      const handleUpload = async (e) => {
        if (e) {
          preventFormNavigation(e);
        }
        if (!file || !authToken) return;
        setUploading(true);
        setError('');
        try {
          if (!ALLOWED_TYPES.includes(file.type) && file.type !== '') {
            setMessage(`Warning: File type ${file.type || 'unknown'} may not be fully supported. Attempting to process...`);
            setShowMessage(true);
          }
          const result = await api.uploadFile(authToken, file);
          setMessage(`Successfully uploaded ${result.filename}`);
          setShowMessage(true);
          setTimeout(() => setShowMessage(false), 5000);
          setFile(null);
        } catch (error) {
          if (error.message.includes('codec') || error.message.includes('decode') || error.message.includes('encoding')) {
            setError('File encoding not supported. Please convert to UTF-8 or try a different file.');
          } else if (error.message.includes('Internal Server Error')) {
            setError('Server error processing file. The file format may not be supported.');
          } else {
            setError(error.message);
          }
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
              aria-label="Choose file to upload"
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
          <div className="file-upload-actions">
            <button
              type="button"
              onClick={handleUpload}
              disabled={!file || uploading || extracting || !authToken || !!error}
              className="upload-button"
              aria-busy={uploading}
            >
              {uploading ? 'Uploading...' : <><FiUpload /> Upload</>}
            </button>
            <button
              type="button"
              onClick={handleExtractContent}
              disabled={!file || uploading || extracting || !authToken || !!error}
              className="extract-button"
              aria-busy={extracting}
            >
              {extracting ? 'Extracting...' : <><FiEye /> View Content</>}
            </button>
          </div>
          {showMessage && (
            <div className={`upload-message ${error ? 'error' : 'success'}`} role="alert">
              {error || message}
            </div>
          )}
        {extractedContent && (
          <div className="extracted-content">
            <h3>Extracted Content from {extractedContent.filename}</h3>
            <div className="content-info">
              <p><strong>File type:</strong> {extractedContent.file_type}</p>
              <p><strong>File size:</strong> {Math.round(extractedContent.file_size / 1024)} KB</p>
              <p><strong>Content length:</strong> {extractedContent.content_length} characters</p>
              <p><strong>Detected encoding:</strong> {extractedContent.encoding_info?.encoding || 'Unknown'} (confidence: {Math.round((extractedContent.encoding_info?.confidence || 0) * 100)}%)</p>
            </div>
            <div className="content-preview">
              <h4>Content Preview:</h4>
              <pre>{extractedContent.content_preview}</pre>
            </div>
          </div>
        )}
      </div>
    );
}
