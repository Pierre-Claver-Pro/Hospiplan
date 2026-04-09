import { useEffect, useState } from 'react';
import api from '../api/axios';

export default function Soignants() {
  const [soignants, setSoignants] = useState([]);
  const [form, setForm] = useState({ nom: '', prenom: '', specialite: '', phone_number: '' });
  const [editId, setEditId] = useState(null);
  const [error, setError] = useState('');

  const fetchSoignants = () => api.get('/soignants/').then(r => setSoignants(r.data));

  useEffect(() => { fetchSoignants(); }, []);

  const handleSubmit = async () => {
    try {
      if (editId) {
        await api.put(`/soignants/${editId}/`, form);
        setEditId(null);
      } else {
        await api.post('/soignants/', form);
      }
      setForm({ nom: '', prenom: '', specialite: '', phone_number: '' });
      setError('');
      fetchSoignants();
    } catch (e) {
      setError(JSON.stringify(e.response?.data));
    }
  };

  const handleDelete = async (id) => {
    await api.delete(`/soignants/${id}/`);
    fetchSoignants();
  };

  const handleEdit = (s) => {
    setEditId(s.id);
    setForm({ nom: s.nom, prenom: s.prenom, specialite: s.specialite, phone_number: s.phone_number });
  };

  return (
    <div>
      <h2>Soignants</h2>

      {/* Formulaire */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <input placeholder="Nom" value={form.nom} onChange={e => setForm({...form, nom: e.target.value})} />
        <input placeholder="Prénom" value={form.prenom} onChange={e => setForm({...form, prenom: e.target.value})} />
        <input placeholder="Spécialité" value={form.specialite} onChange={e => setForm({...form, specialite: e.target.value})} />
        <input placeholder="Téléphone" value={form.phone_number} onChange={e => setForm({...form, phone_number: e.target.value})} />
        <button onClick={handleSubmit}>{editId ? 'Modifier' : 'Ajouter'}</button>
        {editId && <button onClick={() => { setEditId(null); setForm({ nom: '', prenom: '', specialite: '', phone_number: '' }); }}>Annuler</button>}
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {/* Liste */}
      <table border="1" cellPadding="8" style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr><th>Nom</th><th>Prénom</th><th>Spécialité</th><th>Téléphone</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {soignants.map(s => (
            <tr key={s.id}>
              <td>{s.nom}</td>
              <td>{s.prenom}</td>
              <td>{s.specialite}</td>
              <td>{s.phone_number}</td>
              <td>
                <button onClick={() => handleEdit(s)}>Modifier</button>
                <button onClick={() => handleDelete(s.id)} style={{ marginLeft: '8px', color: 'red' }}>Supprimer</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}