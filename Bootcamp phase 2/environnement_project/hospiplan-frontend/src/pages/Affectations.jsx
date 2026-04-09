import { useEffect, useState } from 'react';
import api from '../api/axios';

export default function Affectations() {
  const [soignants, setSoignants] = useState([]);
  const [postes, setPostes] = useState([]);
  const [soignantId, setSoignantId] = useState('');
  const [posteId, setPosteId] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    api.get('/soignants/').then(r => setSoignants(r.data));
    api.get('/postes/').then(r => setPostes(r.data));
  }, []);

  const handleSubmit = async () => {
    try {
      const r = await api.post('/affectations/', { soignant: soignantId, poste: posteId });
      setMessage('Affectation créée avec succès !');
      setIsError(false);
    } catch (e) {
      setMessage(e.response?.data?.error || 'Erreur inconnue');
      setIsError(true);
    }
  };

  return (
    <div>
      <h2>Créer une affectation</h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '400px' }}>
        <select value={soignantId} onChange={e => setSoignantId(e.target.value)}>
          <option value="">-- Choisir un soignant --</option>
          {soignants.map(s => (
            <option key={s.id} value={s.id}>{s.nom} {s.prenom}</option>
          ))}
        </select>

        <select value={posteId} onChange={e => setPosteId(e.target.value)}>
          <option value="">-- Choisir un poste --</option>
          {postes.map(p => (
            <option key={p.id} value={p.id}>{p.type_garde} — {new Date(p.date_debut).toLocaleString()}</option>
          ))}
        </select>

        <button onClick={handleSubmit}>Créer l'affectation</button>

        {message && (
          <p style={{ color: isError ? 'red' : 'green', fontWeight: '500' }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}