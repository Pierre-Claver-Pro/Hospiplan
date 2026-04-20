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
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce poste ?')) {
      await api.delete(`/postes/${id}/`);
      fetchPostes();
    }
  };

  const handleCancel = () => {
    setEditId(null);
    setForm({ type_garde: 'jour', date_debut: '', date_fin: '', min_soignants: 1 });
  };

  return (
    <div>
      <div className="form-container">
        <h2 className="form-title">
          <i className="fas fa-briefcase-medical"></i>
          {editId ? 'Modifier un poste' : 'Ajouter un poste de garde'}
        </h2>

        {error && (
          <div className="alert alert-error">
            <i className="fas fa-exclamation-circle"></i>
            <span>{error}</span>
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="type_garde">Type de garde</label>
            <select
              id="type_garde"
              value={form.type_garde}
              onChange={e => setForm({...form, type_garde: e.target.value})}
            >
              <option value="jour">Jour</option>
              <option value="nuit">Nuit</option>
              <option value="weekend">Weekend</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="date_debut">Date de début</label>
            <input
              id="date_debut"
              type="datetime-local"
              value={form.date_debut}
              onChange={e => setForm({...form, date_debut: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label htmlFor="date_fin">Date de fin</label>
            <input
              id="date_fin"
              type="datetime-local"
              value={form.date_fin}
              onChange={e => setForm({...form, date_fin: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label htmlFor="min_soignants">Soignants minimum</label>
            <input
              id="min_soignants"
              type="number"
              min="1"
              value={form.min_soignants}
              onChange={e => setForm({...form, min_soignants: e.target.value})}
            />
          </div>
        </div>

        <div className="button-group">
          <button className="btn btn-primary" onClick={handleSubmit}>
            <i className="fas fa-check"></i>
            {editId ? 'Modifier' : 'Ajouter'}
          </button>
          {editId && (
            <button className="btn btn-secondary" onClick={handleCancel}>
              <i className="fas fa-times"></i>
              Annuler
            </button>
          )}
        </div>
      </div>

      {postes.length === 0 ? (
        <div className="empty-state">
          <i className="fas fa-briefcase-medical"></i>
          <p>Aucun poste trouvé. Commencez par en ajouter un !</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th><i className="fas fa-clock"></i> Type</th>
                <th><i className="fas fa-calendar"></i> Début</th>
                <th><i className="fas fa-calendar"></i> Fin</th>
                <th><i className="fas fa-users"></i> Min soignants</th>
                <th><i className="fas fa-cogs"></i> Actions</th>
              </tr>
            </thead>
            <tbody>
              {postes.map(p => (
                <tr key={p.id}>
                  <td>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.3rem 0.8rem',
                      borderRadius: '20px',
                      fontSize: '0.85rem',
                      fontWeight: '600',
                      background: p.type_garde === 'jour' ? '#e0ffe0' : p.type_garde === 'nuit' ? '#e0e0ff' : '#ffe0e0',
                      color: p.type_garde === 'jour' ? '#2d5016' : p.type_garde === 'nuit' ? '#001680' : '#801010'
                    }}>
                      {p.type_garde.charAt(0).toUpperCase() + p.type_garde.slice(1)}
                    </span>
                  </td>
                  <td>{new Date(p.date_debut).toLocaleString('fr-FR')}</td>
                  <td>{new Date(p.date_fin).toLocaleString('fr-FR')}</td>
                  <td><strong>{p.min_soignants}</strong></td>
                  <td>
                    <button className="btn btn-danger btn-small" onClick={() => handleDelete(p.id)}>
                      <i className="fas fa-trash"></i> Supprimer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}