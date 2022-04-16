# Параметры рассылки
# Имя документа в Google Sheets
# Список всех членов клуба
CLUB_CP_MEMBERS_SHEET = 'Участники ЭкоКлуба Чистый Петербург'
NEW_MEMB_ISHOP = 'ЭкоКлуб - участники'
# Внесённые вручную участники для перечислени бонусов
# MANUAL_ADD_SHEET + mm (номер мксяцев 01...12)
MANUAL_ADD_SHEET = 'Бонусы за акции '
# SCAN_SHEET таблица сканирования qr на акциях
SCAN_SHEET = 'ЧП Акции сканер'
# История всех посещенных акций + mm (номер мксяцев 01...12)
EVENTS_VISITS = 'Посещения акций '
ev_columns = ['date', 'phone', 'name', 'expire', 'email', 'event']

# имена файлов отсётов для ВВ
VV_EVENTS_REPORT = 'ВВ Чистый Петербург акции '
VV_MEMBERS_REPORT = 'ВВ Чистый Петербург члены клуба '

# Отправка только своим - True, всем - False
TEAM_SEND = False
# Мия файла лога
LOG_FILE_NAME = 'mailing.log'
LOG_PATH = 'general/log/'
from gland_site.settings import STATIC_URL
from gland_site.settings import MEDIA_URL
123
# пути к csv файлов с отсканированными qr кодами
evet_qr_path = STATIC_URL + 'event_qr/'
evet_qr_path_archive = STATIC_URL + 'event_qr/archive/'
new_members_import = STATIC_URL + 'new_members/'
new_members_archive = STATIC_URL + 'new_members/archive/'
# smtp сервер
SMTP_SERVER = "smtp.yandex.ru"  # "smtp.gmail.com"
SMTP_PORT = 465  # 587 #

# Соответсвия называний колонок основной таблицы
COLUMS_NAMES = {
    'date_in': 'Дата вступления'
    , 'name': 'Имя Фамилия'
    , 'phone': 'Номер телефона'
    , 'email': 'Email'
    , 'note': 'Примечания'
    , 'sended': 'QR-код отправлен'
    , 'team': 'Свои'
    , 'expire': 'Срок действия'
    , 'print': 'Надо печатать'
    , 'vv_card': 'Номер карты ВВ'
}

ABC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

# Тема письма рассылуа qr
SUBJECT = "Ваш персональный QR-код от проекта Чистый Петербург"

# генерация qr
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from PIL import Image
# отпраыка e-mail smtp
import smtplib
# формирование тела письма
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
# кодирования информации в 64-разрядный код (6 бит),
# широко используемый в приложениях электронной почты
from email import encoders
# BeautifulSoup для парсига html в текст
from bs4 import BeautifulSoup as bs
# для работы с таблицей
import pandas as pd
# для работы с google sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials
# длф работы с датой
from datetime import datetime
from dateutil.relativedelta import relativedelta
import datetime as dt
from transliterate import translit
import calendar
import requests
import json
import re
import general.email_texts as et
import os

with open('general/conf/email.json') as fm:
    em = json.load(fm)
# Адрес и пароль для отправки почты
SENDER_EMAIL = em['email']
SENDER_PASSWORD = em['pw']
# Адрес отправителя
FROM = em['email']

# получение текущего месяца
MONTH = datetime.now().strftime("%m")
PREV_MONTH = (datetime.now() - relativedelta(months=1)).strftime("%m")
YEAR = datetime.now().strftime("%Y")


def translit_safe(data, reversed=True):
    try:
        return translit(data, reversed)
    except:
        return data

def correct_phone_number(p_number):
    return p_number[-10:]


def split_delsps(str_in, div=','):
    return str_in.replace(' ', '').split(div)


