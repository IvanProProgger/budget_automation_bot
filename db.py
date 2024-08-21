import aiosqlite
import logging


logging.basicConfig(level=logging.INFO)


class ApprovalDB:
    def __init__(self):
        self.db_file = "./approvals.db"

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
        await self.cursor.execute('''CREATE TABLE IF NOT EXISTS approvals
                                      (id INTEGER PRIMARY KEY, 
                                       amount REAL, 
                                       expense_item TEXT, 
                                       expense_group TEXT, 
                                       partner TEXT, 
                                       period TEXT, 
                                       payment_method TEXT, 
                                       comment TEXT,
                                       approvals_needed INTEGER, 
                                       approvals_received INTEGER,
                                       status TEXT)''')
        await self.conn.commit()
        logging.info("Таблица 'approvals' создана.")

    async def insert_record(self, record):
        approvals_needed_value = 1 if float(record["amount"]) < 50000 else 2
        record["approvals_needed"] = approvals_needed_value
        record["approvals_received"] = 0
        record["status"] = "Created"
        try:
            await self.cursor.execute(
                'INSERT INTO approvals (amount, expense_item, expense_group, partner, period, payment_method, comment, '
                'approvals_needed, approvals_received, status) VALUES (?,?,?,?,?,?,?,?,?,?)',
                list(record.values())
            )
            await self.conn.commit()
            logging.info("Record inserted successfully.")
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Failed to insert record: {e}")
            raise

    async def update_row_by_id(self, approval_id, updates):
        try:
            await self.cursor.execute(
                'UPDATE approvals SET approvals_received =?, status =? WHERE id =?',
                [updates.get("approvals_received"), updates.get("status"), approval_id]
            )
            await self.conn.commit()
            logging.info("Record updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update record: {e}")
            raise

    async def find_row_by_id(self, approval_id):
        try:
            result = await self.cursor.execute('SELECT * FROM approvals WHERE id =?', (approval_id,))
            row = await result.fetchone()
            if row is None:
                return None
            return dict(zip(('id', 'amount', 'expense_item', 'expense_group', 'partner', 'period', 'payment_method',
                             'comment', 'approvals_needed', 'approvals_received', 'status'), row))
        except Exception as e:
            logging.error(f"Failed to fetch record: {e}")
            return None


db = ApprovalDB()

