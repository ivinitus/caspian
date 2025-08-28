import { FiSettings, FiBook } from 'react-icons/fi';
import { FileUpload } from './FileUpload';
import './Header.css';

export function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <h1>Caspian</h1>
          <span className="logo-subtitle">WEB</span>
        </div>
        
        <div className="header-actions">
          <FileUpload />
          
          <div className="header-buttons">
            <button className="header-button">
              <FiBook />
              <span className="button-text">SUMMARY</span>
            </button>
            <button className="header-button">
              <FiSettings />
              <span className="button-text">Settings</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
