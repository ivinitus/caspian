
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
        </div>
      </div>
    </header>
  );
}


