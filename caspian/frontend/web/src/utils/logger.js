/**
 * Logger utility to capture and report errors
 */

// Define error severity levels
export const LogLevel = {
  INFO: 'info',
  WARNING: 'warning',
  ERROR: 'error',
  CRITICAL: 'critical'
};

// In-memory log storage
const logs = [];
const MAX_LOGS = 100;

/**
 * Log an error or message with metadata
 * @param {string} message - Error message or information
 * @param {object} metadata - Additional data about the error (optional)
 * @param {string} level - Severity level (from LogLevel enum)
 */
export const logEvent = (message, metadata = {}, level = LogLevel.INFO) => {
  const logEntry = {
    timestamp: new Date().toISOString(),
    message,
    level,
    metadata: {
      ...metadata,
      userAgent: navigator.userAgent,
      url: window.location.href
    }
  };
  
  // Add to in-memory logs (with limit to prevent memory leaks)
  logs.unshift(logEntry);
  if (logs.length > MAX_LOGS) {
    logs.pop();
  }
  
  // Log to console
  const consoleMethod = level === LogLevel.ERROR || level === LogLevel.CRITICAL 
    ? console.error 
    : (level === LogLevel.WARNING ? console.warn : console.log);
  
  consoleMethod(`[${level.toUpperCase()}] ${message}`, metadata);
  
  // You could send to a server or analytics here
  // For critical errors, you might want to report immediately
  if (level === LogLevel.CRITICAL) {
    reportCriticalError(logEntry);
  }
};

/**
 * Log network failures specifically
 * @param {Error} error - The network error
 * @param {object} requestDetails - Information about the failed request
 */
export const logNetworkFailure = (error, requestDetails) => {
  logEvent(
    `Network failure: ${error.message}`,
    {
      error: error.toString(),
      stack: error.stack,
      request: requestDetails
    },
    LogLevel.ERROR
  );
};

/**
 * Report a critical error to a monitoring service
 * @param {object} logEntry - The log entry to report
 */
const reportCriticalError = (logEntry) => {
  // In a real app, you would send this to a monitoring service
  // This is a placeholder for actual implementation
  console.error('CRITICAL ERROR REPORTED:', logEntry);
  
  // Example of reporting to a hypothetical API endpoint
  /*
  fetch('/api/error-reporting', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(logEntry)
  }).catch(err => {
    console.error('Failed to report critical error:', err);
  });
  */
};

/**
 * Get all logged events
 * @returns {Array} - Array of log entries
 */
export const getAllLogs = () => [...logs];

/**
 * Clear all logged events
 */
export const clearLogs = () => {
  logs.length = 0;
};

/**
 * Monitor unhandled errors and rejections globally
 */
export const setupGlobalErrorMonitoring = () => {
  window.addEventListener('error', (event) => {
    logEvent(
      `Unhandled error: ${event.message || 'Unknown error'}`,
      {
        error: event.error?.toString(),
        stack: event.error?.stack,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      },
      LogLevel.CRITICAL
    );
    
    // Don't prevent default so browser console still shows the error
  });
  
  window.addEventListener('unhandledrejection', (event) => {
    logEvent(
      `Unhandled promise rejection: ${event.reason?.message || 'Unknown reason'}`,
      {
        reason: event.reason?.toString(),
        stack: event.reason?.stack
      },
      LogLevel.CRITICAL
    );
  });
};
