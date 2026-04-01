from django.contrib import admin
from .models import Soignant, Absence

@admin.register(Soignant)
class SoignantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'specialite')
    search_fields = ('nom', 'prenom')

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('staff', 'start_date', 'expected_end_date')
    search_fields = ('staff__nom', 'staff__prenom')

    # Register your models here.