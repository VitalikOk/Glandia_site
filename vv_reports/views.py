from django.shortcuts import render
import general.main_func as mf
import pandas as pd
from ast import Str


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


def add_bonus_to_team(rol, bonus_num, all_members):
    team = (all_members[(all_members['team'].str.lower().replace('ё', 'е')
                         == rol.lower())
                        & (all_members['vv_card'] != 'Нет карты')][['vv_card', 'phone']]
    )
    team['count'] = int(bonus_num)
    return team


def get_team_bonus(all_members, start_day=1):
    teab_bonus = pd.DataFrame()
    team = {'Сотрудник': 3,
            'волонтер': 1,
            'Регулярный посетитель': 3
            }
    for rol in team:
        teab_bonus = pd.concat([teab_bonus, add_bonus_to_team(rol, team[rol], all_members)])
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
    g_sheets = mf.gspread.service_account(filename='static/1234.json')
    # Открыывем таблицу
    all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    all_members = mf.get_all_memb_df(all_members)
    all_members['vv_card'] = all_members['vv_card'].apply(mf.change_cir_lat)
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
    all_members = mf.get_all_members(g_sheets)
    vv_rep_events = vvrep_from_gs(mf.EVENTS_VISITS, mf.ev_columns + ['vv_card'], g_sheets)
    if type(vv_rep_events) != None and len(vv_rep_events):
        vv_rep_events = (vv_rep_events.groupby(['vv_card', 'phone']).count()
                         .rename(columns={'date': 'count'})
                         .sort_values(by='count', ascending=False)
                         .reset_index(drop=False)
                         )
        vv_rep_events = vv_rep_events[vv_rep_events['vv_card'] != 'Нет карты']
    else:
        print('Нет данных о посещении акций')
    vv_rep_events = pd.concat([vv_rep_events, get_team_bonus(all_members)])
    vv_rep_events['count'] = vv_rep_events['count'].astype('int')
    vv_rep_events = (vv_rep_events.groupby(['vv_card', 'phone']).sum()
                     .rename(columns={'date': 'count'})
                     .sort_values(by='count', ascending=False)
                     .reset_index(drop=False)
                     )
    vv_rep_events = vv_rep_events[(vv_rep_events['vv_card'].str.fullmatch(r'.{6,8}'))]
    # display(vv_rep_events)
    # vv_rep_events['vv_card'] = vv_rep_events.apply(get_vv_card_all, axis=1)
    # vv_rep_events_no_send = vv_rep_events[vv_rep_events['vv_card'].isin(['Нет карты','Не в клубе'])]
    # vv_rep_events_send = vv_rep_events[~vv_rep_events['vv_card'].isin(['Нет карты','Не в клубе'])]
    # display(vv_rep_events_no_send.sort_values(by='vv_card'))

    if len(vv_rep_events):
        vvrep_to_gs(mf.VV_EVENTS_REPORT, vv_rep_events[['vv_card', 'count']])
    else:
        print('Нет данных для добавления в очёт')
    context = {
        'bonus_count': vv_rep_events['count'].count()
    }
    return render(request, "vv_reports/vv_events_visits_report.html", context)
