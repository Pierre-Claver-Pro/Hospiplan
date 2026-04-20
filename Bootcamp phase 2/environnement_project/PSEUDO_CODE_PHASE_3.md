# 📋 PHASE 3 : PSEUDO-CODE DÉTAILLÉ DE GÉNÉRATION DE PLANNING

## Document sur feuille papier : HospiPlan Phase 3

Ce document satisfait à l'exigence de la phase 3 :
> "Sur feuille papier : pseudo-code des fonctions qui servent à minimiser les contraintes molles (via une heuristique et/ou une métaheuristique)"

---

## 📌 Vue d'ensemble de l'algorithme

### Problème

**Entrée :**
- Une période [start_date, end_date]
- Un ensemble de postes à couvrir (Poste)
- Un ensemble de soignants disponibles (Soignant)

**Sortie :**
- Un Planning avec affectations (Soignant → Poste)
- Tel que :
  - ✅ TOUTES les contraintes dures sont respectées (100% légal)
  - ✅ Les contraintes molles sont minimisées (score le plus bas possible)

**Complexité :** NP-difficile (scheduling is NP-complete)

---

## 🎯 Heuristique : LEAST-LOADED (Glouton)

### Pseudo-code niveau 1 (Haut niveau)

```
ALGORITHME GenererPlanning(start_date, end_date)

  // Étape 1 : Initialisation
  postes = SelectionnerPostes(start_date, end_date)
  planning = CreerPlanning(start_date, end_date)
  
  // Étape 2 : Pour chaque poste (dans un ordre stratégique)
  POUR chaque poste DANS postes FAIRE
    soignants_legaux = TrouverSoignantLegaux(poste)
    
    SI soignants_legaux.taille() > 0 ALORS
      // Appliquer heuristique : LEAST-LOADED
      soignant = ChoisirLeMoinsCharge(soignants_legaux, planning)
      AffecterSoignantAuPoste(soignant, poste, planning)
    SINON
      // Aucun soignant légal disponible
      MarquerPosteCommeNonCouvert(planning, poste)
    FIN SI
  FIN POUR
  
  // Étape 3 : Optimisation du score
  score = CalculerScoreMolles(planning)
  planning.score_total = score
  
  RETOURNER planning

FIN ALGORITHME
```

---

## 📝 Détail des sous-fonctions

### 1. SelectionnerPostes(start_date, end_date)

```
FONCTION SelectionnerPostes(start_date, end_date) → Liste<Poste>

  // Sélectionner tous les postes dans la plage
  postes = []
  POUR chaque poste DANS DB.Poste FAIRE
    SI poste.date_debut >= start_date ET poste.date_fin <= end_date ALORS
      postes.ajouter(poste)
    FIN SI
  FIN POUR
  
  // Tri stratégique : nuits en priorité (plus difficiles à couvrir)
  postes = TRIER(postes, par = (type_garde DESC, date_debut ASC))
  // → Les nuits apparaissent d'abord, puis les jours, puis les week-ends
  
  RETOURNER postes

FIN FONCTION

Exemple:
  Entrée: start_date = 2025-01-06, end_date = 2025-01-12
  Sortie: [
    Poste(nuit, 06/01 22h-06h),
    Poste(nuit, 07/01 22h-06h),
    ...
    Poste(jour, 06/01 09h-17h),
    Poste(jour, 07/01 09h-17h),
    ...
  ]
```

### 2. TrouverSoignantLegaux(poste)

```
FONCTION TrouverSoignantLegaux(poste) → Liste<Soignant>

  soignants_legaux = []
  
  POUR chaque soignant DANS DB.Soignant FAIRE
    SI soignant.is_active ALORS
      // Valider TOUTES les contraintes dures
      est_valide, message = ValidateAffectation(soignant, poste)
      
      SI est_valide ALORS
        soignants_legaux.ajouter(soignant)
      FIN SI
    FIN SI
  FIN POUR
  
  RETOURNER soignants_legaux

FIN FONCTION

Appels des validateurs (Phase 2):
  1. ValidateNoOverlap(soignant, poste)
     → Pas de chevauchement avec affectations existantes
  
  2. ValidateRequiredCertifications(soignant, poste)
     → Certifications présentes et valides
  
  3. ValidateMinimalRest(soignant, poste)
     → 11h minimum après garde de nuit
  
  4. ValidateNoDeclaredAbsence(soignant, poste)
     → Pas en absence à cette date
  
  5. ValidateContractAllowsShiftType(soignant, poste)
     → Contrat autorise le type de garde
  
  6. ValidateWeeklyHoursLimit(soignant, poste)
     → Heures hebdomadaires pas dépassées
  
  7. ValidateDeclaredConstraints(soignant, poste)
     → Contraintes déclarées (F-07) respectées
```

