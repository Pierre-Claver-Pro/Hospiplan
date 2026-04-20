# HospiPlan - Phase 2 : Pseudo-code des Contraintes Dures

## Vue d'ensemble

Ce document décrit le pseudo-code des 7 contraintes dures que le backend doit valider avant d'accepter toute affectation. Chaque contrainte est vérifiée par une fonction dédiée dans `validators.py`.

La fonction wrapper `validate_affectation(soignant, poste)` appelle tous les validateurs et retourne une liste d'erreurs si une contrainte est violée.

---

## Contrainte 1 : PAS DE CHEVAUCHEMENT HORAIRE

**Texte métier :** Un soignant ne peut pas être affecté à deux postes dont les plages horaires se chevauchent, même partiellement.

**Pseudo-code :**

```
FONCTION validate_no_overlap(soignant, poste_a_affecter)
  POUR CHAQUE affectation_existante IN Affectation WHERE soignant_id = soignant.id
    SI (affectation_existante.poste.date_fin > poste_a_affecter.date_debut) ET 
       (affectation_existante.poste.date_debut < poste_a_affecter.date_fin)
      // Il y a chevauchement
      RETOURNER (False, "Chevauchement horaire détecté")
    FIN SI
  FIN POUR
  
  // Pas de chevauchement trouvé
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
# Vérifier s'il existe une affectation existante qui chevauche la plage
Affectation.objects.filter(
    soignant=soignant,
    poste__date_fin__gt=poste.date_debut,
    poste__date_debut__lt=poste.date_fin
).exists()
```

**Exemple :**
- Soignant A affecté lundi 9h-17h
- On essaie d'affecter lundi 16h-22h → **REJETÉ** (chevauchement 16h-17h)
- On essaie d'affecter mardi 8h-16h → **ACCEPTÉ** (pas de chevauchement)

---

## Contrainte 2 : CERTIFICATIONS REQUISES NON EXPIRÉES

**Texte métier :** Un soignant ne peut occuper un poste que s'il possède TOUTES les certifications requises par ce poste, et qu'aucune n'est expirée à la date de la garde.

**Pseudo-code :**

```
FONCTION validate_required_certifications(soignant, poste)
  certs_requises = SELECT * FROM PosteCertificationRequise WHERE poste_id = poste.id
  
  POUR CHAQUE cert_requise IN certs_requises
    certification = cert_requise.certification
    date_poste = poste.date_debut
    
    // Chercher si le soignant possède cette certification
    possession = SELECT * FROM SoignantCertification 
                 WHERE soignant_id = soignant.id 
                   AND certification_id = certification.id
                   AND obtained_date <= date_poste
                   AND (expiration_date IS NULL OR expiration_date >= date_poste)
    
    SI possession N'EXISTE PAS
      RETOURNER (False, f"Certification manquante ou expirée: {certification.name}")
    FIN SI
  FIN POUR
  
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
for poste_cert in poste.certifications_requises.all():
    cert = poste_cert.certification
    date_poste = poste.date_debut.date()
    
    possede = SoignantCertification.objects.filter(
        soignant=soignant,
        certification=cert,
        obtained_date__lte=date_poste,
    ).exclude(
        expiration_date__lt=date_poste
    ).exists()
    
    if not possede:
        return (False, f"Certification manquante ou expirée : {cert.name}")
```

**Exemple :**
- Poste urgences requiert : RCP (réanimation) + urgences pédiatriques
- Soignant possède : RCP (valide) + rien d'autre → **REJETÉ**
- Soignant possède : RCP (expiré hier) + urgences pédiatriques → **REJETÉ** (RCP expiré)

---

## Contrainte 3 : REPOS MINIMAL APRÈS GARDE DE NUIT

**Texte métier :** Après une garde de nuit, un soignant doit jouir d'un repos minimal réglementaire (configurable, par défaut 11h) avant toute nouvelle affectation.

**Pseudo-code :**

