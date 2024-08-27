import aiosqlite
import logging

from config import DATABASE_PATH

logging.basicConfig(level=logging.INFO)


class ApprovalDB:
    def __init__(self):
        self.db_file = DATABASE_PATH

    async def __aenter__(self):
        self.conn = await aiosqlite.connect(self.db_file)
        self.cursor = await self.conn.cursor()
        logging.info("Connected to database.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()
        logging.info("Disconnected from database.")
        return True

    async def create_table(self):
        """Создает таблицу 'approvals', если она еще не существует."""
        await self.cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="approvals";')
        table_exists = await self.cursor.fetchone()
        if not table_exists:
            await self.cursor.execute('''CREATE TABLE approvals
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
            await self.conn.commit()
            logging.info("Таблица 'approvals' создана.")
        else:
            logging.info("Таблица 'approvals' уже существует.")

    async def insert_record(self, record):
        """
        Вставляет новую запись в таблицу 'approvals'.
        """
        try:
            await self.cursor.execute(
                'INSERT INTO approvals (amount, expense_item, expense_group, partner, comment, period, payment_method,'
                'approvals_needed, approvals_received, status, approved_by) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                list(record.values())
            )
            await self.conn.commit()
            logging.info("Record inserted successfully.")
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Failed to insert record: {e}")
            raise

    async def get_row_by_id(self, row_id):
        try:
            result = await self.cursor.execute('SELECT * FROM approvals WHERE id=?', (row_id,))
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
            await self.cursor.execute(
                'UPDATE approvals SET {} WHERE id = ?'.format(', '.join([f"{key} = ?" for key in updates.keys()])),
                list(updates.values()) + [row_id]
            )
            await self.conn.commit()
            logging.info("Record updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update record: {e}. Approval ID: {row_id}, Updates: {updates}")
            raise

    async def concat_column_by_id(self, row_id, column_name, new_value):
        try:
            current_row = await self.get_row_by_id(row_id)
            current_value = current_row.get(column_name)

            if current_value is None or current_value.strip() == '':
                await db.update_row_by_id(row_id, {column_name: new_value})
            else:
                await db.update_row_by_id(row_id, {column_name: current_value + ' ' + new_value})
            await self.conn.commit()
            logging.info(f"Column '{column_name}' appended to existing value for approval ID: {row_id}")
        except Exception as e:
            logging.error(
                f"Failed to update column: {e}. Approval ID: {row_id}, Column: {column_name}, New value: {new_value}")
            raise

    async def find_not_processed_rows(self):
        try:
            result = await self.cursor.execute('SELECT * FROM approvals WHERE status = ?', ("Not processed",))
            rows = await result.fetchall()
            if not rows:
                return []
            return [dict(zip(('id', 'amount', 'expense_item', 'expense_group', 'partner', 'period', 'payment_method',
                              'comment', 'approvals_needed', 'approvals_received', 'status', 'approved_by'),
                             row)) for row in rows]
        except Exception as e:
            logging.error(f"Failed to fetch records: {e}")
            return []


db = ApprovalDB()
