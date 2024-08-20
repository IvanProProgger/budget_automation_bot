import aiosqlite
import aiofiles
import logging
import os

logging.basicConfig(level=logging.INFO)


class ApprovalDB:
    def __init__(self):
        self.conn = None
        self.cursor = None

    async def _ensure_connected(self):
        """Подключается к базе данных, если соединение еще не установлено."""
        base_dir = "./"
        db_file_path = os.path.join(base_dir, "approvals.db")

        # Проверяем, существует ли директория базы данных
        if not os.path.exists(base_dir):
            await aiofiles.os.makedirs(base_dir)

        # Проверяем, существует ли файл базы данных
        if not os.path.isfile(db_file_path):
            # Создаем новую базу данных, если файл не существует
            await aiosqlite.connect(db_file_path)

        if self.conn is None or not self.conn.closed:
            self.conn = await aiosqlite.connect(db_file_path)
            self.cursor = await self.conn.cursor()
            logging.info("Connected to database.")

    async def _ensure_cursor(self):
        """Устанавливает курсор, если он еще не установлен."""
        if self.cursor is None:
            await self._ensure_connected()

    async def connect(self):
        """Открывает соединение с базой данных."""
        await self._ensure_connected()

    async def disconnect(self):
        """Закрывает соединение с базой данных."""
        if self.conn is not None:
            await self.conn.close()
            logging.info("Disconnected from database.")

    async def insert_record(self, record):
        await self._ensure_cursor()
        approvals_needed_value = 1 if float(record["amount"]) < 50000 else 2
        record["approvals_needed"] = approvals_needed_value
        record["approvals_received"] = 0
        record["status"] = "Created"
        try:
            await self.cursor.execute(
                'INSERT INTO approvals (amount, expense_item, expense_group, partner, period, payment_method, comment, '
                'approvals_needed, approvals_received, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                list(record.values())
            )
            await self.conn.commit()
            logging.info("Record inserted successfully.")
            # Удаляем await перед self.cursor.lastrowid, так как это не корутина
            return self.cursor.lastrowid
        except Exception as e:
            logging.error(f"Failed to insert record: {e}")
            raise

    async def update_record(self, approval_id, updates):
        await self._ensure_cursor()
        try:
            await self.cursor.execute(
                'UPDATE approvals SET approvals_received = ?, status = ? WHERE id = ?',
                [updates.get("approvals_received"), updates.get("status"), approval_id]
            )
            await self.conn.commit()
            logging.info("Record updated successfully.")
        except Exception as e:
            logging.error(f"Failed to update record: {e}")
            raise

    async def find_by_id(self, approval_id):
        await self._ensure_cursor()
        try:
            result = await self.cursor.execute('SELECT * FROM approvals WHERE id = ?', (approval_id,))
            row = await result.fetchone()
            if row is None:
                return None
            # Преобразование кортежа в словарь
            return dict(zip(('id', 'amount', 'expense_item', 'expense_group', 'partner', 'period', 'payment_method',
                             'comment', 'approvals_needed', 'approvals_received', 'status'), row))
        except Exception as e:
            logging.error(f"Failed to fetch record: {e}")
            return None


# Создание экземпляра ApprovalDB
db = ApprovalDB()