```
FONCTION validate_minimal_rest_after_night_shift(soignant, poste)
  // Trouver la dernière garde de nuit avant le poste actuel
  derniere_nuit = SELECT * FROM Affectation 
                  WHERE soignant_id = soignant.id 
                    AND poste.type_garde = 'nuit'
                    AND poste.date_fin <= poste_actuel.date_debut
                  ORDER BY poste.date_fin DESC
                  LIMIT 1
  
  SI derniere_nuit EXISTE
    delta_heures = (poste_actuel.date_debut - derniere_nuit.poste.date_fin).total_hours()
    
    SI delta_heures < REPOS_MINIMAL_HEURES (défaut: 11h)
      RETOURNER (False, f"Repos minimal {REPOS_MINIMAL_HEURES}h non respecté")
    FIN SI
  FIN SI
  
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
derniere_nuit = Affectation.objects.filter(
    soignant=soignant,
    poste__type_garde='nuit',
    poste__date_fin__lte=poste.date_debut
).order_by('-poste__date_fin').first()

if derniere_nuit:
    delta = poste.date_debut - derniere_nuit.poste.date_fin
    if delta < timedelta(hours=11):
        return (False, f"Repos minimal non respecté")
```

**Exemple :**
- Soignant travaille nuit lundi 22h → mardi 6h
- Essayer d'affecter mardi 15h (9h de repos) → **REJETÉ** (< 11h)
- Essayer d'affecter mardi 17h30 (11h30 de repos) → **ACCEPTÉ**

---

## Contrainte 4 : PAS D'ABSENCE DÉCLARÉE

**Texte métier :** Un soignant en absence déclarée ne peut pas être affecté, quelle que soit la raison de l'absence.

**Pseudo-code :**

```
FONCTION validate_no_declared_absence(soignant, poste)
  date_poste = poste.date_debut
  
  // Chercher une absence qui recouvre la date du poste
  absence = SELECT * FROM Absence 
            WHERE soignant_id = soignant.id 
              AND start_date <= date_poste 
              AND expected_end_date >= date_poste
            LIMIT 1
  
  SI absence EXISTE
    RETOURNER (False, f"Soignant en absence du {absence.start_date} au {absence.expected_end_date}")
  FIN SI
  
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
date_poste = poste.date_debut.date()

absence = Absence.objects.filter(
    soignant=soignant,
    start_date__lte=date_poste,
    expected_end_date__gte=date_poste
).first()

if absence:
    return (False, f"Soignant en absence...")
```

**Exemple :**
- Soignant A en congés du 10 au 17 juin
- Essayer d'affecter 12 juin → **REJETÉ**
- Essayer d'affecter 20 juin → **ACCEPTÉ**

---

## Contrainte 5 : CONTRAT ACTIF AUTORISE LE TYPE DE GARDE

**Texte métier :** Un soignant ne peut être affecté que si (a) un contrat est actif à la date du poste, et (b) ce contrat autorise le type de garde (ex: pas de nuit pour les stagiaires).

**Pseudo-code :**

```
FONCTION validate_contract_allows_shift_type(soignant, poste)
  date_poste = poste.date_debut
  
  // Trouver le contrat actif à cette date
  contrat_actif = SELECT * FROM SoignantContrat 
                  WHERE soignant_id = soignant.id 
                    AND start_date <= date_poste 
                    AND (end_date IS NULL OR end_date >= date_poste)
                  ORDER BY start_date DESC
                  LIMIT 1
  
  SI contrat_actif N'EXISTE PAS
    RETOURNER (False, "Aucun contrat actif trouvé")
  FIN SI
  
  // Vérifier si le type de garde est autorisé
  SI poste.type_garde = 'nuit' ET contrat_actif.contract_type.night_shift_allowed = False
    RETOURNER (False, f"Contrat {contrat_actif.type} n'autorise pas les gardes de nuit")
  FIN SI
  
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
date_poste = poste.date_debut.date()

contrat_actif = SoignantContrat.objects.filter(
    soignant=soignant,
    start_date__lte=date_poste,
).filter(
    Q(end_date__isnull=True) | Q(end_date__gte=date_poste)
).order_by('-start_date').first()

if not contrat_actif:
    return (False, "Aucun contrat actif")

if poste.type_garde == 'nuit' and not contrat_actif.contract_type.night_shift_allowed:
    return (False, "Contrat n'autorise pas les gardes de nuit")
```

