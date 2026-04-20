from django.db import models


class Staff(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Role(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class StaffRole(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('staff', 'role')


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class StaffSpecialty(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('staff', 'specialty')


class ContractType(models.Model):
    name = models.CharField(max_length=50)
    max_hours_per_week = models.IntegerField(null=True, blank=True)
    leave_days_per_year = models.IntegerField(null=True, blank=True)
    night_shift_allowed = models.BooleanField(default=True)

    def __str__(self):        # ← ajoute ça
        return self.name      # ← et ça


class Contract(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    workload_percent = models.IntegerField(default=100)


class Certification(models.Model):
    name = models.CharField(max_length=150)


class CertificationDependency(models.Model):
    parent_cert = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name="parent_certifications"
    )

    required_cert = models.ForeignKey(
        Certification,
        on_delete=models.CASCADE,
        related_name="required_certifications"
    )

    class Meta:
        unique_together = ('parent_cert', 'required_cert')


class StaffCertification(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    obtained_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)


class Service(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    bed_capacity = models.IntegerField()
    criticality_level = models.IntegerField(default=1)
    seuil_minimum = models.IntegerField(default=1)



class CareUnit(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)


class ServiceStatus(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)


class StaffServiceAssignment(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)


class ShiftType(models.Model):
    name = models.CharField(max_length=50)
    duration_hours = models.IntegerField()
    requires_rest_after = models.BooleanField(default=True)


class Shift(models.Model):
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE)
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    min_staff = models.IntegerField(default=1)
    max_staff = models.IntegerField(null=True, blank=True)


class ShiftRequiredCertification(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('shift', 'certification')


class ShiftAssignment(models.Model):
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)


class AbsenceType(models.Model):
    name = models.CharField(max_length=50)
    impacts_quota = models.BooleanField(default=True)


class Soignant(models.Model):

    nom=models.CharField(max_length=100)

    prenom=models.CharField(max_length=100)

    specialite=models.CharField(max_length=100)

    phone_number=models.CharField(max_length=20)
    
    is_active = models.BooleanField(default=True, help_text="Soignant actif dans le système")

    def __str__(self):

        return self.nom
    
class Absence(models.Model):
    soignant = models.ForeignKey('Soignant', on_delete=models.CASCADE)  # ← était "staff"
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.CASCADE)
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    is_planned = models.BooleanField(default=True)
    


    
class Poste(models.Model):
    TYPE_CHOICES = [('jour', 'Jour'), ('nuit', 'Nuit'), ('weekend', 'Weekend')]
    
    care_unit = models.ForeignKey(CareUnit, on_delete=models.CASCADE, null=True, blank=True) 
    type_garde = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    min_soignants = models.IntegerField(default=1)

    def __str__(self):
        return f"Poste {self.type_garde} - {self.date_debut}"


class Affectation(models.Model):
    soignant = models.ForeignKey(Soignant, on_delete=models.CASCADE)
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('soignant', 'poste')



class PosteCertificationRequise(models.Model):
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE, related_name='certifications_requises')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('poste', 'certification')



class SoignantCertification(models.Model):
    soignant = models.ForeignKey(Soignant, on_delete=models.CASCADE, related_name='certifications')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    obtained_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)

class SoignantContrat(models.Model):
    soignant = models.ForeignKey(Soignant, on_delete=models.CASCADE, related_name='contrats')
    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)


# ═══════════════════════════════════════════════════════════════
# PHASE 3 : GÉNÉRATION AUTOMATIQUE DE PLANNINGS
# ═══════════════════════════════════════════════════════════════

class Planning(models.Model):
    """
    Un planning généré pour une période donnée.
    Représente l'ensemble des affectations d'une semaine/mois.
    """
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('generated', 'Généré'),
        ('edited', 'Modifié'),
        ('approved', 'Approuvé'),
        ('published', 'Publié')
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Score global du planning
    score_total = models.FloatField(default=0.0, help_text="Score des contraintes molles (plus bas = mieux)")
    
    # Métadonnées de génération
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by_algorithm = models.CharField(
        max_length=50, 
        default='least-loaded',
        help_text="Heuristique utilisée pour générer ce planning"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} → {self.end_date})"


class AffectationPlanning(models.Model):
    """
    Chaque affectation soignant ← → poste dans un planning généré.
    Peut être modifiée manuellement après génération (toujours sous contraintes dures).
    """
    planning = models.ForeignKey(Planning, on_delete=models.CASCADE, related_name='affectations')
    soignant = models.ForeignKey(Soignant, on_delete=models.CASCADE)
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE)
    
    # Métadonnées
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_manual = models.BooleanField(
        default=False, 
        help_text="True si affectation modifiée manuellement après génération"
    )
    
    class Meta:
        unique_together = ('planning', 'soignant', 'poste')
        indexes = [
            models.Index(fields=['planning', 'soignant']),
            models.Index(fields=['planning', 'poste']),
        ]

    def __str__(self):
        return f"{self.soignant.nom} → {self.poste}"


class ScorePlanning(models.Model):
    """
    Détail du score d'un planning : pénalités pour chaque contrainte molle.
    Permet d'analyser où le planning peut être amélioré.
    """
    planning = models.OneToOneField(Planning, on_delete=models.CASCADE, related_name='score_detail')
    
    # Contraintes molles : pénalités
    penalty_night_consecutive = models.FloatField(
        default=0.0,
        help_text="Pénalité : trop de nuits consécutives"
    )
    penalty_preferences = models.FloatField(
        default=0.0,
        help_text="Pénalité : préférences de créneaux non respectées"
    )
    penalty_workload_equity = models.FloatField(
        default=0.0,
        help_text="Pénalité : charge inégale entre soignants (écart-type élevé)"
    )
    penalty_service_changes = models.FloatField(
        default=0.0,
        help_text="Pénalité : trop de changements de service"
    )
    penalty_weekend_equity = models.FloatField(
        default=0.0,
        help_text="Pénalité : inégalité dans les week-ends travaillés"
    )
    penalty_continuity = models.FloatField(
        default=0.0,
        help_text="Pénalité : manque de continuité de soins"
    )
    
    # Autres métriques
    total_shifts_assigned = models.IntegerField(default=0)
    uncovered_shifts = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Score pour {self.planning.name}"


class ConstrainteSouple(models.Model):
    """
    Configuration des poids pour les contraintes molles.
    Permet de configurer l'importance de chaque contrainte molle
    sans modifier le code.
    """
    CONSTRAINT_TYPES = [
        ('night_consecutive', 'Nuits consécutives'),
        ('preferences', 'Préférences de créneaux'),
        ('workload_equity', 'Équité de charge'),
        ('service_changes', 'Changements de service'),
        ('weekend_equity', 'Équité week-ends'),
        ('continuity', 'Continuité de soins'),
    ]
    
    constraint_type = models.CharField(max_length=50, choices=CONSTRAINT_TYPES, unique=True)
    weight = models.FloatField(default=1.0, help_text="Poids (0 = ignoré, >0 = actif)")
    is_active = models.BooleanField(default=True)
    
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Contraintes souples"

    def __str__(self):
        return f"{self.get_constraint_type_display()} (w={self.weight})"