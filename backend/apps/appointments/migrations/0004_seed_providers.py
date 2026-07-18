"""Seed a default clinic and a few doctors so the booking dropdowns work
out of the box. Idempotent (get_or_create) and reversible-safe.
"""
from datetime import time

from django.db import migrations


DOCTORS = [
    ('Dr. Amina Yusuf', 'General Practitioner'),
    ('Dr. Brian Otieno', 'Paediatrics'),
    ('Dr. Grace Wanjiru', 'Internal Medicine'),
    ('Dr. Samuel Kiptoo', 'Family Medicine'),
]


def seed(apps, schema_editor):
    Clinic = apps.get_model('appointments', 'Clinic')
    Doctor = apps.get_model('appointments', 'Doctor')

    clinic, _ = Clinic.objects.get_or_create(
        name='Afya Mkononi Clinic',
        defaults={
            'address': 'Nairobi, Kenya',
            'phone': '+254 700 000 000',
            'opens_weekday': time(8, 0),
            'closes_weekday': time(17, 0),
            'opens_saturday': time(8, 0),
            'closes_saturday': time(13, 0),
            'open_sunday': False,
            'slot_capacity': 2,
            'is_active': True,
        },
    )

    for name, specialty in DOCTORS:
        Doctor.objects.get_or_create(
            name=name,
            defaults={'specialty': specialty, 'clinic': clinic, 'is_active': True},
        )


def unseed(apps, schema_editor):
    Doctor = apps.get_model('appointments', 'Doctor')
    Clinic = apps.get_model('appointments', 'Clinic')
    Doctor.objects.filter(name__in=[n for n, _ in DOCTORS]).delete()
    Clinic.objects.filter(name='Afya Mkononi Clinic').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0003_clinic_appointment_additional_notes_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
