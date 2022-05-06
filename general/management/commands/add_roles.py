from django.core.management.base import BaseCommand
from general.models import Roles

class Command(BaseCommand):
    help = 'Adding roles'   

    def handle(self, *args, **kwargs):

        ROLES = (
            'Сотрудник',
            'Волонтёр',
            'Работник'
        )

        for obj in ROLES:
            print(obj)
            role, created = Roles.objects.get_or_create(                
                    role=obj
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                        f'Роль "{role.role}" добавлена'))
            else:
                self.stdout.write(self.style.SUCCESS(
                        f'Роль "{role.role}" уже существует'))