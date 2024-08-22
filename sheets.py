import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime
import pytz

from config import GOOGLE_SHEETS_SPREADSHEET_ID, GOOGLE_SHEETS_CREDENTIALS_FILE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_today_moscow_time():
    """
    Получает сегодняшний день в формате дд.мм.гггг по московскому времени.
    """
    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz)
    formatted_date = today.strftime('%d.%m.%Y')
    return formatted_date


def create_sheets_service():
    """Авторизация и получение объекта Google Sheets API."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS_FILE, scope)
    gc = gspread.authorize(creds)
    logger.info("Успешная инициализация службы Google Sheets")
    return gc


def add_payment_to_sheet(gc, payment_info):
    """Добавление записи о платеже в Google Sheets."""
    try:
        spreadsheet = gc.open_by_key(GOOGLE_SHEETS_SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1
        logger.info(f"Открытие листа: {GOOGLE_SHEETS_SPREADSHEET_ID}")
    except Exception as e:
        logger.error(f"Ошибка при открытии или доступе к листу: {e}")
        return

    today_date = get_today_moscow_time()
    months = payment_info['period'].split(' ')
    total_sum = payment_info['amount'] / len(months)
    for month in months:
        row_data = [
            today_date,
            total_sum,
            payment_info['expense_item'],
            payment_info['expense_group'],
            payment_info['partner'],
            payment_info['comment'],
            month,
            payment_info['payment_method'],
            (int(today_date[3:5]) - 1) // 3 + 1,
            (int(month[3:5]) - 1) // 3 + 1
        ]
        worksheet.append_row(row_data)

        logger.info(f"Добавлена строка: {row_data}")
