"""
Validateurs des Contraintes Dures - Phase 2 HospiPlan

Chaque fonction valide UNE contrainte dure et retourne:
  (is_valid: bool, message: str)
  
Ces fonctions sont appelées avant de créer une affectation.
"""

from datetime import timedelta
from django.db.models import Q
from .models import (
    Soignant, Poste, Affectation, Absence,
    SoignantCertification, SoignantContrat
)

# Configurable en base pour F-10 (règles légales configurables)
REPOS_MINIMAL_HEURES = 11
HEURES_MAX_PAR_SEMAINE = 35


def validate_no_overlap(soignant, poste_a_affecter):
    """
    CONTRAINTE 1 : PAS DE CHEVAUCHEMENT HORAIRE
    
    Pseudo-code:
      POUR chaque affectation existante du soignant
        SI (affectation.poste.date_fin > poste_a_affecter.date_debut) ET 
           (affectation.poste.date_debut < poste_a_affecter.date_fin)
          RETOURNER (False, "Chevauchement détecté")
      RETOURNER (True, "")
    """
    affectations_existantes = Affectation.objects.filter(soignant=soignant)
    
    for affectation in affectations_existantes:
        # Vérifier si les plages horaires se chevauchent
        if (affectation.poste.date_fin > poste_a_affecter.date_debut and 
            affectation.poste.date_debut < poste_a_affecter.date_fin):
            return (
                False,
                f"Chevauchement horaire : {affectation.poste.date_debut} - {affectation.poste.date_fin}"
            )
    
    return (True, "")


def validate_required_certifications(soignant, poste):
    """
    CONTRAINTE 2 : CERTIFICATIONS REQUISES NON EXPIRÉES
    
    Pseudo-code:
      certs_requises = SELECT * FROM PosteCertificationRequise WHERE poste_id = poste.id
      POUR chaque cert_requise
        possession = SELECT * FROM SoignantCertification 
                   WHERE soignant_id = soignant.id 
                     AND certification_id = cert_requise.certification_id
                     AND (expiration_date IS NULL OR expiration_date >= poste.date_debut)
        SI possession n'existe pas
          RETOURNER (False, f"Certification manquante : {cert_requise}")
      RETOURNER (True, "")
    """
    certs_requises = poste.certifications_requises.all()
    
    for poste_cert in certs_requises:
        cert = poste_cert.certification
        date_poste = poste.date_debut.date()
        
        # Vérifier si le soignant possède la certification ET qu'elle n'est pas expirée
        possede = SoignantCertification.objects.filter(
            soignant=soignant,
            certification=cert,
            obtained_date__lte=date_poste,  # Obtenue avant le poste
        ).filter(
            # Pas d'expiration OU expiration après la date du poste
        ).exclude(
            expiration_date__lt=date_poste  # Exclure si déjà expirée
        ).exists()
        
        if not possede:
            return (
                False,
                f"Certification manquante ou expirée : {cert.name}"
            )
    
    return (True, "")


def validate_minimal_rest_after_night_shift(soignant, poste):
    """
    CONTRAINTE 3 : REPOS MINIMAL APRÈS GARDE DE NUIT
    
    Pseudo-code:
      SI poste.type_garde != 'nuit'
        derniere_nuit = SELECT * FROM Affectation 
                       WHERE soignant_id = soignant.id 
                         AND poste.type_garde = 'nuit'
                         AND poste.date_fin <= poste_a_affecter.date_debut
                       ORDER BY poste.date_fin DESC LIMIT 1
        SI derniere_nuit existe
          delta_heures = (poste_a_affecter.date_debut - derniere_nuit.poste.date_fin).heures
          SI delta_heures < REPOS_MINIMAL_HEURES
            RETOURNER (False, f"Repos minimal de {REPOS_MINIMAL_HEURES}h non respecté")
      RETOURNER (True, "")
    """
    # Ne vérifier que si le nouveau poste n'est PAS une nuit
    # (on ignore le repos après une nuit si la prochaine est aussi une nuit)
    
    derniere_nuit = Affectation.objects.filter(
        soignant=soignant,
        poste__type_garde='nuit',
        poste__date_fin__lte=poste.date_debut
    ).order_by('-poste__date_fin').first()
    
    if derniere_nuit:
        delta = poste.date_debut - derniere_nuit.poste.date_fin
        if delta < timedelta(hours=REPOS_MINIMAL_HEURES):
            return (
                False,
                f"Repos minimal de {REPOS_MINIMAL_HEURES}h après garde de nuit non respecté"
            )
    
    return (True, "")


