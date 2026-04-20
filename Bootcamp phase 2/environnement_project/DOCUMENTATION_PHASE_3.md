# 📅 HospiPlan Phase 3 : Génération Automatique de Plannings

## 📋 Résumé des changements

Cette phase 3 ajoute la **génération automatique de plannings** au système HospiPlan. Le système génère des plannings 100% légaux (respectant toutes les contraintes dures) et optimisés selon les contraintes molles.

### Nouvelles Fonctionnalités

✅ Génération automatique de plannings (jour, semaine, période)  
✅ Heuristique **least-loaded** pour équilibrer la charge  
✅ Calcul du score des contraintes molles (6 critères)  
✅ Interface web pour générer et visualiser les plannings  
✅ Configuration flexible des poids des contraintes  
✅ API REST pour intégration tierce  

---

## 🏗️ Architecture

### Modèles Django ajoutés

```python
# Nouveau modèle pour stocker un planning généré
Planning
├── name: str
├── start_date, end_date: date
├── status: 'draft' | 'generated' | 'edited' | 'approved' | 'published'
├── score_total: float (résultat des contraintes molles)
└── generated_by_algorithm: str

# Affectations au sein d'un planning
AffectationPlanning
├── planning: FK(Planning)
├── soignant: FK(Soignant)
├── poste: FK(Poste)
└── is_manual: bool (modifiée manuellement après génération ?)

# Détail du score
ScorePlanning
├── penalty_night_consecutive: float
├── penalty_preferences: float
├── penalty_workload_equity: float
├── penalty_service_changes: float
├── penalty_weekend_equity: float
└── penalty_continuity: float

# Configuration des contraintes molles
ConstrainteSouple
├── constraint_type: str (choix)
├── weight: float (1.0 = normal)
└── is_active: bool
```

### Nouveaux fichiers

```
hospiplan/
├── planning_generator.py          # Heuristique + calcul scores
├── serializers.py                 # ✏️ MODIFIÉ : + 5 nouveaux serializers
├── views.py                       # ✏️ MODIFIÉ : + 3 nouveaux ViewSets
├── urls.py                        # ✏️ MODIFIÉ : + 3 nouvelles routes
└── models.py                      # ✏️ MODIFIÉ : + 4 nouveaux modèles

hospiplan-frontend/src/
├── pages/Plannings.jsx            # ✨ NOUVEAU : Page principale Phase 3
└── styles/Plannings.css           # ✨ NOUVEAU : Styles
```

---

## 🚀 Mise en place

### 1️⃣ Appliquer les migrations

```bash
# Se placer dans le répertoire du projet Django
cd c:\Users\pcoko\Les Etudes\Année 4\IABD\Bootcamp\Bootcamp phase 2\environnement_project\environnement

# Créer les migrations pour les nouveaux modèles
python manage.py makemigrations hospiplan

# Appliquer les migrations
python manage.py migrate hospiplan
```

### 2️⃣ Charger la configuration par défaut des contraintes molles

```bash
# Depuis Django shell
python manage.py shell

>>> from hospiplan.models import ConstrainteSouple
>>> 
>>> # Créer les configurations par défaut
>>> ConstrainteSouple.objects.create(
...     constraint_type='night_consecutive',
...     weight=1.0,
...     is_active=True,
...     description='Éviter plus de 3 nuits consécutives'
... )
>>> ConstrainteSouple.objects.create(
...     constraint_type='preferences',
...     weight=0.5,
...     is_active=False,  # À activer quand F-07 sera implémenté
...     description='Respecter les préférences de créneaux'
... )
>>> ConstrainteSouple.objects.create(
...     constraint_type='workload_equity',
...     weight=1.5,
...     is_active=True,
...     description='Équilibrer la charge (écart-type)'
... )
>>> ConstrainteSouple.objects.create(
...     constraint_type='service_changes',
...     weight=0.8,
...     is_active=True,
...     description='Minimiser changements de service'
... )
>>> ConstrainteSouple.objects.create(
...     constraint_type='weekend_equity',
...     weight=1.0,
...     is_active=True,
...     description='Équité dans les week-ends'
... )
>>> ConstrainteSouple.objects.create(
...     constraint_type='continuity',
...     weight=0.3,
...     is_active=False,  # À activer quand données patients disponibles
...     description='Favoriser continuité de soins'
... )
>>> exit()
```

