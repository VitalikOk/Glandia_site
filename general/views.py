from django.shortcuts import render
import general.main_func as mf


def disply_table_html(data, col_name=True):
    result = '<table border="1">'
    if col_name:
        result += '<tr>'
        for n_col in data.columns:
            result += f"<th>{n_col}</th>"
        result += '</tr>'

    for ind, row in data.iterrows():
        result += f'<tr><td>{ind}</td>'
        for _, cell in row.items():
            result += f"<td>{cell}</td>"
        result += '</tr>'
    return result + '</table>'

    # !mkdir $evet_qr_path
    # !mkdir $evet_qr_path_archive
    # !mkdir $new_members_import
    # !mkdir $new_members_archive
    # Досуп к аккаунту дял библиатки gspread


def general(request):
    context = {
        'hello': 'Hello WORLD BLYT'
    }
    return render(request, "general/index.html", context)


def members(request):
    g_sheets = mf.get_google_sheet()
    # Открыывем таблицу
    all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    all_members = mf.get_all_memb_df(all_members)
    context = {
        'members': disply_table_html(all_members)
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
    g_sheets = mf.get_google_sheet()
    # Открыывем таблицу
    all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    all_members = mf.get_all_memb_df(all_members)
    log = mf.do_mailing_and_log(all_members, all_members_sheets.sheet1)
    context = {
        'mailing_log': log
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

    data_new_members = mf.pd.DataFrame()
    g_sheets = mf.get_google_sheet()
    # Открыывем таблицу
    all_members_sheets, all_members = mf.get_all_values_sheets(mf.CLUB_CP_MEMBERS_SHEET, g_sheets)
    all_members = mf.get_all_memb_df(all_members)

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
        if row['full_amount'] < 1999:
            live_time = mf.dt.timedelta(days=182)
        else:
            live_time = mf.dt.timedelta(days=365)
        return (row['date'] + live_time).strftime("%m.%Y")

    def get_new_memb_allfiles(columns):
        # получение списка файлов
        data_memb = mf.pd.DataFrame()
        file_list = mf.get_file_list(mf.new_members_import, ext='csv', echo=True)
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

        if len(file_list) > 0:
            data_memb = data_memb[data_memb['full_amount'] >= 1000]
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

    memb_columns = ['date', 'name', 'phone', 'email', 'note', 'qrc_status',
                    'team', 'expire', 'print']

    data_new_members = get_new_memb_allfiles(memb_columns)
    data_new_members['date'] = mf.pd.to_datetime(data_new_members['date']).dt.date
    all_mamb_email = list(all_members[~all_members['email']
                          .isin(['', '-'])]['email']
                          )
    data_new_members = (data_new_members[~data_new_members['email']
        .isin(all_mamb_email)]
        )
    data_new_members.sort_values(by='date', inplace=True)
    # получение номера последней записи в таблице
    mamb_last_row = len(all_members_sheets.sheet1.get_all_values())
    row_cnt, col_cnt = data_new_members.shape

    # добавление данных в гугл таблицу
    cl_rng = mf.get_abcrage(0, mamb_last_row + 1,
                            col_cnt - 1, mamb_last_row + row_cnt + 2)
    # print(cl_rng)
    cel_l = all_members_sheets.sheet1.range(cl_rng)
    ind = 0
    for i in range(row_cnt):
        for j in range(col_cnt):
            cel_l[ind].value = str(data_new_members.iloc[i][j])
            ind += 1
    all_members_sheets.sheet1.update_cells(cel_l)

    pays_ishop_sheets, pays_ishop = mf.get_all_values_sheets(mf.NEW_MEMB_ISHOP, g_sheets)
    pays_cols = {
        'date': 'sent',
        'name': 'Name',
        'phone': 'Phone',
        'email': 'Email',
        'vv_card': 'Номер_вашей_карты_ВкусВилл',
        'status': 'Статус оплаты',
        'price': 'price'
    }
    pays_ishop = mf.get_all_memb_df(pays_ishop, dc=pays_cols)
    pays_ishop = pays_ishop[pays_cols.keys()]
    pays_ishop['name'] = pays_ishop['name'].apply(lambda x: x.split()[0])
    print(pays_ishop)
    print(data_new_members)
    context = {
        'memb_add_csv': disply_table_html(data_new_members),
        'memb_add_is': disply_table_html(pays_ishop)
    }
    return render(request, "general/add_members.html", context)

#
# def contact(request):
#     return render(request, "general/contact.html")
