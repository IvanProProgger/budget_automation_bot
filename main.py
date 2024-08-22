from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN
from handlers import (start_command, submit_record_command, error_callback, reject_record_command,
                      show_not_processed, process_pay, process_approval)


def main() -> None:
    """Основная функция для запуска бота."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("submit_record", submit_record_command))
    application.add_handler(CommandHandler("reject_record", reject_record_command))
    application.add_handler(CommandHandler('show_not_processed', show_not_processed))
    application.add_handler(CallbackQueryHandler(process_pay, pattern='^pay_.*'))
    application.add_handler(CallbackQueryHandler(process_approval, pattern='^approval_.*'))
    application.add_error_handler(error_callback)
    application.run_polling()


if __name__ == "__main__":
    main()
