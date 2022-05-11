from django.shortcuts import render
import general.main_func as mf
import pandas as pd
from ast import Str
import general.db_func as dbf
from general.models import Users, Contacts, SentReportsVV, EventsVisits
from django.db.models import Q
from datetime import datetime

def vvrep_to_gs(file_name, data):
    g_sheets = mf.get_google_sheet()
    try:
        sheet = g_sheets.open(file_name + mf.MONTH).sheet1
    except:
        sheet = g_sheets.create(file_name + mf.MONTH).sheet1
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
    team = team[['gid','vvcard']]
    team['count'] = int(bonus_num)
    return team


def get_team_bonus(start_day=1):
    teab_bonus = pd.DataFrame()
    team = {1: 3, #'Сотрудник'
            2: 1, #'волонтер'
                 #'Регулярный посетитель'
            'G73': 3,
            'G101': 3, 
            'G93': 2,
            }
    for rol in team:
        teab_bonus = pd.concat([teab_bonus, add_bonus_to_team(rol, team[rol])])
    return teab_bonus


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
    return render(request, "vv_reports/vv_reports_menu.html")


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
    all_members = mf.get_all_members()
    vv_rep_members = make_vvrep(all_members[all_members['vv_card'].str.upper() != 'НЕТ КАРТЫ'], ['vv_card'])
    vvrep_to_gs(mf.VV_MEMBERS_REPORT, vv_rep_members)
    context = {
        'members_count': len(vv_rep_members)
    }
    return render(request, "vv_reports/vv_all_members_report.html", context)


def vv_events_visits_report(request):
    # VV_EVENTS_REPORT
    # отчёт посещений акций для
    g_sheets = mf.get_google_sheet()

    message = 'Cформирован'
    start_date = (SentReportsVV.objects.filter(report_type='event')
                               .order_by('date').last()
                               .date
                        )
    
    vv_rep_events = pd.DataFrame(list(EventsVisits.objects.filter(date_time__gte=start_date).values()))    
    vv_rep_events['date'] = vv_rep_events['date_time'].dt.date
    vv_rep_events = vv_rep_events[['date','vvcard','gid']] 
    vv_rep_events.drop_duplicates(inplace=True)

    if vv_rep_events is not None and len(vv_rep_events):
        vv_rep_events = (vv_rep_events.groupby(['vvcard', 'gid']).count()
                         .rename(columns={'date': 'count'})
                         .sort_values(by='count', ascending=False)
                         .reset_index(drop=False)
                         )
        vv_rep_events = vv_rep_events[vv_rep_events['vvcard'] != 'Нет карты']
    else:
        message = 'Нет данных о посещении акций'


    vv_rep_events = pd.concat([vv_rep_events, get_team_bonus()])
    vv_rep_events['count'] = vv_rep_events['count'].astype('int')
    vv_rep_events = (vv_rep_events.groupby(['vvcard', 'gid']).sum()
                     .rename(columns={'date': 'count'})
                     .sort_values(by='count', ascending=False)
                     .reset_index(drop=False)
                     )
    vv_rep_events = vv_rep_events[(vv_rep_events['vvcard'].str.fullmatch(r'.{6,8}'))]


    if len(vv_rep_events):
        vvrep_to_gs(mf.VV_EVENTS_REPORT, vv_rep_events[['vvcard', 'count']])
    else:
        message = 'Нет данных для добавления в очёт'

    report_log = {
        'date': datetime.now().date(),
        'memb_count': len(vv_rep_events),
        'bonus_count': vv_rep_events['count'].sum(),
        'bonus_rate': 50,
        'report_type': 'event',
    }

    dbf.add_sent_report_vv(report_log)
    

    context = {
        'start_date': start_date,
        'date': report_log['date'],
        'memb_count': report_log['memb_count'],
        'bonus_count': report_log['bonus_count'],
        'vv_rep_events': mf.disply_table_html(vv_rep_events),
        'message': message,
    }
    return render(request, "vv_reports/vv_events_visits_report.html", context)
