from rest_framework import serializers
from .models import Soignant, Absence, Poste, Affectation


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