### 3. ChoisirLeMoinsCharge(soignants_legaux, planning) ← HEURISTIQUE

```
FONCTION ChoisirLeMoinsCharge(soignants_legaux, planning) → Soignant

  charge_map = {}  // Dictionnaire: soignant_id → nombre_affectations
  
  // Compter le nombre d'affectations de chaque soignant DANS CE PLANNING
  POUR chaque soignant DANS soignants_legaux FAIRE
    count = 0
    POUR chaque affectation DANS planning.affectations FAIRE
      SI affectation.soignant == soignant ALORS
        count = count + 1
      FIN SI
    FIN POUR
    charge_map[soignant.id] = count
  FIN POUR
  
  // Retourner le soignant avec le MOINS d'affectations
  soignant_id_min = MIN(charge_map.values())
  soignant = FIND(soignants_legaux, id = soignant_id_min)
  
  RETOURNER soignant

FIN FONCTION

Exemple:
  soignants_legaux = [Dupont (0 aff), Martin (2 aff), Durand (1 aff)]
  → Choisir Dupont (0 < 1 < 2)
  
  Effet: Tend à équilibrer naturellement la charge
         Réduit l'écart-type du nombre de gardes par soignant
```

### 4. AffecterSoignantAuPoste(soignant, poste, planning)

```
FONCTION AffecterSoignantAuPoste(soignant, poste, planning) → void

  // Créer une nouvelle affectation dans le planning
  affectation = CREER AffectationPlanning(
    planning = planning,
    soignant = soignant,
    poste = poste,
    is_manual = false
  )
  
  // Ajouter à la base de données
  affectation.save()
  planning.affectations.ajouter(affectation)

FIN FONCTION
```

### 5. MarquerPosteCommeNonCouvert(planning, poste)

```
FONCTION MarquerPosteCommeNonCouvert(planning, poste) → void

  // Simplement ne pas affecter ce poste
  // Le compteur uncovered_shifts sera incrémenté lors du calcul du score
  
  LOG("⚠️ Poste non couvert : {poste.type_garde} {poste.date_debut}")

FIN FONCTION

Raison pour ne pas couvrir:
  - Aucun soignant légal n'existe pour ce poste
  - Exemple: Poste urgent requiert certification RCP
    mais aucun soignant actif n'a cette certification valide
```

---

## 🧮 Calcul du score des contraintes molles

### Pseudo-code principal

```
FONCTION CalculerScoreMolles(planning) → float

  score_total = 0.0
  
  // Pour chaque type de contrainte molle
  
  // 1. Nuits consécutives
  penalty_nuit = CalculerPenaliteNuitsConsecutives(planning)
  weight_nuit = CHARGER_WEIGHT('night_consecutive')
  score_total += penalty_nuit * weight_nuit
  
  // 2. Préférences
  penalty_pref = CalculerPenalitePreferences(planning)
  weight_pref = CHARGER_WEIGHT('preferences')
  score_total += penalty_pref * weight_pref
  
  // 3. Équité de charge
  penalty_eq_charge = CalculerPenaliteEquiteCharge(planning)
  weight_eq_charge = CHARGER_WEIGHT('workload_equity')
  score_total += penalty_eq_charge * weight_eq_charge
  
  // 4. Changements de service
  penalty_service = CalculerPenaliteServiceChanges(planning)
  weight_service = CHARGER_WEIGHT('service_changes')
  score_total += penalty_service * weight_service
  
  // 5. Équité week-ends
  penalty_we = CalculerPenaliteWeekendEquity(planning)
  weight_we = CHARGER_WEIGHT('weekend_equity')
  score_total += penalty_we * weight_we
  
  // 6. Continuité de soins
  penalty_cont = CalculerPenatiteContinuite(planning)
  weight_cont = CHARGER_WEIGHT('continuity')
  score_total += penalty_cont * weight_cont
  
  RETOURNER score_total

FIN FONCTION
```

### Contrainte 1 : Nuits Consécutives

