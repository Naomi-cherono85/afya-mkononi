from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        # Owner is assigned server-side from the request; never trust the client.
        read_only_fields = ['user']