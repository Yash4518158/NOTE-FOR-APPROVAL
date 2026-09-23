import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0005_notificationtemplate'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationtemplate',
            name='is_email_active',
            field=models.BooleanField(db_column='IsEmailActive', default=True),
        ),
        migrations.AddField(
            model_name='notificationtemplate',
            name='is_inapp_active',
            field=models.BooleanField(db_column='IsInAppActive', default=True),
        ),
        migrations.CreateModel(
            name='InAppNotification',
            fields=[
                ('notification_id', models.UUIDField(db_column='NotificationID', default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('event_type', models.CharField(db_column='EventType', max_length=50)),
                ('title', models.CharField(db_column='Title', max_length=255)),
                ('message', models.TextField(db_column='Message')),
                ('is_read', models.BooleanField(db_column='IsRead', default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_column='CreatedAt')),
                ('nfa_request', models.ForeignKey(blank=True, db_column='NFARequestID', null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentication.nfarequest')),
                ('user', models.ForeignKey(db_column='UserID', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='authentication.systemuser')),
            ],
            options={
                'db_table': 'InAppNotifications',
            },
        ),
    ]
