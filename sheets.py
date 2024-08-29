import asyncio

import gspread_asyncio
from google.oauth2.service_account import Credentials
import logging
from datetime import datetime
import pytz
import pandas as pd

from config import GOOGLE_SHEETS_SPREADSHEET_ID, GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_CATEGORIES_SHEET_ID, \
    GOOGLE_SHEETS_RECORDS_SHEET_ID


async def get_today_moscow_time():
    moscow_tz = pytz.timezone('Europe/Moscow')
    today = datetime.now(moscow_tz)
    formatted_date = today.strftime('%d.%m.%Y')
    return formatted_date


def get_credentials():
    creds = Credentials.from_service_account_file(GOOGLE_SHEETS_CREDENTIALS_FILE)
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


class GoogleSheetsManager:
    def __init__(self):
        self.credentials_file = GOOGLE_SHEETS_CREDENTIALS_FILE
        self.sheets_spreadsheet_id = GOOGLE_SHEETS_SPREADSHEET_ID
        self.records_sheet_id = GOOGLE_SHEETS_RECORDS_SHEET_ID
        self.categories_sheet_id = GOOGLE_SHEETS_CATEGORIES_SHEET_ID
        self.options_dict = None
        self.items = None
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.agc = None

    async def initialize_google_sheets(self):
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_credentials)
        self.agc = await agcm.authorize()
        return self.agc

    async def add_payment_to_sheet(self, payment_info):
        try:
            spreadsheet = await self.agc.open_by_key(self.sheets_spreadsheet_id)
            worksheet = await spreadsheet.get_worksheet_by_id(1)
            self.logger.info(f"Открытие листа: {self.sheets_spreadsheet_id}")
        except Exception as e:
            self.logger.error(f"Ошибка при открытии или доступе к листу: {e}")
            return

        today_date = await get_today_moscow_time()
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
            await worksheet.append_row(row_data)

            self.logger.info(f"Добавлена строка: {row_data}")

    async def get_data(self):
        spreadsheet = await self.agc.open_by_key(self.sheets_spreadsheet_id)
        worksheet = await spreadsheet.get_worksheet_by_id(self.categories_sheet_id)

        df = pd.DataFrame(await worksheet.get_all_records())
        unique_items = df['Статья'].unique()
        data_structure = {}

        for _, row in df.iterrows():
            category = row['Статья']
            group = row['Группа']
            partner = row['Партнер']

            if category not in data_structure:
                data_structure[category] = {}

            if group not in data_structure[category]:
                data_structure[category][group] = []

            data_structure[category][group].append(partner)

        self.options_dict, self.items = data_structure, unique_items

        return data_structure, unique_items