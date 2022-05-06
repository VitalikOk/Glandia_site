# Generated by Django 4.0.4 on 2022-05-01 20:36

from django.db import migrations, models
import django.db.models.deletion
import general.enums


class Migration(migrations.Migration):

    dependencies = [
        ('general', '0003_remove_users_expire_remove_users_is_sended_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contacts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, unique=True, verbose_name='имя')),
                ('phone', models.BigIntegerField(default=' - ', unique=True, verbose_name='номер телефона')),
                ('elmail', models.EmailField(max_length=254, unique=True, verbose_name='элетронная почта')),
            ],
        ),
        migrations.RemoveField(
            model_name='users',
            name='elmail',
        ),
        migrations.RemoveField(
            model_name='users',
            name='name',
        ),
        migrations.RemoveField(
            model_name='users',
            name='phone',
        ),
        migrations.AddField(
            model_name='users',
            name='expire',
            field=models.CharField(max_length=64, null=True, verbose_name='дата истечения'),
        ),
        migrations.AddField(
            model_name='users',
            name='is_sended',
            field=models.BooleanField(null=True, verbose_name='отправлено'),
        ),
        migrations.AddField(
            model_name='users',
            name='role',
            field=models.CharField(default=general.enums.Role['MEMBER'], max_length=64, verbose_name='Рольь'),
        ),
        migrations.AddField(
            model_name='users',
            name='vvcard',
            field=models.CharField(default='НЕТ КАРТЫ', max_length=64, verbose_name='номер карты ВВ'),
        ),
        migrations.AlterField(
            model_name='users',
            name='date_in',
            field=models.DateField(auto_now=True, verbose_name='дата добавления'),
        ),
        migrations.AlterField(
            model_name='users',
            name='gid',
            field=models.CharField(max_length=64, null=True, unique=True, verbose_name='идентификатор'),
        ),
        migrations.DeleteModel(
            name='UsersData',
        ),
        migrations.AddField(
            model_name='contacts',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='general.users'),
        ),
    ]