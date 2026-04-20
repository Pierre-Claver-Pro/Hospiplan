import { useEffect, useState } from 'react';
import api from '../api/axios';

export default function Affectations() {
  const [soignants, setSoignants] = useState([]);
  const [postes, setPostes] = useState([]);
  const [affectations, setAffectations] = useState([]);
  const [soignantId, setSoignantId] = useState('');
  const [posteId, setPosteId] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const [loading, setLoading] = useState(false);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.get('/soignants/').then(r => setSoignants(r.data)),
      api.get('/postes/').then(r => setPostes(r.data)),
      api.get('/affectations/').then(r => setAffectations(r.data))
    ]).finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async () => {
    if (!soignantId || !posteId) {
      setMessage('Veuillez sélectionner un soignant et un poste');
      setIsError(true);
      return;
    }

    setLoading(true);
    try {
      await api.post('/affectations/', { soignant: soignantId, poste: posteId });
      setMessage('Affectation créée avec succès !');
      setIsError(false);
      setSoignantId('');
      setPosteId('');
      loadData(); // Recharger la liste
      setTimeout(() => setMessage(''), 3000);
    } catch (e) {
      setMessage(e.response?.data?.error || 'Erreur inconnue');
      setIsError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (affectationId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette affectation ?')) return;
    
    try {
      await api.delete(`/affectations/${affectationId}/`);
      setMessage('Affectation supprimée');
      setIsError(false);
      loadData();
    } catch (e) {
      setMessage(e.response?.data?.error || 'Erreur suppression');
      setIsError(true);
    }
  };

  const getSoignantName = (id) => {
    const s = soignants.find(s => s.id === parseInt(id));
    return s ? `${s.nom} ${s.prenom}` : '';
  };

  const getPosteInfo = (id) => {
    const p = postes.find(p => p.id === parseInt(id));
    return p ? `${p.type_garde} — ${new Date(p.date_debut).toLocaleString('fr-FR')}` : '';
  };

  return (
    <div>
      <div className="form-container" style={{ maxWidth: '600px' }}>
        <h2 className="form-title">
          <i className="fas fa-tasks"></i>
          Créer une affectation
        </h2>

        {message && (
          <div className={`alert ${isError ? 'alert-error' : 'alert-success'}`}>
            <i className={`fas ${isError ? 'fa-exclamation-circle' : 'fa-check-circle'}`}></i>
            <span>{message}</span>
          </div>
        )}

        <div className="form-group">
          <label htmlFor="soignant" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fas fa-user-nurse"></i>
            Choisir un soignant
          </label>
          <select
            id="soignant"
            value={soignantId}
            onChange={e => setSoignantId(e.target.value)}
            disabled={loading}
          >
            <option value="">-- Sélectionner un soignant --</option>
            {soignants.map(s => (
              <option key={s.id} value={s.id}>
                {s.nom} {s.prenom} ({s.specialite})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="poste" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <i className="fas fa-briefcase-medical"></i>
            Choisir un poste
          </label>
          <select
            id="poste"
            value={posteId}
            onChange={e => setPosteId(e.target.value)}
            disabled={loading}
          >
            <option value="">-- Sélectionner un poste --</option>
            {postes.map(p => (
              <option key={p.id} value={p.id}>
                {p.type_garde} — {new Date(p.date_debut).toLocaleString('fr-FR')} ({p.min_soignants} soignants min)
              </option>
            ))}
          </select>
        </div>

        {soignantId && posteId && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="card-body">
              <div className="card-label"><i className="fas fa-check"></i> Résumé de l'affectation</div>
              <div style={{ marginTop: '1rem' }}>
                <p><strong>Soignant:</strong> {getSoignantName(soignantId)}</p>
                <p><strong>Poste:</strong> {getPosteInfo(posteId)}</p>
              </div>
            </div>
          </div>
        )}

        <button
          className="btn btn-primary"
          onClick={handleSubmit}
          disabled={loading || !soignantId || !posteId}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {loading ? (
            <>
              <span className="loading"></span>
              Création en cours...
            </>
          ) : (
            <>
              <i className="fas fa-plus"></i>
              Créer l'affectation
            </>
          )}
        </button>
      </div>

      {/* Section affectations existantes */}
      <div className="form-container" style={{ marginTop: '2rem' }}>
        <h2 className="form-title">
          <i className="fas fa-list"></i>
          Affectations existantes
        </h2>

        {affectations.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#999' }}>
            Aucune affectation pour le moment
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              backgroundColor: '#fff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <thead>
                <tr style={{ backgroundColor: '#6366f1', borderBottom: '2px solid #4f46e5' }}>
                  <th style={{ padding: '1rem', textAlign: 'left', color: '#fff', fontWeight: '600' }}>Soignant</th>
                  <th style={{ padding: '1rem', textAlign: 'left', color: '#fff', fontWeight: '600' }}>Type de Garde</th>
                  <th style={{ padding: '1rem', textAlign: 'left', color: '#fff', fontWeight: '600' }}>Début</th>
                  <th style={{ padding: '1rem', textAlign: 'left', color: '#fff', fontWeight: '600' }}>Fin</th>
                  <th style={{ padding: '1rem', textAlign: 'center', color: '#fff', fontWeight: '600' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {affectations.map((aff) => {
                  const soignant = soignants.find(s => s.id === aff.soignant);
                  const poste = postes.find(p => p.id === aff.poste);
                  return (
                    <tr key={aff.id} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '1rem' }}>
                        {soignant ? `${soignant.nom} ${soignant.prenom}` : 'N/A'}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {poste && (
                          <span style={{
                            display: 'inline-block',
                            padding: '0.25rem 0.75rem',
                            borderRadius: '0.25rem',
                            backgroundColor: poste.type_garde === 'nuit' ? '#1e3a8a' : 
                                           poste.type_garde === 'weekend' ? '#be123c' : '#7c3aed',
                            color: '#fff',
                            fontSize: '0.875rem'
                          }}>
                            {poste.type_garde}
                          </span>
                        )}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {poste && new Date(poste.date_debut).toLocaleString('fr-FR')}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        {poste && new Date(poste.date_fin).toLocaleString('fr-FR')}
                      </td>
                      <td style={{ padding: '1rem', textAlign: 'center' }}>
                        <button
                          onClick={() => handleDelete(aff.id)}
                          style={{
                            padding: '0.5rem 1rem',
                            backgroundColor: '#dc2626',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '0.25rem',
                            cursor: 'pointer',
                            fontSize: '0.875rem'
                          }}
                          onMouseOver={(e) => e.target.style.backgroundColor = '#b91c1c'}
                          onMouseOut={(e) => e.target.style.backgroundColor = '#dc2626'}
                        >
                          <i className="fas fa-trash"></i> Supprimer
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}