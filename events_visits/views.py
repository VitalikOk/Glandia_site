from django.shortcuts import render
import general.main_func as mf
import pandas as pd


def fix_qr_data(arr):
    """
    Обработка и коррекция данных из qr - кодов
    """
    arr = arr.split(' ')
    result = []
    if not mf.re.fullmatch(r"\d{10}", arr[-1]):
        print(f"Err qr-data  {' '.join(arr)}")
        return None
    for a in reversed(arr):
        if a not in ['', 'декабрь', '2022']:
            result.append(a)
    return result


def check_field(row, field_name, all_members):
    """
    Функция для заполнения пустых полей
    """
    if (field_name not in row.index) or (row[field_name] == ''):
        result = (all_members.loc[(all_members['phone'] == row['phone'])
                                  | (all_members['vv_card'] == row['vv_card'])
        , [field_name]].values
                  )
        if len(result) > 0:
            row[field_name] = result[0][0]
        else:
            row[field_name] = f"{mf.COLUMS_NAMES[field_name]} не указано"
    return row[field_name]


def fill_data(data, all_members):
    """
    Функция для востановления данных из разных источников
    """
    data_ev = pd.DataFrame(columns=mf.ev_columns)
    if 'vv_card' in data.columns:
        data['vv_card'] = data['vv_card'].apply(mf.change_cir_lat)
    # if 'event' not in data.columns:
    #   data['event'] = data['gps']
    if 'qr_data' in data.columns:  # разбор строки qr кода
        for ind, row in data.iterrows():
            data_str = pd.Series([], dtype=pd.StringDtype())
            data_str['date'] = row['date']
            if 'gps' in data.columns:
                data_str['event'] = row['gps']
            elif ('gps_a' in data.columns) and ('gps_b' in data.columns):
                data_str['event'] = f"{row['gps_a']},{row['gps_b']}"
            str_datd = fix_qr_data(row['qr_data'])
            if str_datd is None:
                continue
            num_col = min(len(str_datd), len(mf.ev_columns))
            for i in range(num_col):  # распред строки qr кода по колонкам
                data_str[mf.ev_columns[1 + i]] = str_datd[i]
            data_ev = data_ev.append(data_str, ignore_index=True)
        data_ev['vv_card'] = ''
    else:
        data_ev = data
    data_ev.fillna('', inplace=True)
    for ind, row in data_ev.iterrows():  # Заполнение недостающих полей
        for col in mf.ev_columns + ['vv_card']:
            if col not in ['event']:
                data_ev.loc[ind, col] = check_field(row, col, all_members)
    data_ev.fillna('', inplace=True)
    data_ev['date'] = pd.to_datetime(data_ev['date'])
    return data_ev


