from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('soignants', views.SoignantViewSet)
router.register('postes', views.PosteViewSet)
router.register('absences', views.AbsenceViewSet)
router.register('affectations', views.AffectationViewSet)

# Phase 3 : Plannings automatiques
router.register('plannings', views.PlanningViewSet, basename='planning')
router.register('affectations-planning', views.AffectationPlanningViewSet, basename='affectation-planning')
router.register('contraintes-souples', views.ConstrainteSoupleViewSet, basename='contrainte-souple')

urlpatterns = [
    path('', include(router.urls)),
]