def validate_no_declared_absence(soignant, poste):
    """
    CONTRAINTE 4 : SOIGNANT NE PAS EN ABSENCE
    
    Pseudo-code:
      absence = SELECT * FROM Absence 
               WHERE soignant_id = soignant.id 
                 AND start_date <= poste.date_debut 
                 AND (actual_end_date IS NULL OR actual_end_date >= poste.date_debut)
      SI absence existe
        RETOURNER (False, f"Soignant en absence : {absence.raison}")
      RETOURNER (True, "")
    """
    date_poste = poste.date_debut.date()
    
    absence = Absence.objects.filter(
        soignant=soignant,
        start_date__lte=date_poste,
        expected_end_date__gte=date_poste
    ).first()
    
    if absence:
        return (
            False,
            f"Soignant en absence déclarée du {absence.start_date} au {absence.expected_end_date}"
        )
    
    return (True, "")


def validate_contract_allows_shift_type(soignant, poste):
    """
    CONTRAINTE 5 : CONTRAT AUTORISE LE TYPE DE GARDE
    
    Pseudo-code:
      date_poste = poste.date_debut
      contrat_actif = SELECT * FROM SoignantContrat 
                     WHERE soignant_id = soignant.id 
                       AND start_date <= date_poste 
                       AND (end_date IS NULL OR end_date >= date_poste)
      SI contrat_actif n'existe pas
        RETOURNER (False, "Aucun contrat actif")
      
      SI poste.type_garde == 'nuit' ET contrat_actif.contract_type.night_shift_allowed == False
        RETOURNER (False, "Contrat n'autorise pas les gardes de nuit")
      
      RETOURNER (True, "")
    """
    date_poste = poste.date_debut.date()
    
    # Trouver le contrat actif à la date du poste
    contrat_actif = SoignantContrat.objects.filter(
        soignant=soignant,
        start_date__lte=date_poste,
    ).filter(
        # end_date null = contrat toujours actif OU end_date après date_poste
        Q(end_date__isnull=True) | Q(end_date__gte=date_poste)
    ).order_by('-start_date').first()
    
    if not contrat_actif:
        return (False, "Aucun contrat actif trouvé pour ce soignant à cette date")
    
    # Vérifier si le type de garde est autorisé
    if poste.type_garde == 'nuit' and not contrat_actif.contract_type.night_shift_allowed:
        return (
            False,
            f"Le contrat {contrat_actif.contract_type.name} n'autorise pas les gardes de nuit"
        )
    
    return (True, "")


