from rest_framework import serializers
from .models import (
    Soignant, Absence, Poste, Affectation,
    Planning, AffectationPlanning, ScorePlanning, ConstrainteSouple
)


class SoignantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Soignant
        fields = '__all__'


class AbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Absence
        fields = '__all__'


class PosteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poste
        fields = '__all__'


class AffectationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Affectation
        fields = '__all__'


# ═══════════════════════════════════════════════════════════════
# PHASE 3 : SERIALIZERS POUR PLANNING AUTOMATIQUE
# ═══════════════════════════════════════════════════════════════

class AffectationPlanningSerializer(serializers.ModelSerializer):
    """Affectation au sein d'un planning généré"""
    soignant_nom = serializers.CharField(source='soignant.nom', read_only=True)
    poste_detail = PosteSerializer(source='poste', read_only=True)
    
    class Meta:
        model = AffectationPlanning
        fields = [
            'id', 'planning', 'soignant', 'soignant_nom', 
            'poste', 'poste_detail', 'assigned_at', 'is_manual'
        ]


class ScorePlanningSerializer(serializers.ModelSerializer):
    """Détail du score des contraintes molles"""
    class Meta:
        model = ScorePlanning
        fields = [
            'id', 'planning',
            'penalty_night_consecutive',
            'penalty_preferences',
            'penalty_workload_equity',
            'penalty_service_changes',
            'penalty_weekend_equity',
            'penalty_continuity',
            'total_shifts_assigned',
            'uncovered_shifts',
        ]


class PlanningDetailSerializer(serializers.ModelSerializer):
    """Détail complet d'un planning avec toutes ses affectations"""
    affectations = AffectationPlanningSerializer(many=True, read_only=True)
    score_detail = ScorePlanningSerializer(read_only=True)
    
    class Meta:
        model = Planning
        fields = [
            'id', 'name', 'description', 
            'start_date', 'end_date', 'status',
            'score_total', 'generated_by_algorithm',
            'generated_at', 'created_at', 'updated_at',
            'affectations', 'score_detail'
        ]


class PlanningListSerializer(serializers.ModelSerializer):
    """Liste simple des plannings sans détail"""
    class Meta:
        model = Planning
        fields = [
            'id', 'name', 'start_date', 'end_date', 
            'status', 'score_total', 'generated_at'
        ]


class PlanningGenerateSerializer(serializers.Serializer):
    """Sérialiseur pour la requête de génération"""
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)
    name = serializers.CharField(required=False, allow_blank=True)
    algorithm = serializers.ChoiceField(
        choices=['least-loaded'], 
        default='least-loaded'
    )
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                "start_date doit être avant end_date"
            )
        return data


class ConstrainteSoupleSerializer(serializers.ModelSerializer):
    """Configuration des contraintes molles"""
    class Meta:
        model = ConstrainteSouple
        fields = [
            'id', 'constraint_type', 'weight', 'is_active', 'description'
        ]