def get_waveservice_api(created_from='2022', d_type='issues'):
    with open('general/conf/wf.json') as f:
        wf = mf.json.load(f)
    if d_type == 'issues':
        url = 'https://api.waveservice.ru/public/v1/issues/'
        headers = {
            'accept': 'application/json',
            'x-api-key': wf['x-api-key']
        }
        parameters = {
            'page': 1,
            'size': 100,
            'sort': 'created',
            'created_from': created_from
        }
    elif d_type == 'check_ins':
        url = 'https://api.waveservice.ru/public/v1/check_ins/'
        headers = {
            'accept': 'application/json',
            'x-api-key': wf['x-api-key']
        }
        parameters = {
            'order_by': 'date_asc',
            'date_from': created_from,
            'count': 100
        }

    response = mf.requests.get(url, params=parameters, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        return mf.json.loads(response.text)
    else:
        print(f"Ошибка сервера waveservice: {response.status_code}")
        print(f"Ошибка сервера waveservice: {response.headers}")


def attrs_normalise(data):
    attrs = {'phone': '', 'email': '', 'vv_card': ''}
    for attr in data:
        if attr['name'] == 'Номер карты ВкусВилл':
            attrs['vv_card'] = attr['value'].replace('Карта', '').strip(' №')
        elif attr['name'] == 'Телефон':
            attrs['phone'] = attr['value']
        elif attr['name'] == 'Email':
            attrs['email'] = attr['value']
    return attrs


def ws_report_topd(json_data, action_type='', d_type='issues'):
    if d_type == 'issues':
        data_key = 'items'
        columns_json = ['created', 'attrs', 'author.first_name', 'issue_type.name',
                        'location.name', 'location.location_type.name']
        report = pd.json_normalize(json_data[data_key])[columns_json]
        report['attrs'] = report['attrs'].apply(attrs_normalise)
        report[['phone', 'email', 'vv_card']] = report['attrs'].apply(pd.Series)
        report.drop(columns=['attrs'], inplace=True)
        report.rename(columns={'created': 'date',
                               'author.first_name': 'name',
                               'issue_type.name': 'type',
                               'location.name': 'event',
                               'location.location_type.name': 'event_type'}
                      , inplace=True)

    elif d_type == 'check_ins':
        data_key = 'data'
        columns_json = ['created', 'data']
        report = pd.json_normalize(json_data[data_key])[columns_json]
        report.rename(columns={'created': 'date',
                               'data': 'qr_data'}
                      , inplace=True)

    report['date'] = (pd.to_datetime(report['date'])
                      + pd.DateOffset(hours=3, minutes=1)
                      )

    if action_type != '':
        return report[report['type'] == action_type]
    else:
        return report


def get_last_date(events_log_las):
    w_seets = events_log_las.worksheets()
    for sh in w_seets:
        last_sheet_rows = sh.get_all_values()
        if len(last_sheet_rows) > 0:
            last_date = (pd.to_datetime(last_sheet_rows[-1][0])
                         - pd.DateOffset(hours=3)
                         )
            return str(last_date)
    return None


def events_visits_menu(request):
    return render(request, "events_visits_menu.html")


def events_visits_import(request):
    # Импорт данных с акций
    data_events = pd.DataFrame(columns=mf.ev_columns)
    all_members = mf.get_all_members()
    import_config = {
        'manual_imput': True
        , 'qr_form_ws_import_api': True
        , 'scan_qr_from_ws_api': True
        , 'export_to_gsheet': True
    }

    # создание имени файла с номером месяца
    events_file_n = f"{mf.EVENTS_VISITS}{mf.MONTH}"
    prev_events_file_n = f"{mf.EVENTS_VISITS}{mf.PREV_MONTH}"
    # создание или открытие гугл таблицы
    g_sheets = mf.get_google_sheet()
    try:
        events_log_las = g_sheets.open(events_file_n)
    except:
        events_log_las = g_sheets.open(prev_events_file_n)

    last_date = get_last_date(events_log_las)

    if last_date is None:
        events_log_las = g_sheets.open(prev_events_file_n)
        last_date = get_last_date(events_log_las)
    last_date = mf.datetime.strptime(last_date.split('.')[0], '%Y-%m-%d %H:%M:%S')
    print(last_date)

    # Импорт данных об участниках введйнных вручную
    def add_manual_imput(month, data_events, g_sheets):
        ma_sheets, rows = mf.get_all_values_sheets(mf.MANUAL_ADD_SHEET + month, g_sheets)
        if ma_sheets is not None and len(rows) > 1:
            ma_bonus = mf.get_data_from_gs(ma_sheets, rows[1:]
                                        , columns=rows[0]
                                        , new_sheet=True)
            ma_bonus['event'] = 'Бонус за вступление, ручной ввод'
            # заполнение полей
            ma_bonus = fill_data(ma_bonus, all_members)
            # Добавления данных введйнных вручную к остальным
            data_events = pd.concat([data_events, ma_bonus], ignore_index=True)
        else:
            print(f"Данные в таблтце \"{mf.MANUAL_ADD_SHEET + mf.MONTH}\" не найдены")
        return data_events

    if import_config['manual_imput']:
        if last_date.strftime("%m") < mf.MONTH:
            data_events = add_manual_imput(mf.PREV_MONTH, data_events, g_sheets)
        data_events = add_manual_imput(mf.MONTH, data_events, g_sheets)

    # Импорт данных о посещениях из API app.waveservice.ru
    # api.waveservice.ru/public/v1/docs#/
    if import_config['qr_form_ws_import_api']:
        start_date = last_date
        len_rep = 100
        while len_rep == 100:
            ws_json = get_waveservice_api(created_from=last_date)
            if len(ws_json['items']) > 0:
                report = ws_report_topd(ws_json, action_type='Получить бонусы')
                len_rep = len(ws_json['items'])
                start_date = str(pd.to_datetime(report.iloc[-1]['date'])
                                 - pd.DateOffset(hours=3, seconds=59)
                                 )
                report = fill_data(report, all_members)
                data_events = pd.concat([data_events,
                                         report[mf.ev_columns + ['vv_card']]],
                                        ignore_index=True
                                        )
                print(data_events[data_events['phone'] == 'Номер телефона не указано'])
            else:
                print(f'Нет данных о посещениях из API app.waveservice.ru c {last_date}')
                break

    # Импорт данных о посещениях сканирование qr из
    # api.waveservice.ru/public/v1/docs#/
    if import_config['scan_qr_from_ws_api']:
        start_date = last_date
        len_rep = 100
        while len_rep == 100:
            ws_json = get_waveservice_api(created_from=start_date, d_type='check_ins')
            if len(ws_json['data']) > 0:
                report = ws_report_topd(ws_json, d_type='check_ins')
                len_rep = len(report)
                start_date = str(pd.to_datetime(report.iloc[-1]['date'])
                                 - pd.DateOffset(hours=3, seconds=59)
                                 )
                report = fill_data(report, all_members)
                data_events = pd.concat([data_events,
                                         report[mf.ev_columns + ['vv_card']]],
                                        ignore_index=True
                                        )
            else:
                print(f'Нет данных о check_ins из API app.waveservice.ru c {last_date}')
                break

    # ===================Обработка данных====================
    # сортировка и заполненин nan
    data_events.sort_values(by='date', inplace=True)
    data_events.reset_index(drop=True, inplace=True)
    data_events.fillna('', inplace=True)
    data_events = data_events[data_events['phone'] != 'Номер телефона не указано']
    print(data_events)

    if import_config['export_to_gsheet']:
        try:
            events_log = g_sheets.open(events_file_n).sheet1
        except:
            events_log = g_sheets.create(events_file_n).sheet1
        # получение номера последней записи в таблице
        last_row = len(events_log.get_all_values())
        row_cnt, col_cnt = data_events.shape

        # добавление данных в гугл таблицу
        cl_rng = mf.get_abcrage(0, last_row + 1, col_cnt - 1, last_row + row_cnt + 2)
        # print(cl_rng)
        cel_l = events_log.range(cl_rng)
        ind = 0
        for i in range(row_cnt):
            for j in range(col_cnt):
                cel_l[ind].value = str(data_events.iloc[i][j])
                ind += 1
        events_log.update_cells(cel_l)
    context = {
        'message': 'Отчёт о посещениях сформирован'
    }
    return render(request, "events_visits_import.html", context)


# def contact(request):
#     return render(request, "general/contact.html")
