"""
PHASE 3 : Générateur de planning automatique

Pseudo-code & Implémentation de l'heuristique de génération
avec respect des contraintes dures et optimisation des molles.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from django.db.models import Count, Q, F
from django.utils import timezone

from .models import (
    Planning, Poste, Soignant, Affectation, AffectationPlanning,
    ScorePlanning, ConstrainteSouple, Absence, SoignantContrat
)
from .validators import validate_affectation


# ═══════════════════════════════════════════════════════════════
# HEURISTIQUE DE GÉNÉRATION : LEAST-LOADED
# ═══════════════════════════════════════════════════════════════

"""
PSEUDO-CODE DE L'HEURISTIQUE LEAST-LOADED

FONCTION generer_planning(start_date, end_date, algorithm='least-loaded')
  
  // Étape 1 : Récupérer tous les postes à couvrir
  postes_a_couvrir = SELECT * FROM Poste 
                     WHERE date_debut >= start_date 
                       AND date_fin <= end_date
  
  // Étape 2 : Créer un planning vide
  planning = Planning.create(start_date, end_date, status='generated')
  
  // Étape 3 : Trier les postes par priorité (nuits d'abord, puis urgences)
  postes_triés = TRIER(postes_a_couvrir, par=priorité)
  
  // Étape 4 : Pour chaque poste à couvrir
  pour chaque poste IN postes_triés faire
    soignants_eligibles = TROUVER_SOIGNANTS_LEGAUX(poste)
    
    // Étape 5 : Heuristique least-loaded
    //   Parmi les soignants légaux, choisir celui qui a MOINS de gardes
    //   Cela tend à équilibrer la charge (réduire écart-type)
    
    si soignants_eligibles.size() > 0 alors
      soignant = CHOISIR_LE_MOINS_CHARGE(soignants_eligibles, planning, periode)
      
      // Vérifier une dernière fois les contraintes dures
      si validate_affectation(soignant, poste) == OK alors
        CRÉER Affectation(soignant, poste)
        planning.affectations.ajouter(soignant, poste)
      sinon
        MARQUER poste comme non-couvert
      fin si
    sinon
      MARQUER poste comme impossible à couvrir (pas de personnel légal)
    fin si
  fin pour
  
  // Étape 6 : Calculer le score des contraintes molles
  score = CALCULER_SCORE_MOLLES(planning)
  planning.score_total = score.total
  planning.save()
  
  RETOURNER planning

FIN FONCTION
"""


class PlanningGeneratorError(Exception):
    """Exception levée lors d'erreurs de génération"""
    pass


