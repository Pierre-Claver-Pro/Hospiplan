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


class Absence(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    absence_type = models.ForeignKey(AbsenceType, on_delete=models.CASCADE)
    start_date = models.DateField()
    expected_end_date = models.DateField()
    actual_end_date = models.DateField(null=True, blank=True)
    is_planned = models.BooleanField(default=True)
    


class Soignant(models.Model):

    nom=models.CharField(max_length=100)

    prenom=models.CharField(max_length=100)

    specialite=models.CharField(max_length=100)

    def __str__(self):

        return self.nom