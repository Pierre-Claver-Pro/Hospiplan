#!/usr/bin/env python
"""
Script pour générer automatiquement des postes de test pour Phase 3
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'environnement.settings')
django.setup()

from hospiplan.models import Poste, CareUnit, Service

def generate_postes():
    """Génère 30 postes sur 2 semaines (19/01 → 01/02)"""
    
    # Récupérer ou créer un service/unit
    try:
        service = Service.objects.first()
        unit = CareUnit.objects.first()
    except:
        print("❌ Pas de Service ou CareUnit trouvé!")
        return
    
    if not service or not unit:
        print("❌ Service ou CareUnit manquant!")
        return
    
    start_date = datetime(2025, 1, 19, 10, 0, 0)
    types_garde = ['jour', 'nuit', 'weekend']
    durations = {
        'jour': 6,      # 6 heures
        'nuit': 8,      # 8 heures
        'weekend': 8    # 8 heures
    }
    
    postes_created = 0
    
    # Créer des postes pour 2 semaines
    for day_offset in range(14):  # 14 jours
        current_date = start_date + timedelta(days=day_offset)
        
        # 2 postes par jour (jour + nuit/weekend)
        for garde_type in types_garde[:2]:  # jour et nuit/weekend
            if garde_type == 'jour':
                debut = current_date.replace(hour=9, minute=0)
                fin = debut + timedelta(hours=durations['jour'])
            elif garde_type == 'nuit':
                debut = current_date.replace(hour=21, minute=0)
                fin = (current_date + timedelta(days=1)).replace(hour=5, minute=0)
            else:  # weekend
                debut = current_date.replace(hour=8, minute=0)
                fin = debut + timedelta(hours=durations['weekend'])
            
            # Créer le poste
            poste, created = Poste.objects.get_or_create(
                date_debut=debut,
                date_fin=fin,
                type_garde=garde_type,
                defaults={
                    'care_unit': unit,
                    'min_soignants': 1,
                }
            )
            
            if created:
                postes_created += 1
                print(f"✅ Créé: {garde_type.upper()} - {debut.strftime('%d/%m %H:%M')} → {fin.strftime('%d/%m %H:%M')}")
    
    print(f"\n✨ {postes_created} nouveaux postes créés!")

if __name__ == '__main__':
    generate_postes()