class PlanningGenerator:
    """Générateur principal de plannings avec heuristique least-loaded"""
    
    def __init__(self, start_date, end_date, algorithm='least-loaded'):
        self.start_date = start_date
        self.end_date = end_date
        self.algorithm = algorithm
        self.planning = None
        self.eligible_soignants_cache = {}
        
    def generate(self, name=None):
        """
        Génère un planning pour la période [start_date, end_date].
        
        Returns:
            Planning: L'objet Planning créé avec toutes les affectations
            
        Raises:
            PlanningGeneratorError: Si la génération échoue
        """
        try:
            # Étape 1 : Récupérer tous les postes à couvrir
            postes = Poste.objects.filter(
                date_debut__date__gte=self.start_date,
                date_fin__date__lte=self.end_date
            ).order_by('type_garde', 'date_debut')  # Nuits en priorité
            
            if not postes.exists():
                raise PlanningGeneratorError(
                    f"Aucun poste trouvé pour la période {self.start_date} → {self.end_date}"
                )
            
            # Étape 2 : Créer le Planning
            self.planning = Planning.objects.create(
                name=name or f"Planning {self.start_date} → {self.end_date}",
                start_date=self.start_date,
                end_date=self.end_date,
                status='generated',
                generated_by_algorithm=self.algorithm
            )
            
            # Étape 3-5 : Pour chaque poste, appliquer l'heuristique
            uncovered_count = 0
            total_assignments = 0
            
            for poste in postes:
                # Trouver les soignants légaux pour ce poste
                soignants_legaux = self._find_eligible_soignants(poste)
                
                if soignants_legaux:
                    # Heuristique least-loaded : choisir le moins chargé
                    soignant = self._choose_least_loaded(soignants_legaux, poste)
                    
                    if soignant:
                        try:
                            # Créer l'affectation
                            AffectationPlanning.objects.create(
                                planning=self.planning,
                                soignant=soignant,
                                poste=poste,
                                is_manual=False
                            )
                            total_assignments += 1
                        except Exception as e:
                            uncovered_count += 1
                            print(f"⚠️  Échec affectation {soignant.nom} → {poste}: {e}")
                else:
                    uncovered_count += 1
            
            # Étape 6 : Calculer le score des contraintes molles
            score = self._compute_soft_constraints_score()
            self.planning.score_total = score['total']
            self.planning.save()
            
            # Créer le détail du score
            ScorePlanning.objects.create(
                planning=self.planning,
                penalty_night_consecutive=score.get('penalty_night_consecutive', 0),
                penalty_preferences=score.get('penalty_preferences', 0),
                penalty_workload_equity=score.get('penalty_workload_equity', 0),
                penalty_service_changes=score.get('penalty_service_changes', 0),
                penalty_weekend_equity=score.get('penalty_weekend_equity', 0),
                penalty_continuity=score.get('penalty_continuity', 0),
                total_shifts_assigned=total_assignments,
                uncovered_shifts=uncovered_count
            )
            
            return self.planning
            
        except Exception as e:
            if self.planning:
                self.planning.delete()
            raise PlanningGeneratorError(f"Erreur génération planning: {e}")
    
    
    def _find_eligible_soignants(self, poste):
        """
        Trouve tous les soignants qui PEUVENT occuper ce poste
        (respectent toutes les contraintes dures).
        
        Returns:
            list: Liste des Soignant légaux pour ce poste
        """
        soignants_valides = []
        all_soignants = Soignant.objects.filter(is_active=True) if hasattr(Soignant, 'is_active') else Soignant.objects.all()
        
        for soignant in all_soignants:
            # Vérifier TOUTES les contraintes dures
            is_valid, msg = validate_affectation(soignant, poste)
            if is_valid:
                soignants_valides.append(soignant)
        
        return soignants_valides
    
    
    def _choose_least_loaded(self, soignants, poste):
        """
        Heuristique LEAST-LOADED : choisir le soignant avec le moins de gardes
        dans ce planning pour cette période.
        
        Cela tend à équilibrer la charge et à réduire l'écart-type.
        
        Args:
            soignants (list): Liste de Soignant légaux
            poste (Poste): Le poste à couvrir
            
        Returns:
            Soignant: Le soignant le moins chargé, ou None
        """
        if not soignants:
            return None
        
        # Compter le nombre de gardes de chaque soignant dans ce planning
        charge = {}
        for soignant in soignants:
            count = AffectationPlanning.objects.filter(
                planning=self.planning,
                soignant=soignant
            ).count()
            charge[soignant.id] = count
        
        # Retourner le soignant avec le moins de gardes
        soignant_id = min(charge, key=charge.get)
        return next(s for s in soignants if s.id == soignant_id)
    
    
    def _compute_soft_constraints_score(self):
        """
        Calcule le score total des contraintes molles pour ce planning.
        
        Returns:
            dict: {
                'total': float,
                'penalty_night_consecutive': float,
                'penalty_preferences': float,
                'penalty_workload_equity': float,
                'penalty_service_changes': float,
                'penalty_weekend_equity': float,
                'penalty_continuity': float,
            }
        """
        penalties = {
            'penalty_night_consecutive': 0.0,
            'penalty_preferences': 0.0,
            'penalty_workload_equity': 0.0,
            'penalty_service_changes': 0.0,
            'penalty_weekend_equity': 0.0,
            'penalty_continuity': 0.0,
        }
        
        # Charger les poids des contraintes molles
        try:
            constraints = {c.constraint_type: c.weight for c in ConstrainteSouple.objects.filter(is_active=True)}
        except:
            constraints = {}
        
        # Contrainte 1 : Nuits consécutives
        if constraints.get('night_consecutive', 0) > 0:
            penalties['penalty_night_consecutive'] = self._compute_night_consecutive_penalty() * constraints.get('night_consecutive', 1.0)
        
        # Contrainte 2 : Préférences
        if constraints.get('preferences', 0) > 0:
            penalties['penalty_preferences'] = self._compute_preferences_penalty() * constraints.get('preferences', 1.0)
        
        # Contrainte 3 : Équité de charge
        if constraints.get('workload_equity', 0) > 0:
            penalties['penalty_workload_equity'] = self._compute_workload_equity_penalty() * constraints.get('workload_equity', 1.0)
        
        # Contrainte 4 : Changements de service
        if constraints.get('service_changes', 0) > 0:
            penalties['penalty_service_changes'] = self._compute_service_changes_penalty() * constraints.get('service_changes', 1.0)
        
        # Contrainte 5 : Équité week-ends
        if constraints.get('weekend_equity', 0) > 0:
            penalties['penalty_weekend_equity'] = self._compute_weekend_equity_penalty() * constraints.get('weekend_equity', 1.0)
        
        # Contrainte 6 : Continuité de soins
        if constraints.get('continuity', 0) > 0:
            penalties['penalty_continuity'] = self._compute_continuity_penalty() * constraints.get('continuity', 1.0)
        
        # Score total : somme des pénalités
        penalties['total'] = sum(penalties[k] for k in penalties if k != 'total')
        
        return penalties
    
    
    def _compute_night_consecutive_penalty(self):
        """
        Pénalité : plus de N nuits consécutives.
        Cherche les patterns de nuits consécutives et pénalise.
        """
        penalty = 0.0
        
        affectations = AffectationPlanning.objects.filter(
            planning=self.planning
        ).select_related('soignant', 'poste').order_by('soignant', 'poste__date_debut')
        
        # Grouper par soignant
        by_soignant = defaultdict(list)
        for aff in affectations:
            by_soignant[aff.soignant.id].append(aff)
        
        # Pour chaque soignant, détecter les nuits consécutives
        for soignant_id, affs in by_soignant.items():
            night_sequence = 0
            for aff in affs:
                if aff.poste.type_garde == 'nuit':
                    night_sequence += 1
                    if night_sequence > 3:  # Max 3 nuits consécutives
                        penalty += (night_sequence - 3) * 5.0  # 5 points par nuit en excès
                else:
                    night_sequence = 0
        
        return penalty
    
    
    def _compute_preferences_penalty(self):
        """
        Pénalité : préférences de créneaux non respectées.
        TODO: À implémenter quand F-07 (préférences) sera implémenté
        """
        # Placeholder - serait lié à PreferenceCreneauSoignant (à créer)
        return 0.0
    
    
    def _compute_workload_equity_penalty(self):
        """
        Pénalité : Charge inégale entre soignants.
        Calcule l'écart-type du nombre de gardes et le pénalise.
        """
        affectations = AffectationPlanning.objects.filter(
            planning=self.planning
        ).values('soignant').annotate(count=Count('id'))
        
        charges = [aff['count'] for aff in affectations]
        
        if len(charges) < 2:
            return 0.0
        
        # Écart-type : plus il est élevé, plus inégal est la charge
        std_dev = statistics.stdev(charges)
        
        # Transformer en pénalité (par exemple, écart-type * 10)
        return std_dev * 10.0
    
    
    def _compute_service_changes_penalty(self):
        """
        Pénalité : trop de changements de service dans une semaine.
        Cherche les changements de care_unit par soignant.
        """
        penalty = 0.0
        
        affectations = AffectationPlanning.objects.filter(
            planning=self.planning
        ).select_related('soignant', 'poste__care_unit').order_by('soignant', 'poste__date_debut')
        
        # Grouper par soignant
        by_soignant = defaultdict(list)
        for aff in affectations:
            by_soignant[aff.soignant.id].append(aff)
        
        # Compter les changements de service
        for soignant_id, affs in by_soignant.items():
            last_care_unit = None
            changes = 0
            for aff in affs:
                if aff.poste.care_unit and aff.poste.care_unit != last_care_unit:
                    if last_care_unit is not None:
                        changes += 1
                    last_care_unit = aff.poste.care_unit
            
            # Pénaliser chaque changement au-delà de 1 par semaine
            if changes > 1:
                penalty += (changes - 1) * 3.0  # 3 points par changement en excès
        
        return penalty
    
    
    def _compute_weekend_equity_penalty(self):
        """
        Pénalité : inégalité dans les week-ends travaillés.
        Compte les week-ends par soignant et pénalise l'inégalité.
        """
        affectations = AffectationPlanning.objects.filter(
            planning=self.planning
        ).select_related('soignant', 'poste')
        
        # Compter les week-ends par soignant
        weekend_counts = defaultdict(int)
        for aff in affectations:
            if aff.poste.type_garde == 'weekend':
                weekend_counts[aff.soignant.id] += 1
        
        counts = list(weekend_counts.values())
        
        if len(counts) < 2:
            return 0.0
        
        # Écart-type des week-ends
        std_dev = statistics.stdev(counts) if len(counts) > 1 else 0.0
        return std_dev * 8.0
    
    
    def _compute_continuity_penalty(self):
        """
        Pénalité : manque de continuité de soins.
        Favorise l'affectation du même soignant plusieurs jours consécutifs.
        TODO: À affiner quand les données de patients seront disponibles
        """
        # Placeholder - serait lié à des données de suivi de patients
        return 0.0