```
FONCTION CalculerPenaliteNuitsConsecutives(planning) → float

  penalty = 0.0
  MAX_NUITS = 3
  
  // Grouper les affectations par soignant
  affectations_par_soignant = GROUPER(planning.affectations, par=soignant)
  
  POUR chaque (soignant_id, affectations) DANS affectations_par_soignant FAIRE
    
    // Trier par date
    affectations = TRIER(affectations, par=poste.date_debut ASC)
    
    // Compter les nuits consécutives
    nuits_consecutives = 0
    POUR chaque affectation DANS affectations FAIRE
      
      SI affectation.poste.type_garde == 'nuit' ALORS
        nuits_consecutives += 1
        
        SI nuits_consecutives > MAX_NUITS ALORS
          // Chaque nuit au-delà de 3 coûte 5 points
          penalty += (nuits_consecutives - MAX_NUITS) * 5.0
        FIN SI
      SINON
        // Réinitialiser le compteur
        nuits_consecutives = 0
      FIN SI
      
    FIN POUR
    
  FIN POUR
  
  RETOURNER penalty

FIN FONCTION

Exemple:
  Soignant A: nuit, nuit, nuit, nuit, jour
  nuits_consecutives = 1, 2, 3, 4
  Quand nuits_consecutives = 4 > 3:
    penalty += (4 - 3) * 5 = 5 points
  Total pour ce soignant: 5 points

  Soignant B: nuit, nuit, jour, jour, nuit, nuit, nuit, nuit, nuit
  Séquence 1: nuit, nuit → 0 pénalité
  Séquence 2: nuit, nuit, nuit, nuit, nuit → (5-3)*5 = 10 points
  Total pour ce soignant: 10 points
```

### Contrainte 3 : Équité de Charge (écart-type)

```
FONCTION CalculerPenaliteEquiteCharge(planning) → float

  // Compter le nombre d'affectations par soignant
  charges = []
  affectations_par_soignant = GROUPER(planning.affectations, par=soignant)
  
  POUR chaque (soignant_id, affectations) DANS affectations_par_soignant FAIRE
    charges.ajouter(affectations.taille())
  FIN POUR
  
  SI charges.taille() < 2 ALORS
    // Impossible de calculer écart-type avec <2 valeurs
    RETOURNER 0.0
  FIN SI
  
  // Calculer écart-type
  moyenne = MOYENNE(charges)
  variance = MOYENNE((charge - moyenne)² POUR charge DANS charges)
  ecart_type = RACINE(variance)
  
  // Transformer en pénalité
  // Plus l'écart-type est élevé, plus inégale est la charge
  penalty = ecart_type * 10.0
  
  RETOURNER penalty

FIN FONCTION

Exemple:
  charges = [8, 8, 8, 8, 8]
  → écart-type = 0 → penalty = 0 ✅ PARFAIT
  
  charges = [10, 10, 6, 6, 6]
  → écart-type ≈ 1.67 → penalty ≈ 16.7
  
  charges = [12, 12, 2, 2, 2]
  → écart-type ≈ 4.5 → penalty ≈ 45.0 ❌ INÉGAL
```

### Contrainte 4 : Changements de Service

```
FONCTION CalculerPenaliteServiceChanges(planning) → float

  penalty = 0.0
  MAX_CHANGES_PAR_SEMAINE = 1
  
  POUR chaque soignant DANS SOIGNANTS_UNIQUES(planning.affectations) FAIRE
    
    // Obtenir toutes les affectations de ce soignant
    affectations = FILTER(planning.affectations, soignant = soignant)
    affectations = TRIER(affectations, par=poste.date_debut ASC)
    
    // Compter les changements de service (care_unit)
    derniere_unit = null
    changes = 0
    
    POUR chaque affectation DANS affectations FAIRE
      care_unit_actuelle = affectation.poste.care_unit
      
      SI care_unit_actuelle != derniere_unit AND derniere_unit != null ALORS
        changes += 1
      FIN SI
      
      derniere_unit = care_unit_actuelle
    FIN POUR
    
    // Pénaliser les changements au-delà de MAX
    SI changes > MAX_CHANGES_PAR_SEMAINE ALORS
      penalty += (changes - MAX_CHANGES_PAR_SEMAINE) * 3.0
    FIN SI
    
  FIN POUR
  
  RETOURNER penalty

FIN FONCTION

Exemple:
  Soignant X (semaine du 6 au 12 janvier):
    Lundi 6 : Urgences
    Mardi 7 : Urgences
    Mercredi 8 : Cardiologie  ← Changement 1
    Jeudi 9 : Cardiologie
    Vendredi 10 : Pédiatrie   ← Changement 2
    Samedi 11 : Pédiatrie
    Dimanche 12 : Urgences    ← Changement 3
  
  changes = 3 > MAX(1)
  penalty = (3 - 1) * 3 = 6 points
```