### 3️⃣ Tester depuis Django shell

```bash
python manage.py shell

>>> from hospiplan.planning_generator import generer_planning_simple
>>> from datetime import date
>>>
>>> # Générer un planning pour la semaine du 6 au 12 janvier 2025
>>> planning = generer_planning_simple(
...     date(2025, 1, 6),
...     date(2025, 1, 12),
...     name="Planning Test Semaine 1"
... )
>>>
>>> print(f"✅ Planning généré: {planning.name}")
>>> print(f"   Score: {planning.score_total:.2f}")
>>> print(f"   Affectations: {planning.affectations.count()}")
>>> exit()
```

---

## 🌐 Endpoints API (Phase 3)

### Générer un nouveau planning

```bash
POST /api/hospiplan/plannings/generate/

Requête JSON:
{
  "start_date": "2025-01-06",
  "end_date": "2025-01-12",
  "name": "Planning Semaine 1 (optionnel)",
  "algorithm": "least-loaded"
}

Réponse (201 Created):
{
  "id": 1,
  "name": "Planning Semaine 1",
  "start_date": "2025-01-06",
  "end_date": "2025-01-12",
  "status": "generated",
  "score_total": 24.5,
  "generated_by_algorithm": "least-loaded",
  "affectations": [
    {
      "id": 1,
      "soignant": 5,
      "soignant_nom": "Jean Dupont",
      "poste": 10,
      "is_manual": false,
      ...
    },
    ...
  ],
  "score_detail": {
    "penalty_night_consecutive": 5.0,
    "penalty_workload_equity": 12.3,
    ...
  }
}
```

### Lister tous les plannings

```bash
GET /api/hospiplan/plannings/

Paramètres optionnels:
  ?status=generated
  ?start_date=2025-01-01
  ?end_date=2025-01-31
```

### Récupérer le détail d'un planning

```bash
GET /api/hospiplan/plannings/{id}/

Retourne le planning avec toutes ses affectations.
```

### Récupérer le score d'un planning

```bash
GET /api/hospiplan/plannings/{id}/score/

Retourne le détail des pénalités de chaque contrainte molle.
```

### Lister les affectations d'un planning

```bash
GET /api/hospiplan/plannings/{id}/affectations/
```

### Ajouter une affectation manuellement

```bash
POST /api/hospiplan/affectations-planning/

Requête JSON:
{
  "planning": 1,
  "soignant": 5,
  "poste": 10
}

Note: Toujours validée contre les contraintes dures!
```

### Configurer les contraintes molles

```bash
GET /api/hospiplan/contraintes-souples/

PUT /api/hospiplan/contraintes-souples/{id}/

Exemple :
{
  "constraint_type": "workload_equity",
  "weight": 2.0,          # Augmenter l'importance
  "is_active": true
}
```

---

## 📊 Heuristique LEAST-LOADED

### Pseudo-code

```
FONCTION generer_planning(start_date, end_date)
  
  // Étape 1 : Récupérer tous les postes à couvrir
  postes = SELECT * FROM Poste WHERE date BETWEEN start_date AND end_date
  
  // Étape 2 : Créer un planning vide
  planning = Planning.create(status='generated')
  
  // Étape 3 : Pour chaque poste (triés par priorité)
  pour chaque poste IN postes_triés_par_priorité
    
    // Trouver les soignants légaux (contraintes dures OK)
    soignants_legaux = []
    pour chaque soignant IN all_soignants
      si validate_affectation(soignant, poste) == OK
        soignants_legaux.ajouter(soignant)
    
    // Heuristique : choisir le moins chargé dans CE planning
    si soignants_legaux.taille() > 0
      soignant = min(soignants_legaux, key=lambda s: count_affectations(s, planning))
      planning.affectations.ajouter(soignant, poste)
    sinon
      planning.postes_non_couverts.ajouter(poste)
  
  // Étape 4 : Calculer le score des contraintes molles
  score = calculer_score_contraintes_molles(planning)
  planning.score_total = score
  
  RETOURNER planning
```