def validate_weekly_hours_limit(soignant, poste):
    """
    CONTRAINTE 6 : LIMITE D'HEURES HEBDOMADAIRES
    
    Pseudo-code:
      semaine_debut = LUNDI de la semaine de poste.date_debut
      semaine_fin = DIMANCHE de la semaine de poste.date_debut
      
      heures_existantes = 0
      POUR chaque affectation du soignant cette semaine
        heures_existantes += (affectation.poste.date_fin - affectation.poste.date_debut).heures
      
      heures_nouveau_poste = (poste.date_fin - poste.date_debut).heures
      heures_contrat = soignant.contrat_actif.max_hours_per_week
      
      SI (heures_existantes + heures_nouveau_poste) > heures_contrat
        RETOURNER (False, "Dépassement d'heures hebdomadaires")
      
      RETOURNER (True, "")
    """
    date_poste = poste.date_debut.date()
    
    # Trouver le lundi de la semaine
    lundi = date_poste - timedelta(days=date_poste.weekday())
    dimanche = lundi + timedelta(days=6)
    
    # Heures du nouveau poste
    duree_nouveau = (poste.date_fin - poste.date_debut).total_seconds() / 3600
    
    # Heures déjà affectées cette semaine
    affectations_semaine = Affectation.objects.filter(
        soignant=soignant,
        poste__date_debut__date__gte=lundi,
        poste__date_debut__date__lte=dimanche
    )
    
    heures_existantes = sum(
        (a.poste.date_fin - a.poste.date_debut).total_seconds() / 3600
        for a in affectations_semaine
    )
    
    # Limite contractuelle
    contrat_actif = SoignantContrat.objects.filter(
        soignant=soignant,
        start_date__lte=date_poste,
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=date_poste)
    ).order_by('-start_date').first()
    
    if not contrat_actif or not contrat_actif.contract_type.max_hours_per_week:
        return (True, "")  # Pas de limite définie
    
    limite = contrat_actif.contract_type.max_hours_per_week
    
    if heures_existantes + duree_nouveau > limite:
        return (
            False,
            f"Dépassement d'heures hebdomadaires : {heures_existantes:.1f}h + {duree_nouveau:.1f}h > {limite}h"
        )
    
    return (True, "")


def validate_minimum_service_threshold(poste):
    """
    CONTRAINTE 7 : SEUIL MINIMUM DE SOIGNANTS PAR SERVICE
    
    Pseudo-code:
      affectations_existantes = SELECT COUNT(*) FROM Affectation 
                               WHERE poste.id IN (
                                 SELECT id FROM Poste 
                                 WHERE care_unit.service_id = poste.care_unit.service_id
                               )
      
      min_requis = poste.care_unit.service.seuil_minimum
      
      SI affectations_existantes >= min_requis
        RETOURNER (True, "")
      RETOURNER (False, "Seuil minimum de soignants pour ce service non atteint")
    """
    if not poste.care_unit or not poste.care_unit.service:
        return (True, "")  # Pas de service défini
    
    service = poste.care_unit.service
    min_requis = service.seuil_minimum
    
    # Compter les affectations existantes pour ce poste
    affectations_existantes = Affectation.objects.filter(poste=poste).count()
    
    # Si on atteint déjà le minimum, on peut accepter
    if affectations_existantes >= min_requis:
        return (True, "")
    
    # Sinon, il faut respecter le minimum
    if affectations_existantes + 1 > min_requis:
        return (True, "")
    else:
        return (
            False,
            f"Seuil minimum de {min_requis} soignants pour le service {service.name} non atteint"
        )


# ─── FONCTION WRAPPER ───────────────────────────────────────────────────
def validate_affectation(soignant, poste):
    """
    Valide TOUTES les contraintes dures.
    
    Retourne: (is_valid: bool, errors: [str])
    
    Pseudo-code global:
      errors = []
      validateurs = [
        validate_no_overlap,
        validate_required_certifications,
        validate_minimal_rest_after_night_shift,
        validate_no_declared_absence,
        validate_contract_allows_shift_type,
        validate_weekly_hours_limit,
        validate_minimum_service_threshold
      ]
      
      POUR chaque validateur
        (is_valid, message) = validateur(soignant, poste)
        SI NOT is_valid
          errors.append(message)
      
      RETOURNER (len(errors) == 0, errors)
    """
    errors = []
    
    # Appeler tous les validateurs
    validators = [
        ("Pas de chevauchement horaire", validate_no_overlap),
        ("Certifications requises", validate_required_certifications),
        ("Repos après garde de nuit", validate_minimal_rest_after_night_shift),
        ("Pas en absence déclarée", validate_no_declared_absence),
        ("Contrat autorise le type", validate_contract_allows_shift_type),
        ("Limite d'heures hebdomadaires", validate_weekly_hours_limit),
        ("Seuil minimum service", lambda s, p: validate_minimum_service_threshold(p)),
    ]
    
    for nom_contrainte, validateur in validators:
        is_valid, message = validateur(soignant, poste)
        if not is_valid:
            errors.append(f"❌ {nom_contrainte}: {message}")
    
    return (len(errors) == 0, errors)
