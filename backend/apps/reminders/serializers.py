from rest_framework import serializers
from .models import Reminder

class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = '__all__'
        # Owner is assigned server-side from the request; never trust the client.
        read_only_fields = ['user']