# Generated by Django 4.0.4 on 2022-06-28 15:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventsvisits',
            name='special_amount',
            field=models.IntegerField(default=0, verbose_name='Специальная сумма для зачтсления бонусов'),
        ),
    ]
