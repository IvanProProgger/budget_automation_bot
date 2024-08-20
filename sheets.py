import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

from config import GOOGLE_SHEETS_SPREADSHEET_ID, GOOGLE_SHEETS_CREDENTIALS_FILE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_sheets_service():
    """Авторизация и получение объекта Google Sheets API."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
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

    months = payment_info['period_start_date'].split('-')[1]
    total_amount = payment_info['amount'] / int(months)
    row_data = [
        f"Дата оплаты={payment_info['period_start_date']}",
        f"Сумма={total_amount}"
    ]
    worksheet.append_row(row_data)
    logger.info(f"Добавлена строка: {row_data}")
