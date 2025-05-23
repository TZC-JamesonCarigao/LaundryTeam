# Generated by Django 5.2.1 on 2025-05-15 14:58

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LaundryApplication', '0004_connectionlog_wifinetwork_schedule'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MeterData',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('meterId', models.IntegerField()),
                ('timestamp', models.DateTimeField()),
                ('value', models.FloatField()),
                ('correctionFactor', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Meter Data',
                'verbose_name_plural': 'Meter Data',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='last_switch',
        ),
        migrations.AddField(
            model_name='connectionlog',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='schedule',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='schedule',
            name='name',
            field=models.CharField(default='Unnamed Schedule', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='schedule',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='schedule',
            name='user',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wifinetwork',
            name='name',
            field=models.CharField(default='Unknown', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='wifinetwork',
            name='user',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='wifinetwork',
            name='ssid',
            field=models.CharField(max_length=100),
        ),
    ]
