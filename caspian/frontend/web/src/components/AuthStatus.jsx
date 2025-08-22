import { FiAlertCircle, FiRefreshCw, FiCheckCircle, FiClock } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';
import './AuthStatusStyles.css';

export function AuthStatus() {
  const { loading, error, authStatus, refreshSession } = useAuth();
  
  if (!loading && !error && authStatus === 'authenticated') return null;
  
  const handleRefresh = async () => {
    try {
      await refreshSession();
    } catch (error) {
      console.error('Failed to refresh session:', error);
    }
  };
  
  return (
    <div className={`auth-status ${getStatusClass(authStatus, error)}`}>
      {loading ? (
        <>
          <div className="auth-loader"></div>
          <span>Connecting to Caspian...</span>
        </>
      ) : error ? (
        <>
          <FiAlertCircle className="status-icon" />
          <span>Connection error: {error}</span>
          <button className="refresh-button" onClick={handleRefresh}>
            <FiRefreshCw />
            Retry
          </button>
        </>
      ) : authStatus === 'expired' ? (
        <>
          <FiClock className="status-icon" />
          <span>Session expired. Reconnecting...</span>
          <button className="refresh-button" onClick={handleRefresh}>
            <FiRefreshCw />
            Reconnect
          </button>
        </>
      ) : authStatus === 'authenticated' ? (
        <>
          <FiCheckCircle className="status-icon" />
          <span>Connected to Caspian</span>
        </>
      ) : (
        <>
          <FiAlertCircle className="status-icon" />
          <span>Connecting to Caspian...</span>
          <button className="refresh-button" onClick={handleRefresh}>
            <FiRefreshCw />
            Connect
          </button>
        </>
      )}
    </div>
  );
}

function getStatusClass(status, error) {
  if (error) return 'error';
  switch (status) {
    case 'authenticated': return 'success';
    case 'expired': return 'warning';
    case 'unauthenticated': return 'error';
    default: return 'loading';
  }
}
