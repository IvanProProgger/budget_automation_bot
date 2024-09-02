import logging
import asyncio
import aiosqlite

from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)



class ApprovalDB:
    """База данных для хранения данных о заявке"""
    def __init__(self):
        self.db_file = DATABASE_PATH
        self._conn = None
        self._cursor = None

    async def __aenter__(self):
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_file)
            self._cursor = await self._conn.cursor()
            logging.info("Connected to database.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            await self._conn.close()
            logging.info("Disconnected from database.")
        return True

    async def create_table(self):
        """Создает таблицу 'approvals', если она еще не существует."""
        async with self:
            await self._cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="approvals";')
            table_exists = await self._cursor.fetchone()

        if not table_exists:
            await self._cursor.execute('''CREATE TABLE IF NOT EXISTS approvals
                                          (id INTEGER PRIMARY KEY, 
                                           amount REAL, 
                                           expense_item TEXT, 
                                           expense_group TEXT, 
                                           partner TEXT, 
                                           comment TEXT,
                                           period TEXT, 
                                           payment_method TEXT, 
                                           approvals_needed INTEGER, 
                                           approvals_received INTEGER,
                                           status TEXT,
                                           approved_by TEXT)''')
            await self._conn.commit()
            logging.info("Таблица 'approvals' создана.")
        else:
            logging.info("Таблица 'approvals' уже существует.")

    async def insert_record(self, record):
        """
        Вставляет новую запись в таблицу 'approvals'.
        """
        try:
            await self._cursor.execute(
                'INSERT INTO approvals (amount, expense_item, expense_group, partner, comment, period, payment_method,'
                'approvals_needed, approvals_received, status, approved_by) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                list(record.values())
            )
            await self._conn.commit()
            logging.info("Record inserted successfully.")
            return self._cursor.lastrowid
        except Exception as e:
            logging.error(f"Failed to insert record: {e}")
            raise

    async def get_row_by_id(self, row_id):
        try:
            result = await self._cursor.execute('SELECT * FROM approvals WHERE id=?', (row_id,))
            row = await result.fetchone()
            if row is None:
                return None
            return dict(zip(('id', 'amount', 'expense_item', 'expense_group', 'partner', 'comment', 'period',
                             'payment_method', 'approvals_needed', 'approvals_received', 'status', 'approved_by'), row))
        except Exception as e:
            logging.error(f"Failed to fetch record: {e}")
            return None

    async def update_row_by_id(self, row_id, updates):
        try:
            await self._cursor.execute(
                'UPDATE approvals SET {} WHERE id = ?'.format(', '.join([f"{key} = ?" for key in updates.keys()])),
                list(updates.values()) + [row_id]
            )
            await self._conn.commit()
            logging.info("Record updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update record: {e}. Approval ID: {row_id}, Updates: {updates}")
            raise

    async def find_not_paid(self):
        try:
            result = await self._cursor.execute('SELECT * FROM approvals WHERE status != ? AND status != ?',
                                                ('Paid', 'Rejected'))
            rows = await result.fetchall()
            if not rows:
                return []

            return [dict(zip(('id заявки', 'сумма', 'статья', 'группа', 'партнёр', 'комментарий', 'период дат',
                              'способ оплаты', 'апрувов требуется', 'апрувов получено', 'статус', 'кем апрувенно'),
                             row)) for row in rows]
        except Exception as e:
            logging.error(f"Failed to fetch records: {e}")

            return []
