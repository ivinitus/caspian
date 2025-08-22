import { useState } from 'react';
import { FiUser, FiUpload, FiSettings, FiBook, FiLogOut } from 'react-icons/fi';
import { FileUpload } from './FileUpload';
import { useAuth } from '../context/AuthContext';
import './Header.css';

export function Header() {
  const { logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <h1>Caspian</h1>
          <span className="logo-subtitle">AI Assistant</span>
        </div>
        
        <div className="header-actions">
          <FileUpload />
          
          <div className="header-buttons">
            <button className="header-button">
              <FiBook />
              <span className="button-text">Knowledge</span>
            </button>
            <button className="header-button">
              <FiSettings />
              <span className="button-text">Settings</span>
            </button>
            <div className="user-menu-container">
              <button 
                className="header-button user"
                onClick={() => setShowUserMenu(!showUserMenu)}
                aria-expanded={showUserMenu}
                aria-haspopup="true"
              >
                <FiUser />
                <span className="button-text">Sir</span>
              </button>
              
              {showUserMenu && (
                <div className="user-menu">
                  <button 
                    className="user-menu-item"
                    onClick={handleLogout}
                  >
                    <FiLogOut />
                    <span>Logout</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
