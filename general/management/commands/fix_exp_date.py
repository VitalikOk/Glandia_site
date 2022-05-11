from django.core.management.base import BaseCommand
from general.enums import Role
from general.models import Users, Contacts, Roles
from datetime import date
import general.main_func as mf


class Command(BaseCommand):
    help = 'Adding roles'   

    def handle(self, *args, **kwargs):


        mailing_list = []
        q_set = list(Users.objects.all()                            
                            .values_list('gid', 'expire')
                            )


        for memb in q_set:
            gid = memb[0]
            old_exp = memb[1]
            if '-' in old_exp:
                tmp_exp = old_exp.split('-')
                fix_exp = f'{tmp_exp[2]}.{tmp_exp[1]}.{tmp_exp[0]}'
            else:
                fix_exp = old_exp
            print(f'Дата изменена {gid} - {old_exp} -> {fix_exp}' )
            Users.objects.filter(gid=gid).update(expire=fix_exp)