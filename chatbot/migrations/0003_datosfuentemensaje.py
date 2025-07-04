# Generated by Django 5.2.3 on 2025-06-25 02:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0002_contextoprompt'),
    ]

    operations = [
        migrations.CreateModel(
            name='DatosFuenteMensaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datos', models.JSONField()),
                ('mensaje', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='datos_fuente', to='chatbot.mensajechat')),
            ],
        ),
    ]
