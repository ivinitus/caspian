import { AuthProvider } from './context/AuthContext';
import { Header } from './components/Header';
import { Chat } from './components/Chat';
import { AuthStatus } from './components/AuthStatus';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';

function AppContent() {
  return (
    <div className="app-container">
      <AuthStatus />
      <Header />
      <main className="main-content">
        <ErrorBoundary>
          <Chat />
        </ErrorBoundary>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;