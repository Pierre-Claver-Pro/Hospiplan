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
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce soignant ?')) {
      await api.delete(`/soignants/${id}/`);
      fetchSoignants();
    }
  };

  const handleEdit = (s) => {
    setEditId(s.id);
    setForm({ nom: s.nom, prenom: s.prenom, specialite: s.specialite, phone_number: s.phone_number });
  };

  const handleCancel = () => {
    setEditId(null);
    setForm({ nom: '', prenom: '', specialite: '', phone_number: '' });
  };

  return (
    <div>
      <div className="form-container">
        <h2 className="form-title">
          <i className="fas fa-user-nurse"></i>
          {editId ? 'Modifier un soignant' : 'Ajouter un soignant'}
        </h2>

        {error && (
          <div className="alert alert-error">
            <i className="fas fa-exclamation-circle"></i>
            <span>{error}</span>
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="nom">Nom</label>
            <input
              id="nom"
              placeholder="Ex: Dupont"
              value={form.nom}
              onChange={e => setForm({...form, nom: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label htmlFor="prenom">Prénom</label>
            <input
              id="prenom"
              placeholder="Ex: Jean"
              value={form.prenom}
              onChange={e => setForm({...form, prenom: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label htmlFor="specialite">Spécialité</label>
            <input
              id="specialite"
              placeholder="Ex: Cardiologie"
              value={form.specialite}
              onChange={e => setForm({...form, specialite: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label htmlFor="phone">Téléphone</label>
            <input
              id="phone"
              type="tel"
              placeholder="Ex: +33612345678"
              value={form.phone_number}
              onChange={e => setForm({...form, phone_number: e.target.value})}
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

      {soignants.length === 0 ? (
        <div className="empty-state">
          <i className="fas fa-user-nurse"></i>
          <p>Aucun soignant trouvé. Commencez par en ajouter un !</p>
        </div>
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th><i className="fas fa-user"></i> Nom</th>
                <th><i className="fas fa-user"></i> Prénom</th>
                <th><i className="fas fa-stethoscope"></i> Spécialité</th>
                <th><i className="fas fa-phone"></i> Téléphone</th>
                <th><i className="fas fa-cogs"></i> Actions</th>
              </tr>
            </thead>
            <tbody>
              {soignants.map(s => (
                <tr key={s.id}>
                  <td>{s.nom}</td>
                  <td>{s.prenom}</td>
                  <td>{s.specialite}</td>
                  <td>{s.phone_number}</td>
                  <td>
                    <button className="btn btn-success btn-small" onClick={() => handleEdit(s)}>
                      <i className="fas fa-edit"></i> Modifier
                    </button>
                    <button className="btn btn-danger btn-small" onClick={() => handleDelete(s.id)}>
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