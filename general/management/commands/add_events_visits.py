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
                date_time = datetime.strptime(visit['date_time'] + ' +0000', '%Y-%m-%d %H:%M:%S +0000'),
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

        for month_c in range(1,2):
            events_log = g_sheets.open(f'Посещения акций 0{month_c}')
            w_sheets = events_log.worksheets()
            for sh in w_sheets:
                rows = sh.get_all_values()
                if len(rows) > 0:  
                    data = mf.pd.DataFrame(rows, columns=columns)                                                       
                    for _, visit in data.iterrows():
                        add_visit(visit)
        