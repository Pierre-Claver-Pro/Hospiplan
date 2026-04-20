
from django.contrib import admin
from django.urls import path, include
from hospiplan import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('hospiplan.urls')),  # routes API avec /api/ prefix
    path('', views.home, name="home"),              # page d'accueil
]
