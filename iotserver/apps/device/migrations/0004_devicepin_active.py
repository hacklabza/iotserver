# Generated by Django 4.0.6 on 2022-07-20 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0003_devicepin_interval'),
    ]

    operations = [
        migrations.AddField(
            model_name='devicepin',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
