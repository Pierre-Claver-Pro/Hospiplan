from django.contrib import admin
from .models import Soignant, Absence

@admin.register(Soignant)
class SoignantAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'specialite')
    search_fields = ('nom', 'prenom')

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('soignant', 'start_date', 'expected_end_date')  # ← staff → soignant
    search_fields = ('soignant__nom', 'soignant__prenom')           # ← staff → soignant