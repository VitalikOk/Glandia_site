from django.shortcuts import render
import general.main_func as mf
import pandas as pd
from ast import Str
import general.db_func as dbf
from general.models import Users, Contacts, SentReportsVV, EventsVisits, CollectionPoints
from django.db.models import Q
from datetime import datetime
from datetime import timedelta
from datetime import date
    
def vvrep_to_gs(file_name, data):
    g_sheets = mf.get_google_sheet()
    try:
        sheets = g_sheets.open(file_name)
    except:
        sheets = g_sheets.create(file_name)
    sheet = sheets.sheet1    
    sheet.clear()
    # добавление данных в гугл таблицу
    row_cnt, col_cnt = data.shape
    # display(data)
    cl_rng = mf.get_abcrage(0, 1, col_cnt - 1, row_cnt)
    # print(cl_rng)
    cel_l = sheet.range(cl_rng)
    ind = 0
    for i in range(row_cnt):
        for j in range(col_cnt):
            cel_l[ind].value = str(data.iloc[i][j])
            ind += 1
    sheet.update_cells(cel_l)

    return f"https://docs.google.com/spreadsheets/d/{sheets.id}"


    # for ind, row in data.iterrows():
    #   sheet.insert_row(list(row),ind+1)


def add_bonus_to_team(b_role, bonus_num):
    if 'G' in str(b_role):
        b_gid = int(b_role.lstrip('G'))
        team = pd.DataFrame(list(Users.objects.filter(gid=b_gid)
                                            .values())
                                            )
    else:
        team = pd.DataFrame(list(Users.objects.filter(role=b_role)
                                            .exclude(vvcard='НЕТ КАРТЫ')
                                            .values())
                                            )
    team = team[['gid','vvcard', 'expire']]
    team['note'] = 'Волонтёрство'
    team['count'] = int(bonus_num)
    return team


def get_team_bonus(start_day=1):
    team_bonus = pd.DataFrame()
    team = {1: 3, #'Сотрудник'
            2: 1, #'волонтер'
                 #'Регулярный посетитель'
            'G73': 12,
            'G101': 3, 
            'G93': 2,
            'G2': 12
            }
    for rol in team:
        team_bonus = pd.concat([team_bonus, add_bonus_to_team(rol, team[rol])])
    return team_bonus


def get_vv_card_all(row):
    all_members = mf.get_all_members()
    vv_card = all_members[all_members['phone'] == row['phone']]['vv_card'].values
    try:
        vv_card = vv_card[0]
    except:
        vv_card = 'Не в клубе'
    return vv_card


def make_vvrep(data, rep_cols=['date', 'vv_card', 'phone']):
    data = data[rep_cols].copy()
    if 'date' in rep_cols:
        data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d %H:%M:%S')
        data['date'] = data['date'].apply(lambda x: x.strftime('%d.%m'))

    data.drop_duplicates(inplace=True)
    data.reset_index(drop=True, inplace=True)
    return data


def vvrep_from_gs(file_name, columns, g_sheets):
    sheets, rows = mf.get_all_values_sheets(file_name + mf.MONTH, g_sheets)
    if rows == None:
        return None
    data = make_vvrep(pd.DataFrame(rows, columns=columns))
    if len(data) > 0:
        list_name = (f"{data['date'].min().split('.')[0]}-"
                     + f"{data['date'].max()}"
                     )
        sheets.sheet1.update_title(list_name)
        sheets.add_worksheet(title="new", rows="37", cols="10", index=0)
    return data


def correct_all_vvcards():
    g_sheets = mf.get_google_sheet()
    # Открыывем таблицу
    all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    all_members = mf.get_all_memb_df(all_members)
    all_members['vv_card'] = all_members['vv_card'].apply(lambda x: mf.change_cir_lat(x) 
                                                                if x!='' else 'НЕТ КАРТЫ')    
    mf.all_memb_rewrite_column(all_members, 'vv_card', all_members_sheets.sheet1)


def vv_reports_menu(request):
    context = {
        'today': datetime.now().date().strftime("%Y-%m-%d")
            }
    return render(request, "vv_reports/vv_reports_menu.html", context)


def vv_cards_correct(request):
    correct_all_vvcards()
    return render(request, "vv_reports/vv_cards_correct.html")


def vv_nocard_emails(request):
    all_members = mf.get_all_members()
    nocard_mail_list = (all_members[all_members['vv_card'].str.upper() == 'НЕТ КАРТЫ']
                        .reset_index(drop=True)
                        )
    print(nocard_mail_list)
    mail_list, log = mf.do_mailing(nocard_mail_list, msg_text='no card')
    context = {
        'mailing_log': log
    }
    return render(request, "vv_reports/vv_nocard_emails.html", context)