# ═══════════════════════════════════════════════════════════════
# FONCTIONS D'EXPORT & UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def generer_planning_simple(start_date, end_date, name=None):
    """
    Fonction simple pour générer un planning en une ligne.
    
    Args:
        start_date (date): Début de la période
        end_date (date): Fin de la période
        name (str, optional): Nom du planning
        
    Returns:
        Planning: Le planning généré
        
    Example:
        >>> from datetime import date
        >>> planning = generer_planning_simple(date(2025, 1, 6), date(2025, 1, 12))
    """
    generator = PlanningGenerator(start_date, end_date, algorithm='least-loaded')
    return generator.generate(name=name)


def get_planning_summary(planning_id):
    """
    Récupère un résumé textuel du planning.
    
    Returns:
        dict: Résumé formaté du planning
    """
    try:
        planning = Planning.objects.get(id=planning_id)
        score = ScorePlanning.objects.get(planning=planning)
        
        affectations = AffectationPlanning.objects.filter(planning=planning)
        
        return {
            'id': planning.id,
            'name': planning.name,
            'period': f"{planning.start_date} → {planning.end_date}",
            'status': planning.status,
            'total_assignments': affectations.count(),
            'total_score': planning.score_total,
            'score_detail': {
                'night_consecutive': score.penalty_night_consecutive,
                'preferences': score.penalty_preferences,
                'workload_equity': score.penalty_workload_equity,
                'service_changes': score.penalty_service_changes,
                'weekend_equity': score.penalty_weekend_equity,
                'continuity': score.penalty_continuity,
            },
            'uncovered_shifts': score.uncovered_shifts,
        }
    except Planning.DoesNotExist:
        return None
