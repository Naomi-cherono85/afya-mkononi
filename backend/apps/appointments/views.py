from rest_framework import mixins, permissions, viewsets

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """Booking API used by the appointment-book page.

    Scoped to the signed-in user: each patient only ever lists and creates
    their own appointments. Full management (edit/cancel/reschedule) lives in
    the server-rendered frontend views.
    """

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
