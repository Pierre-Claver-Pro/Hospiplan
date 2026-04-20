import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import '../styles/Plannings.css';

/**
 * PHASE 3 : Page de génération et visualisation de plannings automatiques
 * 
 * Fonctionnalités :
 * - Afficher la liste des plannings générés
 * - Formulaire pour générer un nouveau planning
 * - Visualiser un planning avec toutes ses affectations
 * - Afficher le score des contraintes molles
 * - Modifier le planning manuellement (optionnel)
 */

export default function Plannings() {
  const [plannings, setPlannings] = useState([]);
  const [selectedPlanning, setSelectedPlanning] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);

  // État du formulaire de génération
  const [formData, setFormData] = useState({
    start_date: '',
    end_date: '',
    name: '',
    algorithm: 'least-loaded'
  });

  // Charger les plannings au montage
  useEffect(() => {
    loadPlannings();
  }, []);

  /**
   * Charge la liste de tous les plannings
   */
  const loadPlannings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/plannings/');
      setPlannings(response.data);
    } catch (err) {
      setError(`Erreur chargement plannings: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Charge les détails d'un planning spécifique
   */
  const loadPlanningDetail = async (planningId) => {
    try {
      setLoading(true);
      const response = await api.get(`/plannings/${planningId}/`);
      setSelectedPlanning(response.data);
    } catch (err) {
      setError(`Erreur chargement détail: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Envoie la requête de génération au backend
   */
  const handleGeneratePlanning = async (e) => {
    e.preventDefault();

    // Validation
    if (!formData.start_date || !formData.end_date) {
      setError('Veuillez remplir les dates start et end');
      return;
    }

    if (new Date(formData.start_date) >= new Date(formData.end_date)) {
      setError('La date de début doit être avant la date de fin');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // POST /plannings/generate
      const response = await api.post('/plannings/generate/', {
        start_date: formData.start_date,
        end_date: formData.end_date,
        name: formData.name || `Planning ${formData.start_date} → ${formData.end_date}`,
        algorithm: formData.algorithm
      });

      // Le planning a été généré avec succès
      console.log('✅ Planning généré:', response.data);
      
      // Rafraîchir la liste des plannings
      await loadPlannings();
      
      // Afficher le planning généré
      setSelectedPlanning(response.data);
      
      // Réinitialiser le formulaire
      setFormData({
        start_date: '',
        end_date: '',
        name: '',
        algorithm: 'least-loaded'
      });
      setShowForm(false);

    } catch (err) {
      if (err.response?.data?.error) {
        setError(`Erreur génération: ${err.response.data.error}`);
      } else {
        setError(`Erreur: ${err.message}`);
      }
      console.error('Erreur génération planning:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Met à jour un champ du formulaire
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  /**
   * Supprime un planning
   */
  const handleDeletePlanning = async (planningId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce planning ? Cette action est irréversible.')) {
      return;
    }

    try {
      setLoading(true);
      await api.delete(`/plannings/${planningId}/`);
      setError(null);
      setSelectedPlanning(null); // Fermer la vue détail si elle était ouverte
      loadPlannings(); // Rafraîchir la liste
    } catch (err) {
      setError(`Erreur suppression planning: ${err.response?.data?.error || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Affiche un planning avec sa liste d'affectations et son score
   */
  const renderPlanningDetail = () => {
    if (!selectedPlanning) return null;

    const { name, start_date, end_date, status, score_total, affectations, score_detail, generated_by_algorithm } = selectedPlanning;

    return (
      <div className="planning-detail">
        <h2>{name}</h2>
        
        <div className="planning-info">
          <p><strong>Période :</strong> {start_date} → {end_date}</p>
          <p><strong>Statut :</strong> <span className={`status ${status}`}>{status}</span></p>
          <p><strong>Algorithme :</strong> {generated_by_algorithm}</p>
        </div>

        {/* Score Global */}
        <div className="score-section">
          <h3>📊 Score des Contraintes Molles</h3>
          <div className="score-total">
            <div className="score-value">{score_total.toFixed(2)}</div>
            <p className="score-label">(Plus bas = Mieux)</p>
          </div>

          {score_detail && (
            <div className="score-breakdown">
              <h4>Détail des pénalités :</h4>
              <ul>
                <li>🌙 Nuits consécutives : <span className="penalty">{score_detail.penalty_night_consecutive.toFixed(2)}</span></li>
                <li>👤 Préférences : <span className="penalty">{score_detail.penalty_preferences.toFixed(2)}</span></li>
                <li>⚖️ Équité charge : <span className="penalty">{score_detail.penalty_workload_equity.toFixed(2)}</span></li>
                <li>🔄 Changements service : <span className="penalty">{score_detail.penalty_service_changes.toFixed(2)}</span></li>
                <li>📅 Équité week-ends : <span className="penalty">{score_detail.penalty_weekend_equity.toFixed(2)}</span></li>
                <li>🏥 Continuité soins : <span className="penalty">{score_detail.penalty_continuity.toFixed(2)}</span></li>
              </ul>
              <p className="coverage-info">
                ✅ Affectations : {score_detail.total_shifts_assigned} | 
                ⚠️ Postes non couverts : {score_detail.uncovered_shifts}
              </p>
            </div>
          )}
        </div>

        {/* Liste des Affectations */}
        <div className="affectations-section">
          <h3>📋 Affectations ({affectations.length})</h3>
          {affectations.length === 0 ? (
            <p className="no-data">Aucune affectation pour cette période</p>
          ) : (
            <div className="affectations-table">
              <table>
                <thead>
                  <tr>
                    <th>Soignant</th>
                    <th>Type de Garde</th>
                    <th>Début</th>
                    <th>Fin</th>
                    <th>Unité</th>
                    <th>Modifié</th>
                  </tr>
                </thead>
                <tbody>
                  {affectations.map((aff, idx) => (
                    <tr key={idx}>
                      <td>{aff.soignant_nom}</td>
                      <td><span className={`badge ${aff.poste_detail.type_garde}`}>
                        {aff.poste_detail.type_garde}
                      </span></td>
                      <td>{new Date(aff.poste_detail.date_debut).toLocaleString()}</td>
                      <td>{new Date(aff.poste_detail.date_fin).toLocaleString()}</td>
                      <td>{aff.poste_detail.care_unit || '-'}</td>
                      <td>{aff.is_manual ? '✏️ Oui' : 'Non'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="actions">
          <button 
            className="btn btn-secondary"
            onClick={() => setSelectedPlanning(null)}
          >
            ← Retour à la liste
          </button>
          <button 
            className="btn btn-danger"
            onClick={() => handleDeletePlanning(selectedPlanning.id)}
            style={{ backgroundColor: '#dc2626', color: '#fff' }}
          >
            🗑️ Supprimer ce planning
          </button>
        </div>
      </div>
    );
  };

  /**
   * Affiche la liste des plannings
   */
  const renderPlanningsList = () => {
    if (plannings.length === 0) {
      return <p className="no-data">Aucun planning généré. Créez le premier ! 🎯</p>;
    }

    return (
      <div className="plannings-table">
        <table>
          <thead>
            <tr>
              <th>Nom</th>
              <th>Période</th>
              <th>Statut</th>
              <th>Score</th>
              <th>Généré le</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {plannings.map((planning) => (
              <tr key={planning.id}>
                <td><strong>{planning.name}</strong></td>
                <td>{planning.start_date} → {planning.end_date}</td>
                <td><span className={`status ${planning.status}`}>{planning.status}</span></td>
                <td>
                  <span className={`score ${planning.score_total > 50 ? 'high' : 'low'}`}>
                    {planning.score_total.toFixed(2)}
                  </span>
                </td>
                <td>{new Date(planning.generated_at).toLocaleDateString()}</td>
                <td>
                  <button 
                    className="btn btn-small"
                    onClick={() => loadPlanningDetail(planning.id)}
                    style={{ marginRight: '0.5rem' }}
                  >
                    Voir détail →
                  </button>
                  <button 
                    className="btn btn-small"
                    onClick={() => handleDeletePlanning(planning.id)}
                    style={{ backgroundColor: '#dc2626', color: '#fff' }}
                    onMouseOver={(e) => e.target.style.backgroundColor = '#b91c1c'}
                    onMouseOut={(e) => e.target.style.backgroundColor = '#dc2626'}
                  >
                    🗑️ Supprimer
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  /**
   * Formulaire de génération
   */
  const renderGenerationForm = () => {
    return (
      <form className="generation-form" onSubmit={handleGeneratePlanning}>
        <h3>🤖 Générer un nouveau Planning</h3>
        
        <div className="form-group">
          <label htmlFor="start_date">Date de début *</label>
          <input
            type="date"
            id="start_date"
            name="start_date"
            value={formData.start_date}
            onChange={handleInputChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="end_date">Date de fin *</label>
          <input
            type="date"
            id="end_date"
            name="end_date"
            value={formData.end_date}
            onChange={handleInputChange}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="name">Nom du planning (optionnel)</label>
          <input
            type="text"
            id="name"
            name="name"
            placeholder="ex: Planning Semaine 1"
            value={formData.name}
            onChange={handleInputChange}
          />
        </div>

        <div className="form-group">
          <label htmlFor="algorithm">Algorithme</label>
          <select
            id="algorithm"
            name="algorithm"
            value={formData.algorithm}
            onChange={handleInputChange}
          >
            <option value="least-loaded">Least-Loaded (recommandé)</option>
          </select>
          <small>Heuristique : affecter d'abord les soignants les moins chargés</small>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-success" disabled={loading}>
            {loading ? '⏳ Génération en cours...' : '✨ Générer le Planning'}
          </button>
          <button 
            type="button" 
            className="btn btn-secondary"
            onClick={() => setShowForm(false)}
          >
            Annuler
          </button>
        </div>
      </form>
    );
  };

  // Rendu principal
  return (
    <div className="plannings-container">
      <div className="plannings-header">
        <h1>📅 Génération Automatique de Plannings - Phase 3</h1>
        <p className="subtitle">Générez des plannings optimisés en respectant les contraintes légales et RH</p>
      </div>

      {error && (
        <div className="alert alert-error">
          ❌ {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {loading && (
        <div className="alert alert-info">
          ⏳ Chargement en cours...
        </div>
      )}

      {selectedPlanning ? (
        renderPlanningDetail()
      ) : (
        <>
          {showForm && renderGenerationForm()}
          
          {!showForm && (
            <button 
              className="btn btn-primary btn-large"
              onClick={() => setShowForm(true)}
            >
              + Générer un nouveau Planning
            </button>
          )}

          <div className="plannings-list-section">
            <h2>📊 Plannings existants</h2>
            {renderPlanningsList()}
          </div>
        </>
      )}
    </div>
  );
}
