from rest_framework import mixins, viewsets
from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

# Create your views here.
