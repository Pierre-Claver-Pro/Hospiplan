import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Soignants from './pages/Soignants';
import Postes from './pages/Postes';
import Affectations from './pages/Affectations';

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ padding: '1rem', borderBottom: '1px solid #eee', display: 'flex', gap: '1rem' }}>
        <Link to="/">Soignants</Link>
        <Link to="/postes">Postes</Link>
        <Link to="/affectations">Affectations</Link>
      </nav>
      <div style={{ padding: '2rem' }}>
        <Routes>
          <Route path="/" element={<Soignants />} />
          <Route path="/postes" element={<Postes />} />
          <Route path="/affectations" element={<Affectations />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}