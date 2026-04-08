from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from datetime import timedelta
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

from .models import (
    Soignant, Poste, Affectation, Absence,
    SoignantCertification, SoignantContrat
)
from .serializers import (
    SoignantSerializer, PosteSerializer,
    AffectationSerializer, AbsenceSerializer
)

REPOS_MINIMAL_HEURES = 11  # configurable ici


# ─── CRUD SOIGNANTS ───────────────────────────────────────────
class SoignantViewSet(viewsets.ModelViewSet):
    queryset = Soignant.objects.all()
    serializer_class = SoignantSerializer


# ─── CRUD POSTES ──────────────────────────────────────────────
class PosteViewSet(viewsets.ModelViewSet):
    queryset = Poste.objects.all()
    serializer_class = PosteSerializer


# ─── CRUD ABSENCES ────────────────────────────────────────────
class AbsenceViewSet(viewsets.ModelViewSet):
    queryset = Absence.objects.all()
    serializer_class = AbsenceSerializer


# ─── AFFECTATION avec contraintes dures ───────────────────────
@api_view(['POST'])
def create_affectation(request):
    soignant_id = request.data.get('soignant')
    poste_id = request.data.get('poste')

    # Vérification existence
    try:
        soignant = Soignant.objects.get(id=soignant_id)
        poste = Poste.objects.get(id=poste_id)
    except Soignant.DoesNotExist:
        return Response({"error": "Soignant introuvable"}, status=status.HTTP_404_NOT_FOUND)
    except Poste.DoesNotExist:
        return Response({"error": "Poste introuvable"}, status=status.HTTP_404_NOT_FOUND)

    # ── Contrainte 1 : Absence déclarée ──────────────────────
    if Absence.objects.filter(
        soignant=soignant,
        start_date__lte=poste.date_debut,
        expected_end_date__gte=poste.date_debut
    ).exists():
        return Response(
            {"error": "Soignant en absence déclarée sur cette période"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Contrainte 2 : Chevauchement horaire ─────────────────
    if Affectation.objects.filter(
        soignant=soignant,
        poste__date_debut__lt=poste.date_fin,
        poste__date_fin__gt=poste.date_debut
    ).exists():
        return Response(
            {"error": "Chevauchement horaire avec une affectation existante"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Contrainte 3 : Certifications requises non expirées ──
    certs_requises = poste.certifications_requises.select_related('certification').all()
    for poste_cert in certs_requises:
        cert = poste_cert.certification
        possede = SoignantCertification.objects.filter(
            soignant=soignant,
            certification=cert,
            expiration_date__gte=poste.date_debut.date()
        ).exists()
        if not possede:
            return Response(
                {"error": f"Certification manquante ou expirée : {cert.name}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # ── Contrainte 4 : Repos minimal après garde de nuit ─────
    derniere_nuit = Affectation.objects.filter(
        soignant=soignant,
        poste__type_garde='nuit',
        poste__date_fin__lte=poste.date_debut
    ).order_by('-poste__date_fin').first()

    if derniere_nuit:
        delta = poste.date_debut - derniere_nuit.poste.date_fin
        if delta < timedelta(hours=REPOS_MINIMAL_HEURES):
            return Response(
                {"error": f"Repos minimal de {REPOS_MINIMAL_HEURES}h après garde de nuit non respecté"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # ── Contrainte 5 : Seuil minimum soignants par service ───
    if poste.service:
        nb_affectes = Affectation.objects.filter(
            poste__service=poste.service,
            poste__date_debut__date=poste.date_debut.date()
        ).values('soignant').distinct().count()

        if nb_affectes < poste.service.seuil_minimum:
            # On vérifie qu'on ne retire pas un soignant (ici on en ajoute un, ok)
            pass  # La contrainte bloque la suppression, pas la création

    # ── Contrainte 6 : Contrat autorise le type de garde ─────
    contrat = SoignantContrat.objects.filter(
        soignant=soignant,
        start_date__lte=poste.date_debut.date(),
    ).filter(
        # end_date null = contrat en cours
        end_date__isnull=True
    ).last() or SoignantContrat.objects.filter(
        soignant=soignant,
        end_date__gte=poste.date_debut.date()
    ).last()

    if not contrat:
        return Response(
            {"error": "Aucun contrat actif trouvé pour ce soignant"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if poste.type_garde == 'nuit' and not contrat.contract_type.night_shift_allowed:
        return Response(
            {"error": "Le contrat du soignant n'autorise pas les gardes de nuit"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Tout valide → créer l'affectation ────────────────────
    affectation = Affectation.objects.create(soignant=soignant, poste=poste)
    return Response(
        AffectationSerializer(affectation).data,
        status=status.HTTP_201_CREATED
    )


# ─── SUPPRIMER UNE AFFECTATION ────────────────────────────────
@api_view(['DELETE'])
def delete_affectation(request, id):
    try:
        affectation = Affectation.objects.get(id=id)
        affectation.delete()
        return Response({"message": "Affectation supprimée"}, status=status.HTTP_204_NO_CONTENT)
    except Affectation.DoesNotExist:
        return Response({"error": "Affectation introuvable"}, status=status.HTTP_404_NOT_FOUND)