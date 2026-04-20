import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Soignants from './pages/Soignants';
import Postes from './pages/Postes';
import Affectations from './pages/Affectations';
import Plannings from './pages/Plannings';
import './App.css';

function Navigation() {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <i className="fas fa-hospital"></i> HospiPlan
        </Link>
        <div className="navbar-menu">
          <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
            <i className="fas fa-user-nurse"></i> Soignants
          </Link>
          <Link to="/postes" className={`nav-link ${isActive('/postes') ? 'active' : ''}`}>
            <i className="fas fa-briefcase-medical"></i> Postes
          </Link>
          <Link to="/affectations" className={`nav-link ${isActive('/affectations') ? 'active' : ''}`}>
            <i className="fas fa-tasks"></i> Affectations
          </Link>
          <Link to="/plannings" className={`nav-link ${isActive('/plannings') ? 'active' : ''}`}>
            <i className="fas fa-calendar-check"></i> Plannings (Phase 3)
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Soignants />} />
            <Route path="/postes" element={<Postes />} />
            <Route path="/affectations" element={<Affectations />} />
            <Route path="/plannings" element={<Plannings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}