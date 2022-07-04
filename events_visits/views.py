from django.shortcuts import render
import general.main_func as mf
import pandas as pd
import general.db_func as dbf
from general.models import Users, Contacts, EventsVisits, CollectionPoints
from django.db.models import Q
from datetime import datetime

EV_COLUMNS = mf.ev_columns + ['gid', 'vv_card']
EV_COLUMNS_BD = ['date', 'gid', 'expire', 'event', 'vv_card']

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


def check_field(row, field_name):
    """
    Функция для заполнения пустых полей
    """
    if (field_name not in row.index) or (row[field_name] == '') or (field_name == 'expire'):

        bd_filds = {
            'date': 'date_time',
            'gid': 'gid',
            'expire': 'expire',
            'note': 'note',
            'vv_card': 'vvcard',
            'phone': 'phone',
            'name': 'name',
            'email': 'elmail'
        }


        # result = (all_members.loc[(all_members['phone'] == row['phone'])
        #                           | (all_members['vv_card'] == row['vv_card'])
        # , [field_name]].values
        #           )


        q_set = list(Contacts.objects.select_related('user')
                        .filter(Q(phone=row['phone']) | Q(user__vvcard=row['vv_card']))
                        .values_list('gid')
                        )
        gid = None
        result = None
        if len(q_set) > 0:
            gid = q_set[0][0]   
            if field_name == 'gid':
                result  = int(gid)
            else:
                try:
                    memb = Users.objects.filter(gid=gid)        
                    result = getattr(memb[0], bd_filds[field_name])
                except:
                    memb = Contacts.objects.filter(gid=gid)        
                    result = getattr(memb[0], bd_filds[field_name])                                     
        
        if result is not None and gid is not None:
            row[field_name] = result
        else:
            if field_name == 'gid':
                row[field_name] = 0
            else:
                row[field_name] = f"{mf.COLUMS_NAMES[field_name]} не указано"
            
    return row[field_name]


def fill_data(data):
    """
    Функция для востановления данных из разных источников
    """
    data_ev = pd.DataFrame(columns=EV_COLUMNS)
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
        for col in EV_COLUMNS:
            if col not in ['event']:
                data_ev.loc[ind, col] = check_field(row, col)
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
            attrs['vv_card'] = attr['value'].replace('Карта', '').strip(' №').strip()
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


def get_last_date():
    return EventsVisits.objects.all().order_by('date_time').last().date_time     


def events_visits_menu(request):
    return render(request, "events_visits_menu.html")


def events_visits_import(request):
    # Импорт данных с акций
    data_events = pd.DataFrame(columns=EV_COLUMNS)
    no_members = pd.DataFrame(columns=EV_COLUMNS)
    import_config = {
        'manual_imput': True
        , 'qr_form_ws_import_api': True
        , 'scan_qr_from_ws_api': True
        , 'export_to_bd': True
    }

    g_sheets = mf.get_google_sheet()
    last_date = get_last_date()
    # last_date = mf.datetime.strptime(last_date, '%Y-%m-%d %H:%M:%S')
    mf.write_log('api_import.log',f'Got last date {last_date}')
    # Импорт данных об участниках введйнных вручную
    def add_manual_imput(month, data_events, g_sheets):
        ma_sheets, rows = mf.get_all_values_sheets(mf.MANUAL_ADD_SHEET + month, g_sheets)
        if ma_sheets is not None and len(rows) > 1:
            ma_bonus = mf.get_data_from_gs(ma_sheets, rows[1:]
                                        , columns=rows[0]
                                        , new_sheet=True)
            ma_bonus['event'] = 'Бонус за вступление, ручной ввод'
            # заполнение полей
            ma_bonus = fill_data(ma_bonus)
            # Добавления данных введйнных вручную к остальным
            data_events = pd.concat([data_events, ma_bonus], ignore_index=True)
        else:
            print(f"Данные в таблтце \"{mf.MANUAL_ADD_SHEET + mf.MONTH}\" не найдены")
        return data_events

    

    if import_config['manual_imput']:
        if last_date.strftime("%m") < mf.MONTH:
            data_events = add_manual_imput(mf.PREV_MONTH, data_events, g_sheets)
        data_events = add_manual_imput(mf.MONTH, data_events, g_sheets)
        mf.write_log('api_import.log',f'Add manual import {len(data_events)} records')

    # Импорт данных о посещениях из API app.waveservice.ru
    # api.waveservice.ru/public/v1/docs#/
    if import_config['qr_form_ws_import_api']:
        start_date = last_date
        len_rep = 100
        while len_rep == 100:
            ws_json = get_waveservice_api(created_from=start_date)
            if len(ws_json['items']) > 0:
                report = ws_report_topd(ws_json, action_type='Получить бонусы')
                len_rep = len(ws_json['items'])
                start_date = str(pd.to_datetime(report.iloc[-1]['date'])
                                 - pd.DateOffset(hours=3, seconds=59)
                                 )                               
                report = fill_data(report)
                mf.write_log('api_import.log',f'check_ins {len_rep} records last date {start_date} len report after fill {len(report)}')                                  
                data_events = pd.concat([data_events,
                                         report[EV_COLUMNS]],
                                        ignore_index=True
                                        )
                no_members = data_events[data_events['gid'] == 0]
                mf.write_log('api_import.log',f'Add qr_form_ws_import_api {len(data_events)} records')
            else:
                mf.write_log('api_import.log',f'Нет данных о посещениях из API app.waveservice.ru c {last_date}')
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
                mf.write_log('api_import.log',f'check_ins {len_rep} records last date {start_date}')                                 
                report = fill_data(report)
                report['event'] = 'Мобильная станци'
                data_events = pd.concat([data_events,
                                         report[EV_COLUMNS]],
                                        ignore_index=True
                                        )
                data_events = fill_data(data_events)
                mf.write_log('api_import.log',f'Add scan_qr_from_ws_api {len(data_events)} records')
            else:                
                mf.write_log('api_import.log',f'Нет данных о check_ins из API app.waveservice.ru c {last_date}')
                break

    # ===================Обработка данных====================
    # сортировка и заполненин nan
    data_events.sort_values(by='date', inplace=True)
    data_events.reset_index(drop=True, inplace=True)
    data_events['gid'] = data_events['gid'].astype('int')
    # data_events.fillna('', inplace=True)
    # data_events = data_events[data_events['gid'] != 0]

    if import_config['export_to_bd']:
        # добавление данных в таблицу
        for ind, row in data_events.iterrows():
            dbf.add_visit(row)
        mf.write_log('api_import.log',f'Imported to db {len(data_events)} records')

    context = {
        'message': 'Отчёт о посещениях сформирован',
        'start_date': last_date,
        'visits_num': len(data_events),
        'no_members': mf.disply_table_html(no_members),
        'members': mf.disply_table_html(data_events[EV_COLUMNS_BD]),
    }
    return render(request, "events_visits_import.html", context)


