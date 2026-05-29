"""Rename ChatSession/ChatMessage -> Conversation/Message (data-preserving).

This refactor keeps all existing rows: it renames the models, their primary
key / timestamp / FK fields, swaps the old auto-named indexes for explicitly
named ones, and adds the new ``title`` / ``needs_human`` fields plus the
user-ownership behaviour. Indexes are removed BEFORE the fields they reference
are renamed, to keep migration state valid at each step.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chatbot', '0001_initial'),
    ]

    operations = [
        # 1. Rename the models (renames the underlying tables).
        migrations.RenameModel(old_name='ChatSession', new_name='Conversation'),
        migrations.RenameModel(old_name='ChatMessage', new_name='Message'),

        # 2. Drop the old auto-named indexes before renaming their fields.
        migrations.RemoveIndex(model_name='conversation', name='chatbot_cha_last_ac_31d93b_idx'),
        migrations.RemoveIndex(model_name='message', name='chatbot_cha_session_24e989_idx'),
        migrations.RemoveIndex(model_name='message', name='chatbot_cha_safety__0c9b30_idx'),

        # 3. Rename fields to the new names.
        migrations.RenameField(model_name='conversation', old_name='session_id', new_name='id'),
        migrations.RenameField(model_name='conversation', old_name='started_at', new_name='created_at'),
        migrations.RenameField(model_name='conversation', old_name='last_active_at', new_name='updated_at'),
        migrations.RenameField(model_name='message', old_name='session', new_name='conversation'),

        # 4. New fields.
        migrations.AddField(
            model_name='conversation',
            name='title',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name='conversation',
            name='needs_human',
            field=models.BooleanField(default=False),
        ),

        # 5. User ownership: CASCADE + new related_name.
        migrations.AlterField(
            model_name='conversation',
            name='user',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # 6. Updated ordering.
        migrations.AlterModelOptions(
            name='conversation',
            options={'ordering': ['-updated_at']},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['created_at']},
        ),

        # 7. Add the new explicitly-named indexes.
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['user', '-updated_at'], name='conv_user_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='conversation',
            index=models.Index(fields=['-updated_at'], name='conv_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['conversation', 'created_at'], name='msg_conv_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['safety_category'], name='msg_safety_idx'),
        ),
    ]
