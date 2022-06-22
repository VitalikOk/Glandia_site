from operator import mod
from django.db import models
from datetime import datetime
from general.enums import Role


class Roles(models.Model):
    role = models.CharField(verbose_name='Role', max_length=64, unique=True, null=False)

    def __str__(self):
        return f'{self.id} {self.role}'

class Users(models.Model):
    gid = models.IntegerField(verbose_name = "идентификатор", unique=True, null=True)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE)
    # role = models.CharField(verbose_name = 'роль', max_length=64, default=Role.MEMBER)
    date_in = models.DateField(verbose_name="дата добавления")
    is_sended = models.BooleanField(verbose_name="отправлено", null=True)
    note = models.TextField(verbose_name="заметка", blank=True)
    expire = models.CharField(verbose_name="дата истечения", max_length=64, null=True) # input_formats=["%d-%m-%Y"]
    vvcard = models.CharField(verbose_name="номер карты ВВ", max_length=64, default="НЕТ КАРТЫ")

class Contacts(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)    
    gid = models.IntegerField(verbose_name = "идентификатор", unique=True, null=True)
    name = models.CharField(verbose_name="имя", max_length=64)    
    phone = models.CharField(verbose_name="номер телефона", max_length=64, default=' - ')
    elmail = models.EmailField(verbose_name="элетронная почта")  

class SentReportsVV(models.Model):
    date = models.DateField(verbose_name="дата отправки")
    memb_count = models.IntegerField(verbose_name = "количество разных участников", null=True)
    bonus_count = models.IntegerField(verbose_name = "количество начислений", null=True)
    bonus_rate = models.IntegerField(verbose_name = "количество бонусов за посещение", null=True)
    report_type = models.CharField(verbose_name="тип отчёта event|subscrip", max_length=64, default="event")


class CollectionPoints(models.Model):
    ACCURAL_RESTRICT_CHOICES = (
        (1, 'One'),
        (2, 'Two'),
        (3, 'Three'),
        (4, 'Four'),
        (5, 'Five'),
        (6, 'Six'),
        (7, 'Seven')
        # ('ONE', 1),
        # ('TWO', 2),
        # ('THREE', 3),
        # ('FOUR', 4),
        # ('FIVE', 5),
        # ('SIX', 6),
        # ('SEVEN', 7)
    )
    name=models.CharField(verbose_name="имя", max_length=64)
    chp_point=models.BooleanField(verbose_name='принадлежность пункта сбора "Чистому Петербургу"', default=True)
    accrual_restrict=models.IntegerField(verbose_name='ограничение сколько раз в неделю можно начислять от 1-7 ', choices=ACCURAL_RESTRICT_CHOICES, default=1)
    cost_by_visit=models.IntegerField(verbose_name='стоимость посещения', default=0)
    accrual_restrict_nonmember=models.IntegerField(verbose_name='ограничение для не участников клуба 1-7', choices=ACCURAL_RESTRICT_CHOICES, default=1)
    cost_by_nonmember=models.IntegerField(verbose_name='стоимость посещения не участником', default=0)


class EventsVisits(models.Model):
    date_time = models.DateTimeField(verbose_name="дата посещения")
    gid = models.IntegerField(verbose_name = "идентификатор", null=True)
    expire = models.CharField(verbose_name="дата истечения на момент акции", max_length=64, null=True) # input_formats=["%d-%m-%Y"]
    note = models.TextField(verbose_name="заметка", blank=True)    
    vvcard = models.CharField(verbose_name="номер карты ВВ на момент акции", max_length=64, default="НЕТ КАРТЫ")
