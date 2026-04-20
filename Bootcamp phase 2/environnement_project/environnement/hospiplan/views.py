from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, action
from datetime import timedelta
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

from .models import (
    Soignant, Poste, Affectation, Absence,
    SoignantCertification, SoignantContrat,
    Planning, AffectationPlanning, ScorePlanning, ConstrainteSouple
)
from .serializers import (
    SoignantSerializer, PosteSerializer,
    AffectationSerializer, AbsenceSerializer,
    PlanningDetailSerializer, PlanningListSerializer, PlanningGenerateSerializer,
    AffectationPlanningSerializer, ScorePlanningSerializer,
    ConstrainteSoupleSerializer
)
from .validators import validate_affectation
from .planning_generator import (
    PlanningGenerator, generer_planning_simple, PlanningGeneratorError
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


# ─── CRUD AFFECTATIONS avec contraintes dures ─────────────────
class AffectationViewSet(viewsets.ModelViewSet):
    queryset = Affectation.objects.all()
    serializer_class = AffectationSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crée une affectation en validant toutes les contraintes dures.
        """
        soignant_id = request.data.get('soignant')
        poste_id = request.data.get('poste')

        # Vérification existence
        try:
            soignant = Soignant.objects.get(id=soignant_id)
            poste = Poste.objects.get(id=poste_id)
        except Soignant.DoesNotExist:
            return Response(
                {"error": "Soignant introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Poste.DoesNotExist:
            return Response(
                {"error": "Poste introuvable"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {str(e)}")
            return Response(
                {"error": f"Erreur interne: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            # Valider TOUTES les contraintes dures
            is_valid, errors = validate_affectation(soignant, poste)
            
            if not is_valid:
                return Response(
                    {
                        "error": "Affectation impossible - Contraintes dures violées",
                        "details": errors,
                        "soignant": f"{soignant.prenom} {soignant.nom}",
                        "poste": f"{poste.type_garde} ({poste.date_debut} à {poste.date_fin})"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Tout est valide → créer l'affectation
            affectation = Affectation.objects.create(soignant=soignant, poste=poste)
            return Response(
                AffectationSerializer(affectation).data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la création d'affectation: {str(e)}")
            return Response(
                {"error": f"Erreur serveur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ═══════════════════════════════════════════════════════════════
# PHASE 3 : ENDPOINTS POUR GÉNÉRATION AUTOMATIQUE DE PLANNING
# ═══════════════════════════════════════════════════════════════

class PlanningViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les plannings générés"""
    queryset = Planning.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlanningDetailSerializer
        elif self.action == 'list':
            return PlanningListSerializer
        elif self.action == 'generate':
            return PlanningGenerateSerializer
        return PlanningDetailSerializer
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Endpoint POST /plannings/generate
        
        Génère automatiquement un planning pour une période donnée.
        
        Requête JSON:
        {
            "start_date": "2025-01-06",
            "end_date": "2025-01-12",
            "name": "Planning Semaine 1 (optionnel)",
            "algorithm": "least-loaded"
        }
        
        Réponse: Le planning généré avec toutes ses affectations et son score.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']
            name = serializer.validated_data.get('name', None)
            algorithm = serializer.validated_data.get('algorithm', 'least-loaded')
            
            # Générer le planning
            logger.info(f"Génération planning {start_date} → {end_date} (algo: {algorithm})")
            generator = PlanningGenerator(start_date, end_date, algorithm=algorithm)
            planning = generator.generate(name=name)
            
            # Retourner le planning généré avec détail complet
            result_serializer = PlanningDetailSerializer(planning)
            return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
        except PlanningGeneratorError as e:
            logger.error(f"Erreur génération planning: {str(e)}")
            return Response(
                {"error": f"Erreur génération: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Erreur serveur génération: {str(e)}")
            return Response(
                {"error": f"Erreur serveur: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def score(self, request, pk=None):
        """
        Endpoint GET /plannings/{id}/score
        
        Récupère le détail du score des contraintes molles pour un planning.
        """
        try:
            planning = self.get_object()
            score = ScorePlanning.objects.get(planning=planning)
            serializer = ScorePlanningSerializer(score)
            return Response(serializer.data)
        except ScorePlanning.DoesNotExist:
            return Response(
                {"error": "Pas de score trouvé pour ce planning"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def affectations(self, request, pk=None):
        """
        Endpoint GET /plannings/{id}/affectations
        
        Liste toutes les affectations d'un planning.
        """
        planning = self.get_object()
        affectations = AffectationPlanning.objects.filter(planning=planning)
        serializer = AffectationPlanningSerializer(affectations, many=True)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        """
        Liste tous les plannings avec filtrage optionnel.
        
        Paramètres de query (optionnels):
        - status=generated : filtrer par statut
        - start_date=2025-01-01 : filtrer par date de début
        - end_date=2025-01-31 : filtrer par date de fin
        """
        queryset = self.get_queryset()
        
        # Filtres optionnels
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        
        end_date = request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ConstrainteSoupleViewSet(viewsets.ModelViewSet):
    """ViewSet pour configurer les contraintes molles"""
    queryset = ConstrainteSouple.objects.all()
    serializer_class = ConstrainteSoupleSerializer


class AffectationPlanningViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les affectations dans un planning"""
    queryset = AffectationPlanning.objects.all()
    serializer_class = AffectationPlanningSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Crée une affectation dans un planning généré.
        Toujours soumise aux contraintes dures.
        """
        planning_id = request.data.get('planning')
        soignant_id = request.data.get('soignant')
        poste_id = request.data.get('poste')
        
        try:
            planning = Planning.objects.get(id=planning_id)
            soignant = Soignant.objects.get(id=soignant_id)
            poste = Poste.objects.get(id=poste_id)
        except (Planning.DoesNotExist, Soignant.DoesNotExist, Poste.DoesNotExist) as e:
            return Response(
                {"error": f"Ressource introuvable: {e}"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Valider les contraintes dures
        is_valid, errors = validate_affectation(soignant, poste)
        
        if not is_valid:
            return Response(
                {
                    "error": "Contraintes dures violées",
                    "details": errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            affectation = AffectationPlanning.objects.create(
                planning=planning,
                soignant=soignant,
                poste=poste,
                is_manual=True
            )
            
            # Recalculer le score après modification manuelle
            # TODO: implémenter la recalculation du score
            
            serializer = self.get_serializer(affectation)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Erreur création affectation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )