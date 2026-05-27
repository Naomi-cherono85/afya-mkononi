from rest_framework import mixins, viewsets
from .models import Reminder
from .serializers import ReminderSerializer

class ReminderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer

# Create your views here.