def vv_all_members_report(request):
    # VV_MEMBERS_REPORT
    if request.method == 'POST':
        message = 'Cформирован'
        end_date = datetime.strptime(request.POST['end_date_to_subscribe'], "%Y-%m-%d")
        end_date += timedelta(days=1)
        today = datetime.now().date
        vv_rep_members = pd.DataFrame(list(Users.objects.filter(Q(date_in__lte=end_date) & Q(expire__lte=today) & ~Q(vvcard='НЕТ КАРТЫ'))
                                                        .order_by('date_in').values())) 

        gs_link =''
        if len(vv_rep_members):
            vv_rep_members = vv_rep_members[['date_in','gid','vvcard', 'expire']]
            vv_rep_members.drop_duplicates(subset='vvcard', inplace=True)    
            vv_rep_members['expire'] = pd.to_datetime(vv_rep_members['expire'], format='%d.%m.%Y').dt.date
            expire = vv_rep_members[(vv_rep_members['expire'] < datetime.now().date())]   
            vv_rep_members = vv_rep_members[(vv_rep_members['expire'] >= datetime.now().date())]  
            if "gs_create" in request.POST:  
                gs_link = vvrep_to_gs(mf.VV_MEMBERS_REPORT, pd.DataFrame(vv_rep_members['vvcard']))
        else:            
            message = 'Нет данных для добавления в очёт'

        report_log = {
            'date': datetime.now().date(),
            'memb_count': len(vv_rep_members),
            'bonus_count': len(vv_rep_members),
            'bonus_rate': 200,
            'report_type': 'subscrip',
        }

        if "add_rep_in_db" in request.POST: 
            dbf.add_sent_report_vv(report_log)    
            
            

        context = {
            'date': report_log['date'],
            'memb_count': report_log['memb_count'],
            'vv_rep_members': mf.disply_table_html(vv_rep_members),
            'expire': mf.disply_table_html(expire),
            'message': message,
            'gs_link': gs_link,
        }
        return render(request, "vv_reports/vv_all_members_report.html", context)


