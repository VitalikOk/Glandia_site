from django.shortcuts import render
import general.main_func as mf
import general.db_func as dbf
from general.models import Users, Contacts
from general.enums import ROLES


def general(request):
    context = {
        'hello': 'Hello WORLD BLYT'
    }
    return render(request, "general/index.html", context)


def menu(request):
    with open('general/conf/ac.json') as fm:
        ac = mf.json.load(fm)
    context = {
        'access': 'user'
    }    
    if request.method == 'POST':
        if request.POST['login'] == ac['user'] and request.POST['pwd'] == ac['pwd']:
            context['access'] = 'loop'
    return render(request, "general/menu.html", context)


# def members(request):
#     g_sheets = mf.get_google_sheet()
#     # Открыывем таблицу
#     all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
#     all_members = mf.get_all_memb_df(all_members)
#     context = {
#         'members': mf.disply_table_html(all_members)
#     }
#     return render(request, "general/members.html", context)

def members(request):  
    columns = {
        'gid': 'G-id',
        'date_in': 'Дата вступления',
        'is_sended': 'Отправлен QR',
        'note': 'Примечание',
        'expire': 'Годен до',
        'vvcard': 'Каота ВВ',
        'role_id': 'Роль',
    }
    # contacts = Contacts.objects.all()
    context = {
        'members': mf.disply_table_dj_html(Users.objects.all(), dc=columns)
        # 'contacts': contacts
    }

    return render(request, "general/members.html", context)

def create_qr_code(request):
    context = {
        'qr_img': '/media/back_pic.png'
    }
    if request.method == 'POST':
        context['qr_img'] = '/' + mf.make_qrcode(request.POST['qr_data'])
    return render(request, "general/create_qr.html", context)


def add_mem_qrsend(request):
    return render(request, "general/add_mem_qrsend.html")


def qr_email_sending(request):    
    # Открыывем таблицу
    mailing_list = []
    q_set = list(Contacts.objects.select_related('user')
                         .filter(user__is_sended=False)
                         .exclude(elmail__in=('', '-'))
                         .values_list('gid', 'elmail', 'phone', 'name', 'user__role', 'user__is_sended', 'user__expire')
                         )

    dc = [
        'gid', 'email', 'phone', 'name', 'team', 'sended', 'expire'        
    ]

    for memb_email in q_set:
        mailing_list.append(list(memb_email))        
        mailing_list[-1][-3] = ROLES[mailing_list[-1][-3]-1]

    mailing_list = mf.pd.DataFrame(mailing_list, columns=dc)

    log = mf.do_mailing_and_log_db(mailing_list)
    context = {
        'mailing_log': [x + '<br>' for x in log]
    }
    return render(request, "general/qr_email_sending.html", context)


