# Generated by Django 4.0.4 on 2022-05-06 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0007_alter_contacts_phone'),
    ]

    operations = [
        migrations.CreateModel(
            name='Roles',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(max_length=64, unique=True, verbose_name='Role')),
            ],
        ),
        migrations.AlterField(
            model_name='users',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='general.roles'),
        ),
    ]
