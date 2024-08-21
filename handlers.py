import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from db import db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DEPARTMENT_HEAD_CHAT_ID = [594336984]
FINANCE_CHAT_IDS = [594336984]


async def chat_ids_department(department):
    chat_ids = {
        "head": DEPARTMENT_HEAD_CHAT_ID,
        "finance": FINANCE_CHAT_IDS,
        "all": DEPARTMENT_HEAD_CHAT_ID + FINANCE_CHAT_IDS
    }
    return chat_ids[department]


async def start_command(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Добро пожаловать! Используйте /submit_record для отправки запроса на платеж.')
    await db.create_table()


async def submit_record_command(update: Update, context: CallbackContext) -> None:
    """
    Обработчик введённого пользователем платежа в соответствии с паттерном:
    1)Сумма: положительное число (возможно с плавающей точкой)
    2)Статья расхода: любая строка из букв и цифр
    3)Группа расхода: любая строка из букв и цифр
    4)Партнёр: любая строка из букв и цифр
    5)Дата: две даты через пробел; дата оплаты и дата начисления платежа
    6)Форма оплаты: любая строка из букв и цифр
    7)Комментарий к платежу: любая строка из букв и цифр
    Добавление платежа в базу данных 'approvals';
    Отправление данных о платеже для одобрения главой отдела.
    """
    pattern = (r'^(\d*\.?\d+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*(\d{2}\.\d{2}\.\d{4}\s\d{2}\.\d{2}\.\d{4}),\s*([^,'
               r']+),\s*([^,]+)$')
    message = ' '.join(context.args)
    match = re.match(pattern, message)
    if not match:
        await update.message.reply_text('Неверный формат аргументов. Пожалуйста, следуйте указанному формату.')
        return

    record_dict = {
        "amount": match.group(1),
        "expense_item": match.group(2),
        "expense_group": match.group(3),
        "partner": match.group(4),
        "period": match.group(5),
        "payment_method": match.group(6),
        "comment": match.group(7)
    }

    async with db:
        approval_id = await db.insert_record(record_dict)
        await create_and_send_approval_message(approval_id, record_dict, "head", context=context)


async def reject_record_command(update: Update, context: CallbackContext) -> None:
    """
    Меняет в базе данных статус платежа на отклонён('Rejected')
     и отправляет сообщение об отменее ранее одобренного платежа.
    """
    row_id = context.args
    async with db:
        await db.update_row_by_id(row_id, {"status": "Rejected"})
    await send_message_to_chats(await chat_ids_department("all"),
                                f"Заявка {row_id} отклонена.", context)


async def create_and_send_approval_message(approval_id, record, department, context=None):
    """Создание кнопок "Одобрить" и "Отклонить", создание и отправка сообщения для одобрения заявки."""
    keyboard = [
        [InlineKeyboardButton("Одобрить", callback_data=f"{department}_approve_{approval_id}")],
        [InlineKeyboardButton("Отклонить", callback_data=f"{department}_reject_{approval_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_text = f'Пожалуйста, одобрите запрос на платеж {approval_id}: сумма: {record["amount"]}, ' \
                   f'статья: {record["expense_item"]}, группа: {record["expense_group"]}, ' \
                   f'партнер: {record["partner"]}, ' \
                   f'период начисления: {record["period"]}, форма оплаты: {record["payment_method"]}, ' \
                   f'комментарий: {record["comment"]}'

    chat_ids = await chat_ids_department(department)
    await send_message_to_chats(chat_ids, message_text, context, reply_markup)


async def send_message_to_chats(chat_ids, text, context, reply_markup=None):
    """Отправка сообщения в выбранные телеграм-чаты."""
    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def process_approval(update: Update, context: CallbackContext) -> None:
    """
    Обработчик нажатий пользователем кнопок "Одобрить" или "Отклонить."
    """
    try:
        response_list = update.callback_query.data.split("_")
        department, action = response_list[:2]
        approval_id = response_list[2]
        async with db as db_instance:
            record = await db_instance.find_row_by_id(approval_id)
        if not record:
            await update.message.reply_text('Запись не найдена.')
            return
    except Exception as e:
        raise e
    await handle_head_approval(context, approval_id, record, department, action, update=update)


async def handle_head_approval(context, approval_id, record, department, action, update: Update) -> None:
    """Обработчик заявок для одобрения или отклонения."""
    if action == "reject":
        await reject_payment(context, approval_id, department)

    elif action == "approve":
        await approve_payment(context, approval_id, record, department, update=update)


async def reject_payment(context, approval_id, department):
    """Отправка сообщения об отклонении платежа; изменение количество апрувов в базе данных."""
    if department == "finance":
        async with db:
            await db.update_row_by_id(approval_id, {"approvals_received": 1, "status": "Rejected"})
        await send_message_to_chats(await chat_ids_department("all"),
                                    f"Заявка {approval_id} отклонена.", context)
    else:
        async with db:
            await db.update_row_by_id(approval_id, {"approvals_received": 0, "status": "Rejected"})
        await send_message_to_chats(await chat_ids_department(department),
                                    f"Заявка {approval_id} отклонена.", context)


async def approve_payment(context, approval_id, record, department, update: Update):
    """
    Функция выполняет одну из трёх команд в зависимости от входных данных:
    1)отправка сообщения в финансовый отдел на согласование платежа, если платёж более 50000, меняет количество апрувов
     и статус платежа;
    2)отправка сообщения об одобрении платежа для главы департамента, если платёж менее 50000, меняет количество
     апрувов и статус платежа;
    3)отправка сообщения об одобрении платежа для финансового отдела, меняет количество апрувов и статус платежа.
    """
    if department == "head":
        if float(record["amount"]) >= 50000:
            async with db:
                await db.update_row_by_id(approval_id, {"approvals_received": 1, "status": "Pending"})
            await create_and_send_approval_message(approval_id, record, "finance", context=context)
        else:
            async with db:
                await db.update_row_by_id(approval_id, {"approvals_received": 1, "status": "Approved"})
            await update.callback_query.message.reply_text('Запрос на платеж одобрен и готов к оплате.')

    elif department == "finance":
        async with db:
            await db.update_row_by_id(approval_id, {"approvals_received": 2, "status": "Approved"})
        await update.callback_query.message.reply_text('Запрос на платеж одобрен и готов к оплате.')


async def error_callback(update: Update, context: CallbackContext) -> None:
    """Обработчик ошибок для логирования и уведомления пользователя."""
    logger = logging.getLogger(__name__)
    logger.exception('Произошла ошибка:')
    if update:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Произошла ошибка. Попробуйте снова позже.")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об ошибке: {e}")
