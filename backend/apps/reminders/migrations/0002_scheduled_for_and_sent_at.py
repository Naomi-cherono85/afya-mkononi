from django.db import migrations, models
from django.utils import timezone


def backfill_scheduled_for(apps, schema_editor):
    Reminder = apps.get_model('reminders', 'Reminder')
    tz = timezone.get_current_timezone()
    for r in Reminder.objects.all():
        naive = timezone.datetime.combine(r.reminder_date, r.reminder_time)
        r.scheduled_for = timezone.make_aware(naive, tz)
        r.save(update_fields=['scheduled_for'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('reminders', '0001_initial'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='reminder',
            name='reminders_r_status_0f30ec_idx',
        ),
        migrations.AddField(
            model_name='reminder',
            name='scheduled_for',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='reminder',
            name='sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_scheduled_for, noop_reverse),
        migrations.RemoveField(
            model_name='reminder',
            name='reminder_date',
        ),
        migrations.RemoveField(
            model_name='reminder',
            name='reminder_time',
        ),
        migrations.AlterField(
            model_name='reminder',
            name='scheduled_for',
            field=models.DateTimeField(),
        ),
        migrations.AddIndex(
            model_name='reminder',
            index=models.Index(fields=['status', 'scheduled_for'], name='reminders_r_status_42a620_idx'),
        ),
    ]
