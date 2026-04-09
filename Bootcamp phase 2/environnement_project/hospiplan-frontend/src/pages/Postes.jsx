import { useEffect, useState } from 'react';
import api from '../api/axios';

export default function Postes() {
  const [postes, setPostes] = useState([]);
  const [form, setForm] = useState({ type_garde: 'jour', date_debut: '', date_fin: '', min_soignants: 1 });
  const [editId, setEditId] = useState(null);
  const [error, setError] = useState('');

  const fetchPostes = () => api.get('/postes/').then(r => setPostes(r.data));
  useEffect(() => { fetchPostes(); }, []);

  const handleSubmit = async () => {
    try {
      if (editId) {
        await api.put(`/postes/${editId}/`, form);
        setEditId(null);
      } else {
        await api.post('/postes/', form);
      }
      setForm({ type_garde: 'jour', date_debut: '', date_fin: '', min_soignants: 1 });
      setError('');
      fetchPostes();
    } catch (e) {
      setError(JSON.stringify(e.response?.data));
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/postes/${id}/`);
    fetchPostes();
  };

  return (
    <div>
      <h2>Postes de garde</h2>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <select value={form.type_garde} onChange={e => setForm({...form, type_garde: e.target.value})}>
          <option value="jour">Jour</option>
          <option value="nuit">Nuit</option>
          <option value="weekend">Weekend</option>
        </select>
        <input type="datetime-local" value={form.date_debut} onChange={e => setForm({...form, date_debut: e.target.value})} />
        <input type="datetime-local" value={form.date_fin} onChange={e => setForm({...form, date_fin: e.target.value})} />
        <input type="number" placeholder="Min soignants" value={form.min_soignants} onChange={e => setForm({...form, min_soignants: e.target.value})} />
        <button onClick={handleSubmit}>{editId ? 'Modifier' : 'Ajouter'}</button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr><th>Type</th><th>Début</th><th>Fin</th><th>Min soignants</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {postes.map(p => (
            <tr key={p.id}>
              <td>{p.type_garde}</td>
              <td>{new Date(p.date_debut).toLocaleString()}</td>
              <td>{new Date(p.date_fin).toLocaleString()}</td>
              <td>{p.min_soignants}</td>
              <td>
                <button onClick={() => handleDelete(p.id)} style={{ color: 'red' }}>Supprimer</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}