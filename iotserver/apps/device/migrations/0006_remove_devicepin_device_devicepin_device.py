# Generated by Django 4.1 on 2022-08-17 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0005_alter_device_hostname_alter_device_ip_address_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='devicepin',
            name='device',
        ),
        migrations.AddField(
            model_name='devicepin',
            name='device',
            field=models.ManyToManyField(related_name='pins', to='device.device'),
        ),
    ]