**Exemple :**
- Soignant stagiaire avec contrat "Stage" (night_shift_allowed=False)
- Essayer d'affecter poste jour → **ACCEPTÉ**
- Essayer d'affecter poste nuit → **REJETÉ**

---

## Contrainte 6 : LIMITE D'HEURES HEBDOMADAIRES

**Texte métier :** Le quota d'heures hebdomadaires contractuelles ne peut pas être dépassé.

**Pseudo-code :**

```
FONCTION validate_weekly_hours_limit(soignant, poste)
  date_poste = poste.date_debut
  
  // Calculer la semaine (lundi-dimanche)
  lundi = LUNDI_DE_SEMAINE(date_poste)
  dimanche = lundi + 6 jours
  
  // Heures du nouveau poste
  duree_nouveau = (poste.date_fin - poste.date_debut).heures
  
  // Heures déjà affectées cette semaine
  heures_existantes = 0
  POUR CHAQUE affectation IN Affectation 
           WHERE soignant_id = soignant.id 
             AND poste.date_debut >= lundi 
             AND poste.date_debut <= dimanche
    heures_existantes += (affectation.poste.date_fin - affectation.poste.date_debut).heures
  FIN POUR
  
  // Limite contractuelle
  contrat_actif = SELECT ... WHERE date_poste actuelle
  limite = contrat_actif.contract_type.max_hours_per_week
  
  SI (heures_existantes + duree_nouveau) > limite
    RETOURNER (False, f"{heures_existantes}h + {duree_nouveau}h > {limite}h (limite)")
  FIN SI
  
  RETOURNER (True, "")
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
lundi = date_poste - timedelta(days=date_poste.weekday())
dimanche = lundi + timedelta(days=6)

duree_nouveau = (poste.date_fin - poste.date_debut).total_seconds() / 3600

affectations_semaine = Affectation.objects.filter(
    soignant=soignant,
    poste__date_debut__date__gte=lundi,
    poste__date_debut__date__lte=dimanche
)

heures_existantes = sum(
    (a.poste.date_fin - a.poste.date_debut).total_seconds() / 3600
    for a in affectations_semaine
)

limite = contrat_actif.contract_type.max_hours_per_week

if heures_existantes + duree_nouveau > limite:
    return (False, f"Dépassement d'heures...")
```

**Exemple :**
- Soignant CDI avec max_hours_per_week = 35h
- Lundi-jeudi : 8h + 8h + 8h + 8h = 32h affectées
- Vendredi on essaie d'affecter 4h (total = 36h) → **REJETÉ** (> 35h)
- Vendredi on essaie d'affecter 3h (total = 35h) → **ACCEPTÉ**

---

## Contrainte 7 : SEUIL MINIMUM DE SOIGNANTS PAR SERVICE

**Texte métier :** Le nombre de soignants qualifiés affectés à un service ne peut pas descendre sous le seuil de sécurité défini pour ce service et ce type de créneau.

**Pseudo-code :**

```
FONCTION validate_minimum_service_threshold(poste)
  SI poste.care_unit.service N'EXISTE PAS
    RETOURNER (True, "")  // Pas de service = pas de validation
  FIN SI
  
  service = poste.care_unit.service
  min_requis = service.seuil_minimum
  
  // Compter les soignants affectés POUR CE POSTE
  affectations_existantes = COUNT(*) FROM Affectation WHERE poste_id = poste.id
  
  // On compte cet affectation à venir
  affectations_total = affectations_existantes + 1
  
  SI affectations_total >= min_requis
    RETOURNER (True, "")  // Seuil atteint
  SINON
    RETOURNER (False, f"Seuil minimum {min_requis} non atteint pour {service.name}")
  FIN SI
FIN FONCTION
```

**Implémentation Python (Django) :**
```python
service = poste.care_unit.service
min_requis = service.seuil_minimum

affectations_existantes = Affectation.objects.filter(poste=poste).count()

if affectations_existantes + 1 >= min_requis:
    return (True, "")
else:
    return (False, f"Seuil minimum {min_requis} non atteint")
```

**Exemple :**
- Service Urgences avec seuil_minimum = 3
- Pour un poste donné : 0 affectations existantes
- Première affectation → 1 total < 3 → **REJETÉ**
- Deuxième affectation → 2 total < 3 → **REJETÉ**
- Troisième affectation → 3 total = 3 → **ACCEPTÉ**

