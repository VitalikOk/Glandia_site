# Generated by Django 4.0.4 on 2022-04-25 15:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='users',
            name='phone',
            field=models.BigIntegerField(default=' - ', unique=True, verbose_name='номер телефона'),
        ),
    ]