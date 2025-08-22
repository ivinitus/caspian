/**
 * API service for communicating with the backend
 */

// Use an absolute URL for API requests
// If your backend expects /api to be included in the URL path, keep it as '/api'
// If your backend API is at the root (no /api prefix), use '' (empty string)
const API_URL = '/api';
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

/**
 * Wrapper function to handle retries and consistent error handling
 */
async function fetchWithRetry(url, options, retries = MAX_RETRIES) {
  console.log(`API Request: ${options.method} ${url}`, options);
  
  try {
    const response = await fetch(url, options);
    console.log(`API Response status: ${response.status} ${response.statusText}`);
    
    // Handle rate limiting (429)
    if (response.status === 429 && retries > 0) {
      console.log(`Rate limited, retrying in ${RETRY_DELAY}ms...`);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return fetchWithRetry(url, options, retries - 1);
    }
    
    // Handle unauthorized (401) - could trigger a refresh token flow
    if (response.status === 401) {
      console.error('Unauthorized request (401):', url);
      // In a real app, you might refresh the token here
      throw new Error('Session expired. Please log in again.');
    }
    
    // Handle other error responses
    if (!response.ok) {
      try {
        const errorData = await response.json();
        console.error(`API Error (${response.status}):`, errorData);
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      } catch (jsonError) {
        // If we can't parse the error as JSON, use text
        const errorText = await response.text().catch(() => 'Unknown error');
        console.error(`API Error (${response.status}), couldn't parse JSON:`, errorText);
        throw new Error(`Request failed with status ${response.status}: ${errorText.slice(0, 100)}`);
      }
    }
    
    return response;
  } catch (error) {
    // Handle network errors with retry
    if (error.name === 'TypeError' && error.message.includes('network') && retries > 0) {
      console.log(`Network error, retrying in ${RETRY_DELAY}ms...`, error);
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
      return fetchWithRetry(url, options, retries - 1);
    }
    
    console.error('Fetch error:', error);
    throw error;
  }
}

export const api = {
  /**
   * Authenticate with the server and get a token
   */
  authenticate: async (username) => {
    const response = await fetchWithRetry(`${API_URL}/auth/token/from-username`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username }),
    });
    
    const data = await response.json();
    return data.access_token;
  },
  
  /**
   * Start a new conversation
   */
  startConversation: async (token, username) => {
    const response = await fetchWithRetry(`${API_URL}/conversations/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ username }),
    });
    
    return await response.json();
  },
  
  /**
   * Send a message to the conversation
   */
  sendMessage: async (token, conversationId, content, sender) => {
    const response = await fetchWithRetry(`${API_URL}/conversations/${conversationId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content, sender }),
    });
    
    return await response.json();
  },
  
  /**
   * Get a response from the LLM
   */
  getChatResponse: async (token, messages) => {
    console.log('API: Sending chat request with messages:', messages);
    try {
      const response = await fetchWithRetry(`${API_URL}/llm/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ 
          messages: messages.map(({role, content}) => ({role, content})) 
        }),
      });
      
      const data = await response.json();
      console.log('API: LLM response data:', data);
      
      // Handle different response formats
      if (typeof data === 'string') {
        return { text: data };
      } else if (data && typeof data === 'object') {
        // The API might return different formats, try to normalize
        return {
          text: data.text || data.content || data.message || data.response || 
                (data.choices && data.choices[0] && 
                 (data.choices[0].text || data.choices[0].message?.content)) ||
                "Sorry, I couldn't process that request."
        };
      } else {
        console.error('API: Unexpected response format from LLM:', data);
        return { text: "Sorry, I received an unexpected response format." };
      }
    } catch (error) {
      console.error('API: Error in getChatResponse:', error);
      throw error;
    }
  },
  
    /**
 * Upload a file for RAG
 */
uploadFile: async (token, file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    console.log(`Uploading file: ${file.name}, type: ${file.type}, size: ${file.size} bytes`);
    
    const response = await fetchWithRetry(`${API_URL}/rag/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    const result = await response.json();
    
    // Check for expected response structure
    if (!result.filename) {
      console.error('Unexpected upload response format:', result);
      throw new Error('Upload failed: Invalid server response');
    }
    
    return result;
  } catch (error) {
    console.error('File upload error details:', error);
    
    // Convert abort errors to more user-friendly messages
    if (error.name === 'AbortError') {
      throw new Error('Upload timed out. Please try again with a smaller file or check your connection.');
    }
    
    // Handle encoding errors
    if (error.message.includes('codec') || error.message.includes('decode') || error.message.includes('utf-8')) {
      throw new Error('File encoding not supported. Please convert to UTF-8 or try a different file format.');
    }
    
    // Handle other specific upload errors
    if (error.message.includes('413') || error.message.includes('Payload Too Large')) {
      throw new Error('File is too large for the server to process.');
    }
    
    if (error.message.includes('500') || error.message.includes('Internal Server Error')) {
      throw new Error('Server could not process this file. The format may be unsupported.');
    }
    
    // Rethrow the original error with upload context
    throw new Error(`File upload failed: ${error.message}`);
  }
},

/**
 * Extract content from a file without storing it (diagnostic endpoint)
 */
extractFileContent: async (token, file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
    
    console.log(`Extracting content from file: ${file.name}, type: ${file.type}, size: ${file.size} bytes`);
    
    const response = await fetchWithRetry(`${API_URL}/rag/extract-content`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('File content extraction error:', error);
    throw new Error(`Content extraction failed: ${error.message}`);
  }
}
};
