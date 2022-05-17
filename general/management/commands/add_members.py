from django.core.management.base import BaseCommand
from general.enums import Role
from general.models import Users, Contacts, Roles
from datetime import date
import general.main_func as mf


class Command(BaseCommand):
    help = 'Test command'

    def handle(self, *args, **kwargs):
        all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, mf.gspread.service_account(filename='general/conf/gs.json'))
        all_members = mf.get_all_memb_df(all_members)

        VIP_DICT = {
            '9811404242': 1,
            '4795067525': 2,
            '9619796433': 3,
            '9139758064': 73,
            '9162251765': 101
        }

        vip = all_members[all_members['phone'].isin(VIP_DICT.keys())]
        not_vip = all_members[~all_members['phone'].isin(VIP_DICT.keys())]
         

        def next_gid():

            last_gid = Users.objects.all().order_by('gid').last().gid                                 
            
            if last_gid is not None:
                max_gid = int(last_gid)
                if max_gid < 101:
                    return 101
                max_gid += 1    
                if max_gid % 100 == 0:
                    return max_gid + 1
                return max_gid
            else:
                return 102

        def add_user(member):

            if member['expire'][-1].isdigit():                
                expd = list(map(int, member['expire'].split('.')))
                current_date = f'{expd[-3] if len(expd) == 3 else 15}.expd[-2].{expd[-1]}'
            else:
                # очень временно, потом удалить:
                current_date = '31.12.2022'
        
     
            if member['phone'] in VIP_DICT.keys():
                current_gid = VIP_DICT[member['phone']]
            else:
                current_gid = next_gid()

            user, _ = Users.objects.get_or_create(
                gid = current_gid,                
                role = get_role(member),    
                date_in = member['date_in'],
                is_sended = True if member['sended'] == 'ДА' else False,
                note = member['note'],
                expire = current_date,
                vvcard = member['vv_card']
            )             

            contact, created = Contacts.objects.get_or_create(
                gid = current_gid,                
                user = user,
                name = member['name'],
                phone = member['phone'],
                elmail = member['email']                
            )          

            if created:
                self.stdout.write(self.style.SUCCESS(
                        f'Пользователь "{contact.name}" добавлен'))
            else:
                 self.stdout.write(self.style.WARNING(
                        f'Пользователь "{contact.name}" уже существует'))



        def get_role(member):
            input_role = member['team']            
            if input_role.lower() == 'сотрудник':
                return Roles.objects.get(id=1)
            elif input_role.lower() in ('волонтер', 'волонтёр'):
                return Roles.objects.get(id=2)
            else:
                return Roles.objects.get(id=3)
        

        for ind, member in vip.iterrows():
            add_user(member)
        
        for ind, member in not_vip.iterrows():
            add_user(member)