def vv_events_visits_report(request):
    # VV_EVENTS_REPORT
    # отчёт посещений акций для
    if request.method == 'POST':
        message = 'Cформирован'
        start_date = (SentReportsVV.objects.filter(report_type='event')
                                .order_by('date').last()
                                .date
                            )
        start_date = request.POST['start_date']
        end_date = datetime.strptime(request.POST['end_date'], "%Y-%m-%d")
        end_date += timedelta(days=1)
        vv_rep_events = pd.DataFrame(list(EventsVisits.objects.filter(date_time__gte=start_date, 
                                                                      date_time__lte=end_date).values()))    

        if "report_data" in request.POST:
            report_data = mf.disply_table_html(vv_rep_events)
        else:
            report_data = ''

        gs_link = ''
        data_event = ''
        expire_data = ''
        memb_count = 0
        bonus_count = 0
        all_points_data = pd.DataFrame()
        spec_amount = ''

        if len(vv_rep_events):
            vv_rep_events['date'] = vv_rep_events['date_time'].dt.date
            vv_rep_events = vv_rep_events[['date','vvcard','gid', 'expire', 'note', 'special_amount']] 
            vv_rep_events.drop_duplicates(subset=['date','vvcard','gid', 'note', 'special_amount']  ,inplace=True)

            if vv_rep_events is not None and len(vv_rep_events):
                vv_rep_events_spec = vv_rep_events[vv_rep_events['special_amount'] != 0]
                vv_rep_events_spec['bonus'] = vv_rep_events_spec['special_amount']
                vv_rep_events_spec.drop('special_amount', axis=1, inplace=True)
                vv_rep_events_spec['expire'] =  pd.to_datetime(vv_rep_events_spec['expire'], format='%d.%m.%Y', errors='coerce').dt.date
                vv_rep_events = vv_rep_events[vv_rep_events['special_amount'] == 0]
                vv_rep_events.drop('special_amount', axis=1, inplace=True)
                vv_rep_events = (vv_rep_events.groupby(['vvcard', 'gid', 'expire', 'note']).count()
                                .rename(columns={'date': 'count'})
                                .sort_values(by='count', ascending=False)
                                .reset_index(drop=False)
                                )
                vv_rep_events = vv_rep_events[vv_rep_events['vvcard'] != 'Нет карты']
            else:
                message = 'Нет данных о посещении акций'


            vv_rep_events = pd.concat([vv_rep_events, get_team_bonus()])
            vv_rep_events['count'] = vv_rep_events['count'].astype('int')
            vv_rep_events = (vv_rep_events.groupby(['vvcard', 'gid', 'expire','note']).sum()
                            .rename(columns={'date': 'count'})
                            .sort_values(by='count', ascending=False)
                            .reset_index(drop=False)
                            )
            vv_rep_events = vv_rep_events[(vv_rep_events['vvcard'].str.fullmatch(r'.{7}'))]   
            vv_rep_events['expire'] =  pd.to_datetime(vv_rep_events['expire'], format='%d.%m.%Y', errors='coerce').dt.date

            expire = vv_rep_events[(vv_rep_events['gid'] != 0) & (vv_rep_events['expire'] < datetime.now().date())]   

            points = pd.DataFrame(list(CollectionPoints.objects.all().order_by('id').values()))


            for ind, point in points.iterrows():
                data_event += (f"<H2>Точка сбора: {point['name']}</H2><br>"
                              + f"Для участников ЧП {point['accrual_restrict']} раз в неделю {point['cost_by_visit']} Бонусов<br>" 
                              + f"Для остальных {point['accrual_restrict_nonmember']} раз в неделю {point['cost_by_nonmember']} Бонусов<br>"
                )

                point_data = vv_rep_events[vv_rep_events['note'].str.contains(point['name'])]
                point_data_spec = vv_rep_events_spec[vv_rep_events_spec['note'].str.contains(point['name'])]

                def get_bonus_sum(row):
                    if row['gid'] !=0 and row['expire'] >= datetime.now().date():
                        cost = point['cost_by_visit'] 
                        restrict = point['accrual_restrict'] 
                    else:
                        cost = point['cost_by_nonmember']
                        restrict = point['accrual_restrict_nonmember']      

                    if row['count'] > restrict:
                        visits = restrict
                    else:
                        visits = row['count'] 

                    return visits * cost


                if len(point_data):
                    point_data['bonus'] = point_data.apply(get_bonus_sum, axis=1)      
                    if len(point_data_spec):
                        point_data_spec['count'] = 1
                        point_data_spec.fillna(value={'expire': date(2021, 1, 1)}, inplace=True)
                        point_data = pd.concat([point_data, point_data_spec[point_data.columns]])                                                                        
                        point_data = (point_data.groupby(['vvcard', 'gid', 'expire','note'])                                  
                                                .agg({'count': 'sum', 'bonus': 'sum'})                            
                            .sort_values(by='bonus', ascending=False)
                            .reset_index(drop=False)
                            )
                    all_points_data = pd.concat([all_points_data, point_data])
                    point_data.reset_index(drop=True, inplace=True)
                    data_sum = point_data['bonus'].sum()
                    data_count = point_data['bonus'].count()                    
                    data_event += mf.disply_table_html(point_data)
                    memb_count += data_count
                    bonus_count += data_sum
                    data_event += f"<br> Итого {data_sum} бонусов для {data_count} участников"                                            
            
            all_points_data.reset_index(drop=True, inplace=True)
            gs_data_disp = f'Создание отчёта в Google таблице отключено'
            if "gs_create" in request.POST:
                all_points_data = all_points_data[['vvcard','bonus']].groupby(['vvcard']).sum()
                all_points_data.reset_index(drop=False, inplace=True)
                all_points_data.sort_values(by='bonus', ascending=False, inplace=True)
                if 'gs_data' in request.POST:  
                    gs_data_disp = mf.disply_table_html(all_points_data)
                else:
                    gs_data_disp = ''
                gs_data_disp += f"<br> Итого {all_points_data['bonus'].sum()} бонусов для {all_points_data['bonus'].count()} участников"                            
                gs_link = vvrep_to_gs(mf.VV_EVENTS_REPORT, all_points_data)

            report_log = {
                'date': datetime.now().date(),
                'memb_count': memb_count,
                'bonus_count': bonus_count,
                'bonus_rate': 1,
                'report_type': 'event',
            }
        else:            
            message = 'Нет данных для добавления в очёт'
            report_log = {
                'date': datetime.now().date(),
                'memb_count': len(vv_rep_events),
                'bonus_count': 0,
            }

        if 'add_rep_in_db' in request.POST: 
            dbf.add_sent_report_vv(report_log)
        if 'expire_data' in request.POST: 
            expire_data = '<br><h3>Истёк срок абонимента</h3><br>'
            expire_data += mf.disply_table_html(expire)
        
        context = {
            'start_date': start_date,
            'report_data': report_data,
            'date': report_log['date'],
            'memb_count': report_log['memb_count'],
            'bonus_count': report_log['bonus_count'],
            'data_event': data_event,
            'vv_rep_events': gs_data_disp,            
            'expire': expire_data,
            'message': message,
            'gs_link': gs_link,
        }
        return render(request, "vv_reports/vv_events_visits_report.html", context)