def add_members(request):
    
    NEW_MEMBERS_COLUMNS = {
        'id': 'id',
        'name': 'Имя донора',
        'email': 'Email',
        'payment_type': 'Тип платежа',
        'payment_oper': 'Плат. оператор',
        'payment_method': 'Способ платежа',
        'full_amount': 'Полная сумма',
        'total_amount': 'Итоговая сумма',
        'Currency': 'Currency',
        'date': 'Дата пожертвования',
        'status': 'Статус',
        'campaign': 'Кампания',
        'purpose': 'Назначение',
        'subscribe': 'Подписка на рассылку',
        'email_sub': 'Email подписки',
        'comment': 'Комментарий'
    }


    def get_new_members(file_name):
        """
        Чтение и обработка данных из cvs файла
        """
        data_memb = mf.pd.read_csv(file_name, header=0, index_col=False,
                                   sep='\t',
                                   encoding='UTF-16LE'
                                   )

        data_memb = mf.rename_colbyvals(data_memb, data_memb.columns,
                                        dc=NEW_MEMBERS_COLUMNS)
        data_memb = data_memb.loc[data_memb['status'] == 'Оплачено']
        data_memb['name'] = data_memb['name'].apply(lambda x: x.split()[0])

        return data_memb[['date', 'name', 'email', 'full_amount']]


    def get_exp_date(row):
        if int(row['full_amount']) > 1990:
            exp_date = mf.add_months_for_date(row['date'], 12)
        if int(row['full_amount']) > 990:
            exp_date = mf.add_months_for_date(row['date'], 6)
        else:
            exp_date = mf.add_months_for_date(row['date'], 1)
        return exp_date.strftime("%d.%m.%Y")


    def get_new_memb_ishop(new_memberrs_gs, g_sheets):
        pays_ishop_sheets, pays_ishop = mf.get_all_values_sheets(new_memberrs_gs, g_sheets)
        pays_cols = {
            'date': 'sent',
            'name': 'Name',
            'phone': 'Phone',
            'email': 'Email',
            'vv_card': 'card',
            'status': 'Статус оплаты',
            'full_amount': 'price'
        }
        pays_ishop = mf.get_all_memb_df(pays_ishop, dc=pays_cols)
        pays_ishop = pays_ishop[pays_cols.keys()]
        pays_ishop['date'] = mf.pd.to_datetime(pays_ishop['date'])
        pays_ishop['name'] = pays_ishop['name'].apply(lambda x: x.split()[0])
        pays_ishop['phone'] = pays_ishop['phone'].apply(mf.correct_phone_number)     
        pays_ishop['vv_card'] = pays_ishop['vv_card'].apply(lambda x: mf.correct_vv_card(x) 
                                                                if x!='' else 'НЕТ КАРТЫ')    
        pays_ishop['expire'] = pays_ishop.apply(get_exp_date, axis=1)
        pays_ishop['note'] = ''
        pays_ishop['qrc_status'] = ''
        pays_ishop['team'] = ''
        pays_ishop['print'] = ''
        pays_ishop = pays_ishop.drop(columns=['status','full_amount'])
        print(pays_ishop)
        return pays_ishop        


    def get_new_memb_allfiles(columns):
        # получение списка файлов
        data_memb = mf.pd.DataFrame()
        file_list = mf.get_file_list(mf.new_members_import, ext='csv', echo=True)

        if len(file_list) > 0:
            for file in file_list:
                data_memb = mf.pd.concat([data_memb,
                                      get_new_members(mf.new_members_import + file)],
                                     ignore_index=True
                                     )

                data_memb = (data_memb.groupby('email')
                         .agg({'date': 'last',
                               'name': 'last',
                               'full_amount': 'sum'})
                         .reset_index(drop=False)
                         )

            #data_memb = data_memb[data_memb['full_amount'] >= 1000]
            data_memb['date'] = mf.pd.to_datetime(data_memb['date'])
            data_memb['expire'] = data_memb.apply(get_exp_date, axis=1)
            data_memb['phone'] = '!!!'
            data_memb['note'] = ''
            data_memb['qrc_status'] = ''
            data_memb['team'] = ''
            data_memb['print'] = ''

            mf.move_files(file_list, mf.new_members_import, mf.new_members_archive, echo=True)
            # print(data_memb)
        else:
            print(f'Данные для импорта не найдены')
            return mf.pd.DataFrame(columns=columns)
        return data_memb[columns].reset_index(drop=True)

    data_new_members = mf.pd.DataFrame()
    g_sheets = mf.get_google_sheet()
    # Открыывем таблицу
    # all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    # all_members = mf.get_all_memb_df(all_members)


    memb_columns = ['date', 'name', 'phone', 'email', 'note', 'qrc_status',
                    'team', 'expire', 'print']

    data_new_members = get_new_memb_allfiles(memb_columns)
    pays_ishop = get_new_memb_ishop(mf.NEW_MEMB_ISHOP, g_sheets)

    data_new_members = mf.pd.concat([data_new_members,
                                      pays_ishop],
                                     ignore_index=True
                                     )
    data_new_members['date'] = mf.pd.to_datetime(data_new_members['date']).dt.date                                     

    all_mamb_email = []
    q_set = list(Contacts.objects.only('elmail').exclude(elmail__in=('', '-')).values_list('elmail'))

    for memb_email in q_set:
        all_mamb_email.append(memb_email[0])


    data_new_members = (data_new_members[~data_new_members['email']
        .isin(all_mamb_email)]
        )
        
    data_new_members.sort_values(by='date', inplace=True)
    
    # добавление данных в БД
    for ind, member in data_new_members.iterrows():
        dbf.add_user(member)

    
    context = {
        # 'memb_add_is': mf.disply_table_html(pays_ishop),
        'memb_add': mf.disply_table_html(data_new_members),        
    }
    return render(request, "general/add_members.html", context)

#
# def contact(request):
#     return render(request, "general/contact.html")