### Contrainte 5 : Équité Week-ends

```
FONCTION CalculerPenaliteWeekendEquity(planning) → float

  // Compter les week-ends travaillés par soignant
  weekend_counts = {}
  
  POUR chaque affectation DANS planning.affectations FAIRE
    
    SI affectation.poste.type_garde == 'weekend' ALORS
      soignant_id = affectation.soignant.id
      SI soignant_id PAS DANS weekend_counts ALORS
        weekend_counts[soignant_id] = 0
      FIN SI
      weekend_counts[soignant_id] += 1
    FIN SI
    
  FIN POUR
  
  // Calculer l'écart-type des week-ends
  weekend_values = weekend_counts.values()
  
  SI weekend_values.taille() < 2 ALORS
    RETOURNER 0.0
  FIN SI
  
  moyenne = MOYENNE(weekend_values)
  variance = MOYENNE((count - moyenne)² POUR count DANS weekend_values)
  ecart_type = RACINE(variance)
  
  penalty = ecart_type * 8.0  // Poids moins élevé que workload_equity
  
  RETOURNER penalty

FIN FONCTION
```

---

## 🔄 Métaheuristique optionnelle : SIMULATED ANNEALING

### Pseudo-code (pour affinage futur)

```
ALGORITHME SimulatedAnnealing(planning_initial, temperature=100, cooling_rate=0.95)

  solution_courante = planning_initial
  score_courant = CalculerScore(solution_courante)
  
  meilleure_solution = solution_courante
  meilleur_score = score_courant
  
  temperature = temperature
  
  TANT QUE temperature > 0.1 FAIRE
    
    // Générer une solution voisine (perturbation mineure)
    solution_voisine = PerturbationMineure(solution_courante)
    score_voisin = CalculerScore(solution_voisine)
    
    // Critère d'acceptation
    delta = score_voisin - score_courant
    
    SI delta < 0 ALORS
      // Meilleure → accepter
      solution_courante = solution_voisine
      score_courant = score_voisin
    SINON
      // Pire → accepter avec probabilité exp(-delta/T)
      prob_acceptance = exp(-delta / temperature)
      SI random() < prob_acceptance ALORS
        solution_courante = solution_voisine
        score_courant = score_voisin
      FIN SI
    FIN SI
    
    // Mettre à jour la meilleure solution trouvée
    SI score_courant < meilleur_score ALORS
      meilleure_solution = solution_courante
      meilleur_score = score_courant
    FIN SI
    
    // Refroidissement
    temperature = temperature * cooling_rate
    
  FIN TANT QUE
  
  RETOURNER meilleure_solution

FIN ALGORITHME

Idée:
  - Commencer avec le planning généré par least-loaded
  - Essayer des petites modifications (échanges d'affectations)
  - Accepter les améliorations
  - Accepter les dégradations temporaires avec probabilité décroissante
  - Converge vers un optimum local meilleur
```

---

## 📊 Résumé des algorithmes

| Algorithme | Complexité | Qualité | Temps | Implémentation |
|-----------|-----------|---------|--------|--------------|
| **Least-Loaded (Glouton)** | O(n*m) | Bonne | Rapide | ✅ IMPLÉMENTÉE |
| **Simulated Annealing** | O(iter*n*m) | Très Bonne | Moyen | 📋 À implémenter |
| **Genetic Algorithm** | O(gen*pop*n*m) | Excellente | Lent | 📋 À implémenter |
| **Branch & Bound** | O(b^d) | Optimal | Très lent | 📋 À implémenter |

---

## ✅ Conclusion

Cette documentation décrit l'heuristique **least-loaded** implémentée en Phase 3 :

1. **Sélectionner** les postes dans un ordre stratégique (nuits en priorité)
2. **Pour chaque poste** : trouver les soignants légaux (contraintes dures)
3. **Choisir le moins chargé** : heuristique qui équilibre naturellement
4. **Calculer le score** : somme pondérée des 6 contraintes molles
5. **Retourner** le planning 100% légal et optimisé

**Résultat :** Un planning admissible (contraintes dures OK) et bon (score molles minimisé).

Pour une optimisation encore meilleure, utiliser **Simulated Annealing** en Phase 4.