### Avantages

- ✅ **Simple** : facile à comprendre et à déboguer
- ✅ **Rapide** : O(n*m) où n=postes, m=soignants
- ✅ **Efficace** : tend naturellement vers l'équité de charge
- ✅ **Extensible** : facile d'ajouter d'autres heuristiques

### Limitations

- ⚠️ Pas optimal au sens mathématique (c'est NP-difficile)
- ⚠️ Ordre des postes influe sur la qualité du résultat
- ⚠️ Pas de backtracking si un choix s'avère mauvais

### Améliorations possibles (Phase 4)

- Métaheuristique **Simulated Annealing** pour affinage
- **Genetic Algorithm** pour optimisation multi-critère
- **Tabu Search** pour éviter optima locaux
- Branch-and-bound avec pruning

---

## 📈 Contraintes Molles & Score

### 1. Nuits Consécutives

```
Pénalité = (nuits_consécutives - 3) * 5  si > 3
Explication: Max 3 nuits d'affilée, -5 points par nuit supplémentaire
```

### 2. Préférences de Créneaux (F-07)

```
Pénalité = nombre_preferences_violées * weight
Note: À implémenter quand le modèle Préférence sera créé
```

### 3. Équité de Charge

```
Pénalité = écart_type(nombre_gardes_par_soignant) * 10
Explication: Minimiser la variance des charges
```

### 4. Changements de Service

```
Pénalité = (changements_service - 1) * 3  si > 1 par semaine
Explication: Favoriser la stabilité dans un service
```

### 5. Équité Week-ends

```
Pénalité = écart_type(week_ends_par_soignant) * 8
Explication: Répartir équitablement les week-ends travaillés
```

### 6. Continuité de Soins

```
Pénalité = nombre_changements_patients * weight
Note: À affiner quand les données de suivi de patients seront disponibles
```

### Score Total

```
score_total = Σ (pénalité_i * weight_i)

Plus le score est bas, meilleur est le planning! 🎯
```

---

## 🖥️ Interface Frontend (React)

### Page `/plannings`

**Sections :**
1. 📋 Liste des plannings existants (tableau)
2. ✨ Formulaire de génération
3. 📊 Détail du planning sélectionné
4. 📈 Affichage du score et pénalités
5. 📑 Table d'affectations

**Fonctionnalités :**
- ✅ Générer un nouveau planning avec dates et algorithme
- ✅ Lister tous les plannings avec filtrage
- ✅ Voir détail complet avec affectations
- ✅ Afficher score global et détail des pénalités
- ✅ Ajouter/modifier affectations (respectant contraintes dures)

---

## 🧪 Exemples d'utilisation

### Exemple 1 : Générer un planning simple

```python
from hospiplan.planning_generator import generer_planning_simple
from datetime import date

# Générer
planning = generer_planning_simple(
    date(2025, 1, 6),
    date(2025, 1, 12),
    name="Semaine 1"
)

# Afficher le résultat
print(f"Planning: {planning.name}")
print(f"Score: {planning.score_total:.2f}")
print(f"Affectations: {planning.affectations.count()}")

# Accéder au score détaillé
score = planning.score_detail
print(f"  - Nuits consécutives: {score.penalty_night_consecutive:.2f}")
print(f"  - Équité charge: {score.penalty_workload_equity:.2f}")
```

### Exemple 2 : Via l'API REST

```bash
curl -X POST http://localhost:8000/api/hospiplan/plannings/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2025-01-06",
    "end_date": "2025-01-12",
    "name": "Planning Test"
  }'
```

### Exemple 3 : Générer avec algorithme custom

```python
from hospiplan.planning_generator import PlanningGenerator
from datetime import date

generator = PlanningGenerator(
    date(2025, 1, 6),
    date(2025, 1, 12),
    algorithm='least-loaded'
)

planning = generator.generate(name="Mon Planning")
print(f"Score: {planning.score_total}")
```

### Exemple 4 : Modifier les poids des contraintes

```python
from hospiplan.models import ConstrainteSouple

# Augmenter l'importance de l'équité de charge
eq = ConstrainteSouple.objects.get(constraint_type='workload_equity')
eq.weight = 2.5  # Au lieu de 1.5
eq.save()

# Désactiver les contraintes trop pénalisantes
pref = ConstrainteSouple.objects.get(constraint_type='preferences')
pref.is_active = False
pref.save()

# Maintenant, les nouveaux plannings seront générés avec ces poids
```

---

## 🔄 Workflow Phase 3

```
1. RH saisit période souhaitée
   ↓
2. Clic "Générer Planning"
   ↓
3. Backend:
   - Récupère tous les postes
   - Pour chaque poste, trouve soignants légaux
   - Applique heuristique least-loaded
   - Vérifie toutes contraintes dures
   - Calcule score contraintes molles
   ↓
4. Frontend affiche:
   - Planning généré ✅
   - Score global (ex: 24.5)
   - Détail pénalités
   - Table affectations
   ↓
5. RH peut:
   - Modifier manuellement (+ validations)
   - Approuver
   - Exporter
   - Régénérer si insatisfait
```

---

## ⚠️ Points importants

### Contraintes Dures = 100% garanties

Chaque affectation générée ou ajoutée manuellement respecte **TOUTES** les contraintes dures :
- ✅ Pas de chevauchement horaire
- ✅ Certifications présentes et valides
- ✅ Repos minimal après nuit respecté
- ✅ Soignant pas en absence
- ✅ Contrat permet le type de garde
- ✅ Heures hebdomadaires respectées
- ✅ Contraintes déclarées respectées

**Un planning généré par Phase 3 est LÉGAL à 100%.**

### Contraintes Molles = Optimisation

Les contraintes molles sont des **critères d'optimisation**, pas des blocages.
Un planning peut violer une contrainte molle (c'est OK).
L'heuristique essaie de minimiser ces violations.

---

## 📝 Prochaines étapes (optionnel)

- [ ] Implémenter F-07 (préférences) → activer penalty_preferences
- [ ] Implémenter métaheuristique (Simulated Annealing)
- [ ] Exporter planning en PDF
- [ ] Notifications email aux soignants
- [ ] Historique des plannings
- [ ] A/B testing d'algorithmes
- [ ] Dashboard analytics

---

## 🆘 Troubleshooting

### Erreur : "Aucun planning généré"

```
→ Vérifier qu'il y a des postes dans la base de données
→ Vérifier que les dates sont correctes (start < end)
→ Vérifier que soignants existent et sont actifs
```

### Erreur : "Contraintes dures violées"

```
→ Vérifier les validateurs dans validators.py
→ Vérifier que les soignants ont les certifications requises
→ Vérifier les absences déclarées
→ Vérifier les contrats actifs
```

### Score trop élevé (bad planning)

```
→ Vérifier les poids des contraintes molles
→ Augmenter weight sur workload_equity pour plus d'équité
→ Diminuer weight sur les contraintes moins importantes
→ Régénérer plusieurs fois (peut varier selon ordre des postes)
```

---

## 📚 Ressources

- Cahier des charges : https://iabd-eigsi.github.io/
- Django REST Framework : https://www.django-rest-framework.org/
- React Documentation : https://react.dev
- Constraint Satisfaction Problem : https://en.wikipedia.org/wiki/Constraint_satisfaction_problem
- Big-O Complexity : https://www.bigocheatsheet.com/

---

**Phase 3 ✅ Complète!**

Générez vos premiers plannings et observez les scores s'améliorer! 🚀
