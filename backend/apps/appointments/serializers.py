from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Appointment
from .services.availability import validate_slot


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        # Owner is assigned server-side from the request; never trust the client.
        read_only_fields = ['user']

    def validate(self, attrs):
        appt_date = attrs.get('preferred_date')
        appt_time = attrs.get('preferred_time')
        if appt_date and appt_time:
            try:
                validate_slot(
                    appt_date, appt_time,
                    clinic=attrs.get('clinic'),
                    doctor=attrs.get('doctor'),
                )
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'preferred_time': exc.messages})
        return attrs
