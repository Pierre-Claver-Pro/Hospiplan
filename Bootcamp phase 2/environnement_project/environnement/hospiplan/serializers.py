from rest_framework import serializers

from .models import Soignant,Absence


class SoignantSerializer(serializers.ModelSerializer):

    class Meta:

        model = Soignant

        fields = '__all__'


class AbsenceSerializer(serializers.ModelSerializer):

    class Meta:

        model = Absence

        fields = '__all__'