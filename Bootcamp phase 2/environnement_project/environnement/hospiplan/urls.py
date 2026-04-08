from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('soignants', views.SoignantViewSet)
router.register('postes', views.PosteViewSet)
router.register('absences', views.AbsenceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/affectations/', views.create_affectation),
    path('api/affectations/<int:id>/delete/', views.delete_affectation),
]