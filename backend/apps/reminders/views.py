from rest_framework import mixins, permissions, viewsets

from .models import Reminder
from .serializers import ReminderSerializer


class ReminderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """Reminder API used by the reminder-create page.

    Scoped to the signed-in user: each patient only ever lists and creates
    their own reminders. Full management (complete/snooze/edit/delete) lives in
    the server-rendered frontend views.
    """

    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