---

## Fonction Wrapper : VALIDER TOUTES LES CONTRAINTES

**Pseudo-code :**

```
FONCTION validate_affectation(soignant, poste)
  errors = []
  
  validators = [
    ("Pas de chevauchement horaire", validate_no_overlap),
    ("Certifications requises", validate_required_certifications),
    ("Repos après garde de nuit", validate_minimal_rest_after_night_shift),
    ("Pas en absence déclarée", validate_no_declared_absence),
    ("Contrat autorise le type", validate_contract_allows_shift_type),
    ("Limite d'heures hebdomadaires", validate_weekly_hours_limit),
    ("Seuil minimum service", validate_minimum_service_threshold),
  ]
  
  POUR CHAQUE (nom, validateur) IN validators
    (is_valid, message) = validateur(soignant, poste)
    SI NOT is_valid
      errors.append(f"❌ {nom}: {message}")
    FIN SI
  FIN POUR
  
  RETOURNER (len(errors) == 0, errors)
FIN FONCTION
```

**Utilisation dans la vue :**

```python
is_valid, errors = validate_affectation(soignant, poste)

if not is_valid:
    return Response({
        "error": "Affectation impossible - Contraintes dures violées",
        "details": errors,  # Liste de tous les problèmes
        "soignant": f"{soignant.prenom} {soignant.nom}",
        "poste": f"{poste.type_garde}..."
    }, status=400)

# Créer l'affectation
affectation = Affectation.objects.create(soignant=soignant, poste=poste)
```

---

## Exemple Complet : Tentative d'Affectation

```
POST /api/affectations/
{
  "soignant": 5,
  "poste": 42
}

── Validation ──

1. ✅ validate_no_overlap → OK (pas de chevauchement)
2. ✅ validate_required_certifications → OK (a les bonnes certs)
3. ❌ validate_minimal_rest_after_night_shift → ERREUR (10h de repos, besoin de 11h)
4. ✅ validate_no_declared_absence → OK (pas en absence)
5. ✅ validate_contract_allows_shift_type → OK (contrat OK)
6. ✅ validate_weekly_hours_limit → OK (34h < 35h)
7. ✅ validate_minimum_service_threshold → OK

── Réponse ──

HTTP 400 Bad Request
{
  "error": "Affectation impossible - Contraintes dures violées",
  "details": [
    "❌ Repos après garde de nuit: Repos minimal de 11h non respecté"
  ],
  "soignant": "Jean Dupont",
  "poste": "nuit (2026-04-18 22:00 à 2026-04-19 06:00)"
}
```

---

## Intégration avec la Base de Données (Phase 1)

Toutes les requêtes de validation s'appuient sur les tables et relations modélisées en Phase 1 :

| Contrainte | Tables utilisées |
|-----------|------------------|
| 1. Pas de chevauchement | `Affectation`, `Poste` |
| 2. Certifications | `SoignantCertification`, `PosteCertificationRequise`, `Certification` |
| 3. Repos après nuit | `Affectation`, `Poste` |
| 4. Pas en absence | `Absence`, `Soignant` |
| 5. Contrat autorise | `SoignantContrat`, `ContractType` |
| 6. Limite hebdomadaire | `Affectation`, `Poste`, `SoignantContrat`, `ContractType` |
| 7. Seuil minimum | `Service`, `CareUnit`, `Poste`, `Affectation` |

---

## Fichiers Implémentés

- **validators.py** : Contient toutes les 7 fonctions de validation
- **views.py** : La vue `create_affectation` qui appelle `validate_affectation`
- **models.py** : Schéma de base de données (Phase 1)

## Test de l'API

```bash
# Tester une affectation valide
curl -X POST http://localhost:8000/api/affectations/ \
  -H "Content-Type: application/json" \
  -d '{"soignant": 1, "poste": 1}'

# Vous devez recevoir soit:
# - 201 Created (succès)
# - 400 Bad Request avec liste d'erreurs (contrainte violée)
```

---

**Document de référence pour la Phase 2 - Contraintes Dures**
