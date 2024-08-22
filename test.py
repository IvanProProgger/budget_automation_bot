from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler, CallbackContext

from config import TELEGRAM_BOT_TOKEN

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Опция 1", callback_data='1'),
            InlineKeyboardButton("Опция 2", callback_data='2'),
        ],
        [InlineKeyboardButton("Опция 3", callback_data='3')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Пожалуйста, выберите:', reply_markup=reply_markup)


async def input_field(update: Update, context: CallbackContext) -> None:
    keyboard = [['Введите текст']]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    await update.message.reply_text('Пожалуйста, введите текст:', reply_markup=reply_markup)


async def text_handler(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    await update.message.reply_text(f'Вы ввели: {text}')


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    await query.answer()

    await query.edit_message_text(text=f"Выбрана опция: {query.data}")


def main() -> None:
    """Основная функция для запуска бота."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('input', input_field))
    application.add_handler(MessageHandler(filters.ALL, text_handler))
    application.run_polling()


if __name__ == "__main__":
    main()
