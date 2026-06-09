from django.db import migrations

# (title, content, category) for the starter set of tips. Categories use the
# HealthTip.Category values defined on the model.
SEED_TIPS = [
    ('Stay Hydrated',
     'Drink enough water throughout the day to maintain healthy body functions and energy levels.',
     'GENERAL'),
    ('Get Enough Sleep',
     'Adults should aim for 7–9 hours of quality sleep each night.',
     'GENERAL'),
    ('Wash Your Hands',
     'Regular handwashing helps prevent infections and protects those around you.',
     'PREVENTION'),
    ('Exercise Regularly',
     'Aim for at least 30 minutes of physical activity most days of the week.',
     'GENERAL'),
    ('Eat More Fruits and Vegetables',
     'A balanced diet supports overall health and wellbeing.',
     'NUTRITION'),
    ('Manage Stress',
     'Practice relaxation techniques and take time to rest.',
     'MENTAL_HEALTH'),
    ('Monitor Blood Pressure',
     'Regular checks can help detect problems early.',
     'CHRONIC'),
    ('Take Medication as Prescribed',
     "Follow your healthcare provider's instructions carefully.",
     'CHRONIC'),
    ('Attend Regular Checkups',
     'Preventive care helps identify issues before they become serious.',
     'PREVENTION'),
    ('Avoid Smoking',
     'Avoid tobacco products to reduce health risks.',
     'PREVENTION'),
    ('Maintain a Healthy Weight',
     'Balanced nutrition and activity help support long-term health.',
     'NUTRITION'),
    ('Protect Yourself From Mosquitoes',
     'Use mosquito nets and repellents where appropriate.',
     'PREVENTION'),
    ('Practice Safe Food Handling',
     'Proper food preparation helps prevent foodborne illnesses.',
     'NUTRITION'),
    ('Limit Sugar Intake',
     'Reduce sugary drinks and snacks when possible.',
     'NUTRITION'),
    ('Reduce Salt Consumption',
     'Lower salt intake to support healthy blood pressure.',
     'NUTRITION'),
    ('Protect Your Mental Health',
     'Stay connected with supportive people and communities.',
     'MENTAL_HEALTH'),
    ('Stay Up To Date With Vaccinations',
     'Vaccines help protect individuals and communities.',
     'PREVENTION'),
    ('Practice Good Posture',
     'Proper posture helps reduce strain and discomfort.',
     'GENERAL'),
    ('Limit Alcohol Consumption',
     'Drink responsibly and within recommended guidelines.',
     'PREVENTION'),
    ('Seek Care Early When Symptoms Persist',
     'Persistent symptoms should be evaluated by a healthcare professional.',
     'GENERAL'),
]


def seed_health_tips(apps, schema_editor):
    HealthTip = apps.get_model('health_tips', 'HealthTip')
    for title, content, category in SEED_TIPS:
        # Idempotent: re-running (or running after manual edits) won't duplicate.
        HealthTip.objects.get_or_create(
            title=title,
            defaults={'content': content, 'category': category, 'is_active': True},
        )


def unseed_health_tips(apps, schema_editor):
    HealthTip = apps.get_model('health_tips', 'HealthTip')
    titles = [title for title, _, _ in SEED_TIPS]
    HealthTip.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('health_tips', '0002_rename_description_healthtip_content_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_health_tips, unseed_health_tips),
    ]
