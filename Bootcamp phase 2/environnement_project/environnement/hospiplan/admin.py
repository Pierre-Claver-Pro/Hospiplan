from django.contrib import admin
from .models import (
    Soignant, Absence, Poste, Affectation,
    SoignantContrat, ContractType,
    SoignantCertification, Certification,
    Service, CareUnit
)

admin.site.register(Soignant)
admin.site.register(Absence)
admin.site.register(Poste)
admin.site.register(Affectation)
admin.site.register(SoignantContrat)
admin.site.register(ContractType)
admin.site.register(SoignantCertification)
admin.site.register(Certification)
admin.site.register(Service)
admin.site.register(CareUnit)