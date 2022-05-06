from django.db import models
from datetime import datetime
from general.enums import Role


class Roles(models.Model):
    role = models.CharField(verbose_name='Role', max_length=64, unique=True, null=False)

class Users(models.Model):
    gid = models.CharField(verbose_name = "идентификатор", max_length=64, unique=True, null=True)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    # role = models.CharField(verbose_name = 'роль', max_length=64, default=Role.MEMBER)
    date_in = models.DateField(verbose_name="дата добавления", auto_now=True)
    is_sended = models.BooleanField(verbose_name="отправлено", null=True)
    note = models.TextField(verbose_name="заметка", blank=True)
    expire = models.CharField(verbose_name="дата истечения", max_length=64, null=True) # input_formats=["%d-%m-%Y"]
    vvcard = models.CharField(verbose_name="номер карты ВВ", max_length=64, default="НЕТ КАРТЫ")

class Contacts(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)    
    gid = models.CharField(verbose_name = "идентификатор", max_length=64, unique=True, null=True)
    name = models.CharField(verbose_name="имя", max_length=64)    
    phone = models.CharField(verbose_name="номер телефона", max_length=64, default=' - ')
    elmail = models.EmailField(verbose_name="элетронная почта")    
    

    def __str__(self):
        return f'GID!!!!!! {self.gid}'