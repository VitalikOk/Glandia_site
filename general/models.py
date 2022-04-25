from django.db import models

class Users(models.Model):
    name = models.CharField(verbose_name="имя", max_length=64, unique=True)
    date_in = models.DateField(verbose_name="дата добавления", auto_now_add=True)
    phone = models.BigIntegerField(verbose_name="номер телефона", unique=True, default=' - ')
    elmail = models.EmailField(verbose_name="элетронная почта", unique=True)
    note = models.TextField(verbose_name="заметка", blank=True)
    is_sended = models.BooleanField(verbose_name="отправлено")
    expire = models.DateField(verbose_name="дата истечения")
    vvcard = models.IntegerField(verbose_name="номер карты ВВ", default="НЕТ КАРТЫ")

    def __str__(self):
        return self.name
