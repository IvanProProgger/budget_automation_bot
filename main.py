from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from config import TELEGRAM_BOT_TOKEN
from conversation import enter_record, input_sum, input_item, input_group, input_partner, input_comment, \
    input_dates, input_payment_type, confirm_command, stop_dialog
from handlers import start_command, submit_record_command, error_callback, reject_record_command, \
    show_not_paid, process_pay, process_approval

import asyncio

from init import db

INPUT_SUM, INPUT_ITEM, INPUT_GROUP, INPUT_PARTNER, INPUT_COMMENT, INPUT_DATES, INPUT_PAYMENT_TYPE, CONFIRM_COMMAND = (
    range(8))


async def main() -> None:
    """Основная функция для запуска бота."""
    async with db:
        await db.create_table()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("submit_record", submit_record_command))
    application.add_handler(CommandHandler("reject_record", reject_record_command))
    application.add_handler(CommandHandler('show_not_paid', show_not_paid))
    application.add_handler(CallbackQueryHandler(process_pay, pattern='^pay_.*'))
    application.add_handler(CallbackQueryHandler(process_approval, pattern='^approval_.*'))
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('enter_record', enter_record)],
        states={
            INPUT_SUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_sum)],
            INPUT_ITEM: [CallbackQueryHandler(input_item)],
            INPUT_GROUP: [CallbackQueryHandler(input_group)],
            INPUT_PARTNER: [CallbackQueryHandler(input_partner)],
            INPUT_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_comment)],
            INPUT_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_dates)],
            INPUT_PAYMENT_TYPE: [CallbackQueryHandler(input_payment_type)],
            CONFIRM_COMMAND: [CallbackQueryHandler(confirm_command)]
        },
        fallbacks=[
            CommandHandler('stop', stop_dialog),
        ],
    )
    application.add_handler(conversation_handler)
    application.add_error_handler(error_callback)
    await application.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
