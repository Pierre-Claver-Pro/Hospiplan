from django.shortcuts import render
from .models import Soignant
from django.views.decorators.csrf import csrf_exempt

def home(request):

    return render(request,'home.html')

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


@csrf_exempt
def create_affectation(request):

    if request.method=="POST":

        soignant_id=request.POST.get('soignant')

        poste_id=request.POST.get('poste')

        soignant=Soignant.objects.get(id=soignant_id)

        poste=Poste.objects.get(id=poste_id)

        # validation absence

        absence=Absence.objects.filter(

            soignant=soignant,

            date_debut__lte=poste.date_debut,

            date_fin__gte=poste.date_debut

        )

        if absence.exists():

            return JsonResponse({

                "error":"Soignant en absence"

            })

        Affectation.objects.create(

            soignant=soignant,

            poste=poste

        )

        return JsonResponse({

            "message":"Affectation créée"

        })