def make_qrcode(row):
    # taking image which user wants
    # in the QR code center
    logo = STATIC_URL + 'logo.png'
    back_ground = STATIC_URL + 'back_pic.png'
    back_ground = Image.open(back_ground)

    QRcode = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
        , border=2,
        box_size=14
    )
    # adding DATA text to QRcode
    if type(row) == str:
        data = row
        filename = "qr_code_link.png"
    else:
        data = (f"{split_delsps(row['email'])[0]} {row['expire']} "
                + f"{translit_safe(row['name'], reversed=True)} "
                + f"{correct_phone_number(row['phone'])}"
                )
        filename = "qr_code.png"
    QRcode.add_data(data)
    # generating QR code
    QRcode.make()
    # adding color to QR code
    QRimg = QRcode.make_image(image_factory=StyledPilImage,
                              module_drawer=RoundedModuleDrawer(),
                              # color_mask=RadialGradiantColorMask(center_color=(0,255,253),
                              #                                    edge_color=(255,0,252)),
                              fill_color='Black',
                              back_color="white",
                              embeded_image_path=logo).convert('RGB')
    pos = ((back_ground.size[0] - QRimg.size[0]) // 2,
           (back_ground.size[1] - QRimg.size[1] - 15) // 2)
    back_ground.paste(QRimg, pos)

    # save the QR code generated
    back_ground.save(MEDIA_URL + filename)
    return MEDIA_URL + filename


def make_mail(text_to_send, to='', files_to_send='no_file',
              from_email=FROM):
    # initialize the message we wanna send
    subject = SUBJECT
    msg = MIMEMultipart("mixed")
    msg["From"] = from_email
    msg["To"] = to
    msg["Subject"] = subject
    message = MIMEMultipart("alternative")
    html = text_to_send
    text = bs(html, "html.parser").text
    message.attach(MIMEText(text, 'plain'))
    message.attach(MIMEText(html, 'html'))
    msg.attach(message)
    if files_to_send != 'no_file':
        part = MIMEBase("image", "png")
        with open(files_to_send, "rb") as attachment:
            part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f"attachment; filename={files_to_send}")
        msg.attach(part)
    return msg


def do_mailing(mail_list, team=False, to='', sender=SENDER_EMAIL,
               password=SENDER_PASSWORD, from_email=FROM, msg_text='main'):
    # initialize the SMTP server
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    # connect to the SMTP server as TLS mode (secure) and send EHLO
    # server.starttls()
    # login to the account using the credentials
    server.login(sender, password)
    log = []
    log_str = ''
    for index, row in mail_list.iterrows():
        if (not team) or row['team'].lower() == 'cотрудник':
            if ((row['email'] not in ['', '-'] and row['sended'] == '')
                    or msg_text == 'no card'):
                try:
                    if msg_text == 'main':
                        qr_code_file = make_qrcode(row)
                        msg = make_mail(et.make_text(row['name']), to=row['email'],
                                        files_to_send=qr_code_file, from_email=from_email)
                    elif msg_text == 'no card':
                        msg = make_mail(et.make_text_nocard(row['name']), to=row['email']
                                        , from_email=from_email)
                    elif msg_text == 'media':
                        msg = make_mail(et.make_text_media(row['name']), to=row['email']
                                        , from_email=from_email)

                    # send the email
                    server.sendmail(from_email, split_delsps(row['email']), msg.as_string())
                    log_str = (f"{datetime.now()} {index} || {row['name']} || "
                               + f"{row['phone']} || {row['email']} || Email has been sent"
                               )
                    print(log_str)
                    log.append(log_str)
                    row['sended'] = 'ДА'
                # except ValueError:
                except BaseException as err:
                    log_str = (f"{datetime.now()} {index} || {row['name']} || "
                               + f"{row['phone']} || {row['email']} ||Err {err}, {type(err)}"
                               )
                    # print(log_str)
                    log.append(log_str)
    # terminate the SMTP session
    server.quit()

    with open(LOG_PATH + LOG_FILE_NAME, 'a') as f:
        f.write(str(log) + '\n')
    return mail_list, log


def get_keybyval(val, dc=COLUMS_NAMES):
    """
    key by value in dict
    """
    for idn, v in dc.items():
        if v == val:
            return (idn)
    return val


def rename_colbyvals(data, vals, dc=COLUMS_NAMES):
    """
    rename columns by list of vals
    using columns name dict
    """
    for val in vals:
        data = data.rename(columns={val: get_keybyval(val, dc)})
    return data


