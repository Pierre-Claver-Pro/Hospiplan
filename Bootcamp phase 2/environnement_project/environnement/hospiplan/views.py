from django.shortcuts import render
from .models import Soignant

def soignant_list(request):

    soignants = Soignant.objects.all()

    return render(request,'soignant_list.html',{
        'soignants':soignants
    })


def soignant_detail(request,id):

    soignant = Soignant.objects.get(id=id)

    return render(request,'soignant_detail.html',{
        'soignant':soignant
    })

from .models import Absence

def absence_list(request):

    absences = Absence.objects.all()

    return render(request,'absence_list.html',{
        'absences':absences
    })


def absence_detail(request,id):

    absence = Absence.objects.get(id=id)

    return render(request,'absence_detail.html',{
        'absence':absence
    })