# def contact(request):
#     return render(request, "general/contact.html")


def event_add_form(request):
    points = CollectionPoints.objects.all()

    if request.method == "POST" and (request.POST['vvcard'] != '' or gid != 0) :
        if request.POST['gid'] == '':
            gid = 0
        else:
            gid = request.POST['gid']
        user_data = pd.Series(list(Users.objects.filter(Q(gid=gid) | Q(vvcard=request.POST['vvcard'])).values()))
        if len(user_data) > 0:
            user_data = user_data[0]
            context = {'points': points,
                    'today':  request.POST['date_time'],
                    'gid': user_data['gid'],
                    'expire': datetime.strptime(user_data['expire'], "%d.%m.%Y").strftime("%Y-%m-%d"),
                    'vvcard': user_data['vvcard'],                
                    }
        else:
            context = {'points': points,
                    'today':  request.POST['date_time'],
                    'gid': request.POST['gid'],
                    'expire': request.POST['expire'],
                    'vvcard': request.POST['vvcard'],                
                    }
    else:
        context = {
                   'points': points,
                   'today':  datetime.now().date().strftime("%Y-%m-%d")
                   }
    return render(request, "event_add_form.html", context)

def add_event(request):
    if request.method == "POST":
        if request.POST['amount'] == '':
            amount = 0
        else:
            amount = request.POST['amount']

        if request.POST['expire'] != '':
            expire_date = datetime.strptime(request.POST['expire'], "%Y-%m-%d").strftime("%d.%m.%Y")
        else:
            expire_date = 'Срок действия не указано'



        event, created = EventsVisits.objects.get_or_create(
            date_time = request.POST['date_time'],
            gid = request.POST['gid'],
            expire = expire_date,
            note = request.POST['note'],
            vvcard = request.POST['vvcard'],
            special_amount = amount,
        )
        
        if created:
            message = 'Запись события создана'
        else:
            message = 'Ошибка при создании записи'        

        context = {
            'message': message
        }

    return render(request, "event_add_result.html", context)


    '''
    
    <!-- date_time = models.DateTimeField(verbose_name="дата посещения")
    gid = models.IntegerField(verbose_name = "идентификатор", null=True)
    expire = models.CharField(verbose_name="дата истечения на момент акции", max_length=64, null=True) # input_formats=["%d-%m-%Y"]
    note = models.TextField(verbose_name="заметка", blank=True)    
    vvcard = models.CharField(verbose_name="номер карты ВВ на момент акции", max_length=64, default="НЕТ КАРТЫ") -->
    
    '''