def get_abcrage(x1, y1, x2, y2):
    return f"{ABC[x1]}{y1}:{ABC[x2]}{y2}"


def all_memb_rewrite_column(data, column_name, sheet, start_str=2):
    # установка статуса отправки писем в google sheets
    n_count = len(data) + 1
    n_columns = len(data.columns)
    qrc_s_ind = 0
    for i in range(n_columns):
        if data.columns[i] == column_name:
            qrc_s_ind = i
    range_s = get_abcrage(qrc_s_ind, start_str, qrc_s_ind, n_count)
    status = sheet.range(range_s)
    for ind, row in data.iterrows():
        status[ind].value = row[column_name]
    sheet.update_cells(status)


def do_mailing_and_log(mail_list, sheets):
    mail_list, log = do_mailing(mail_list, team=TEAM_SEND)
    all_memb_rewrite_column(mail_list, 'sended', sheets)
    return log


def get_all_values_sheets(file_name, g_sheets):
    try:
        sheets = g_sheets.open(file_name)
    except:
        print(f'Google таблица: "{file_name}" не найдена')
        return None, None
    return sheets, sheets.sheet1.get_all_values()


def get_all_memb_df(rows, dc=COLUMS_NAMES):
    data_memb = pd.DataFrame(rows[1:], columns=rows[0])
    data_memb = rename_colbyvals(data_memb, data_memb.columns, dc)
    return data_memb


def get_all_memb_fr_sheet(sheets):
    return get_all_memb_df(sheets.sheet1.get_all_values())


def get_data_from_gs(sheets, rows, columns, new_sheet=True):
    if rows == None:
        return None
    data = pd.DataFrame(rows, columns=columns)
    if len(data) > 0:
        data['date'] = pd.to_datetime(data['date'], format='%Y-%m-%d %H:%M:%S')
        data_range = data['date'].apply(lambda x: x.strftime('%d.%m'))
        list_name = (f"{data_range.min().split('.')[0]}-"
                     + f"{data_range.max()}"
                     )
        sheets.sheet1.update_title(list_name)
        if new_sheet:
            sheets.add_worksheet(title="new", rows="37", cols="10", index=0)
            # добавление столбцов на новый лист
            cl_rng = get_abcrage(0, 1, len(columns) - 1, 1)
            cel_l = sheets.sheet1.range(cl_rng)
            for i in range(len(columns)):
                cel_l[i].value = columns[i]
            sheets.sheet1.update_cells(cel_l)
    return data


def get_file_list(path, ext='csv', echo=True, recursive=False):
    """
    Получение списка файлов
    """
    file_list = os.listdir(path)
    for item in file_list:
        if '.' + ext not in item:
            file_list.remove(item)
    # file_list = !ls $path | grep $finde
    if echo:
        print(f"В дирректории {path} найдено {ext} файлов {len(file_list)}")
        if len(file_list) > 0:
            print(f"{file_list}")
    return file_list


def move_files(file_list, source, destination, echo=False):
    """
    Перенос csv файлов в архив
    """
    for file in file_list:
        sr_file = source + file
        dest_file = destination + file
        if echo:
            print(f"Перемеще {sr_file} -> {dest_file}")
            os.replace(sr_file, dest_file)


def change_cir_lat(in_str):
    """
    Замена кирилических букв на латинские
    """
    ltrs = {
        'А': 'A',
        'В': 'B',
        'С': 'C',
        'Д': 'D',
        'Н': 'H',
        'а': 'A',
        'в': 'B',
        'с': 'C',
        'д': 'D',
        'н': 'H',
    }
    pattern = r"\b\w{6,8}\b"
    if re.fullmatch(pattern, in_str):
        for lt in ltrs:
            in_str = in_str.replace(lt, ltrs[lt])
    return in_str.upper()


def get_google_sheet():
    return gspread.service_account(filename='general/conf/gs.json')


def get_all_members(g_sheets=get_google_sheet()):
    # Открыывем таблицу
    all_members_sheets, all_members = get_all_values_sheets(CLUB_CP_MEMBERS_SHEET, g_sheets)
    return get_all_memb_df(all_members)
