from django.core.management.base import BaseCommand
from general.models import CollectionPoints

class Command(BaseCommand):
    help = 'Adding test collection point'   

    def handle(self, *args, **kwargs): 
        '''

            name=models.CharField(verbose_name="имя", max_length=64)
            chp_point=models.BooleanField(verbose_name='принадлежность пункта сбора "Чистому Петербургу"', default=True)
            accrual_restrict=models.IntegerField(verbose_name='ограничение сколько раз в неделю можно начислять от 1-7 ', choices=ACCURAL_RESTRICT_CHOICES, default=1)
            cost_by_visit=models.IntegerField(verbose_name='стоимость посещения', default=0)
            accrual_restrict_nonmember=models.IntegerField(verbose_name='ограничение для не участников клуба 1-7', choices=ACCURAL_RESTRICT_CHOICES, default=1)
            cost_by_nonmember=models.IntegerField(verbose_name='стоимость посещения не участником', default=0)
        '''
        role, created = CollectionPoints.objects.get_or_create(                
                    name = 'пункт сбора',
                    chp_point = True,
                    accrual_restrict = 1,
                    cost_by_visit = 50,
                    accrual_restrict_nonmember = 1,   
                    cost_by_nonmember = 100           
        )
    
        if created:
            self.stdout.write(self.style.SUCCESS(
                    f'Пункт сбора добавлен'))
        else:
            self.stdout.write(self.style.ERROR(
                    f'Пункт сбора НЕ добавлен'))
