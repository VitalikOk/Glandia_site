from django.core.management.base import BaseCommand
from general.models import Users, Contacts, EventsVisits
from datetime import date, datetime
import general.main_func as mf


class Command(BaseCommand):
    help = 'Test command'

    def handle(self, *args, **kwargs):

        def add_visit(visit):      
            contact = Contacts.objects.filter(phone=visit['phone']).first()
            if contact is None:
                contact = Contacts.objects.filter(elmail=visit['email']).first()
            if contact is None:
                gid = None
            else:
                gid = contact.gid
            
            ev_visit = EventsVisits.objects.create(
                date_time = datetime.strptime(visit['date_time'].split('.')[0], '%Y-%m-%d %H:%M:%S'),
                gid = gid,
                expire = visit['expire'],
                note = visit['note'],
                vvcard = visit['vvcard'],
            )          

            # if created:
            #     self.stdout.write(self.style.SUCCESS(
            #             f'Событие "{ev_visit.date_time}" добавлено'))
            # else:
            #      self.stdout.write(self.style.WARNING(
            #             f'Событие "{ev_visit.date_time}" не добавлено'))
        

        g_sheets = mf.get_google_sheet()
        columns = [                
                'date_time',
                'phone',
                'name',
                'expire',
                'email',
                'note',
                'vvcard',
        ]
        all_records = 0
        for month_c in range(1,5):
            events_log = g_sheets.open(f'Посещения акций 0{month_c}')            
            w_sheets = events_log.worksheets()
            for sh in reversed(w_sheets):
                print(f' импорт {events_log} - {sh}')                
                rows = sh.get_all_values()
                print(f' количество записей {len(rows)}')
                all_records += len(rows)
                if len(rows) > 0:  
                    data = mf.pd.DataFrame(rows, columns=columns)                                                       
                    for _, visit in data.iterrows():
                        add_visit(visit)
        print(f' Общее количество записей {all_records}')
        