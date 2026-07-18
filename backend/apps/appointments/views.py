from datetime import timedelta

from django.utils.dateparse import parse_date
from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Appointment, Clinic, Doctor
from .serializers import AppointmentSerializer
from .services.availability import get_available_slots, get_day_availability

# Cap the calendar range a client can request in one call.
MAX_DAY_RANGE = 62


def _lookup(model, raw_id):
    """Fetch an active provider by id, tolerating blank / bad values."""
    if not raw_id:
        return None
    try:
        return model.objects.filter(is_active=True).filter(pk=int(raw_id)).first()
    except (TypeError, ValueError):
        return None


class AppointmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    """Booking API used by the appointment-book page.

    Scoped to the signed-in user for list/create. Availability endpoints are
    read-only and power the smart date/time pickers. Full management
    (edit/cancel/reschedule) lives in the server-rendered frontend views.
    """

    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Appointment.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def availability(self, request):
        """Bookable slots for a single date. ``?date=YYYY-MM-DD[&clinic=&doctor=]``."""
        target = parse_date(request.query_params.get('date', ''))
        if not target:
            return Response({'detail': 'A valid ?date=YYYY-MM-DD is required.'}, status=400)
        clinic = _lookup(Clinic, request.query_params.get('clinic'))
        doctor = _lookup(Doctor, request.query_params.get('doctor'))
        return Response({
            'date': target.isoformat(),
            'slots': get_available_slots(target, clinic=clinic, doctor=doctor),
        })

    @action(detail=False, methods=['get'])
    def day_availability(self, request):
        """Per-day availability for a range. ``?start=&end=[&clinic=&doctor=]``."""
        start = parse_date(request.query_params.get('start', ''))
        end = parse_date(request.query_params.get('end', ''))
        if not start or not end or end < start:
            return Response({'detail': 'Valid ?start= and ?end= dates are required.'}, status=400)
        if (end - start).days > MAX_DAY_RANGE:
            end = start + timedelta(days=MAX_DAY_RANGE)
        clinic = _lookup(Clinic, request.query_params.get('clinic'))
        doctor = _lookup(Doctor, request.query_params.get('doctor'))
        return Response({
            'days': get_day_availability(start, end, clinic=clinic, doctor=doctor),
        })
