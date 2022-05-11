from general.enums import Role
from general.models import Users, Contacts, Roles, EventsVisits, SentReportsVV
from datetime import date
from datetime import datetime
import general.main_func as mf


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
    current_gid = next_gid()

    user, _ = Users.objects.get_or_create(
        gid = current_gid,                
        role = get_role(member),    
        date_in = member['date'],
        is_sended = True if member['qrc_status'] == 'ДА' else False,
        note = member['note'],
        expire = member['expire'],
        vvcard = member['vv_card']
    )             

    contact, created = Contacts.objects.get_or_create(
        gid = current_gid,                
        user = user,
        name = member['name'],
        phone = member['phone'],
        elmail = member['email']                
    )          

    # if created:
    #     self.stdout.write(self.style.SUCCESS(
    #             f'Пользователь "{contact.name}" добавлен'))
    # else:
    #         self.stdout.write(self.style.WARNING(
    #             f'Пользователь "{contact.name}" уже существует'))



def get_role(member):
    input_role = member['team']            
    if input_role.lower() == 'сотрудник':
        return Roles.objects.get(id=1)
    elif input_role.lower() in ('волонтер', 'волонтёр'):
        return Roles.objects.get(id=2)
    else:
        return Roles.objects.get(id=3)


def add_visit(visit):                  
            ev_visit = EventsVisits.objects.create(
                date_time = visit['date'],
                gid = visit['gid'],
                expire = visit['expire'],
                note = visit['event'],
                vvcard = visit['vv_card'],
            )          
        

def add_sent_report_vv(rep):                  
            sent_rep_vv = SentReportsVV.objects.create(
                date = rep['date'],
                memb_count = rep['memb_count'],
                bonus_count = rep['bonus_count'],
                bonus_rate = rep['bonus_rate'],
                report_type = rep['report_type'],
            )                  