from django.urls import path

from . import views

urlpatterns=[

    path('',views.soignant_list,name="soignant_list"),

    path('<int:id>/',views.soignant_detail,name="soignant_detail"),

    path('absences/',views.absence_list,name="absence_list"),

    path('absences/<int:id>/',views.absence_detail,name="absence_detail"),

]