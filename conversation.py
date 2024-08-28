from telegram import Update, ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes, CallbackContext

import logging
import re


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


INPUT_SUM, INPUT_ITEM, INPUT_GROUP, INPUT_PARTNER, INPUT_COMMENT, INPUT_DATES, INPUT_PAYMENT_TYPE, CONFIRM_COMMAND = (
    range(8))

items = [
    "Организация мероприятий", "Рекламные кампании", "Digital кампании", "Спонсорство и партнерство",
    "PR и работа со СМИ", "Продакшн", "Стратегические проекты", "Мерчендайзинг и подарки", "Административные расходы",
    "CRM Маркетинг"
]

groups = ['ASO', 'ODDS', 'SCORES24', 'AppsFlyer', 'Sports.ru', 'Legal Bet', 'Ставка ТВ', 'AlfaLeads',
          'Clicklead', 'Прочие CPA', 'Uffiliates', 'Метарейтинг', 'СМС рассылки', 'Программатик',
          'Shutterstock', 'Getty Images', 'IT-агентство', 'Командировки', 'vprognoze.ru', 'Гео-таргетинг',
          'Yellow Images', 'Appska_in_app', 'SERM (Отзывы)', 'БЛ Мероприятия', 'Спорт Экспресс',
          'Советский Спорт', 'Щетилов верстка', 'Digital фриланс', 'Иные проекты РБ', 'SEO tennisi.bet',
          'Блогеры Telegram', 'Push уведомления', 'Услуги фотографа', 'Голосовые роботы', 'Текстовые роботы',
          'Выплаты по акциям', 'Контент-маркетинг', 'Uffiliates_in_app', 'Яндекс Директ РСЯ',
          'Рейтинг букмекеров', 'Youtube production', 'ThinkMobile_in_app', 'Монтаж видео и аудио',
          'Отзывы и комментарии', 'Организация розыгрыша', 'Статистические ролики', 'Ставка ТВ кэшбек-герои',
          'Фанатик текущие проекты', 'Торпедо_BTL-мероприятия', 'ODDS кэтфиш кэшбек-герои',
          'Потенциальные амбассадоры', 'Торпедо_Выплаты по акциям', '2гис (4 месяца до ноября)',
          'Реклама в социальных сетях', 'Торпедо_Производство мерча', 'Анимационный ролик 15 секунд',
          'Иллюстрации и дизайн проекты', 'Торпедо_Организация фотосъемок', 'BHT исследование здоровья бренда',
          'Торпедо_Создание дизайн-проектов', 'Белый договор по CPA - mobupps.com',
          'Торпедо_Реализация спонсорских прав', 'Торпедо_Создание аудио и видео контента',
          'Заказ промо одежды и сувенирной продукции', 'Закупка оборудования и программного обеспечения',
          'Управленческие расходы (такси, доставка, курьеры)',
          'Торпедо_Производство рекламных материалов (в т.ч. наградная продукция)'
          ]

partners = ['РК', 'нет', 'Сами', 'Alfa', '2Gis', 'Manna', 'Чужой', 'Gudai', '3Snet', 'наш ВК', 'Маслов',
            'Гасилин', 'Odds.ru', 'наш инст', 'Legalbet', 'ODNAZHDY', 'Skantrup', 'Вагабонди', 'Sports.ru',
            'Stavka.tv', 'IT Agency', 'Pavlovsky', 'Shee.team', 'Winrating', 'FCTorpedo', 'Чернявский',
            'Телингатер', 'Freebet.ru', 'наш твиттер', 'Betonmobile', 'Overbetting', 'Метарейтинг',
            'mobupps.com', 'наш телеграм', 'AznarDnevnik', 'PremierLeads', 'Максим Фролов', 'DnevnikFanata',
            'Юрий Кузьмичев', 'Артур Бегларян', 'Карен Арутюнян', 'AndreyShipovki', 'Михаил Борзыкин',
            'Советский спорт', 'DmitryKuznetsov', 'Богдан Тимошенко', 'Денис Фломастеров', 'FilippKudryavtsev',
            'Александр Шевченко'
            ]

payment_types = [
    'Наличные', 'Безналичные', 'Криптовалюта'
]


def create_keyboard(massive):
    keyboard = []
    current_row_list = []
    last_elem_index = len(massive)
    for number, item in enumerate(massive):
        button = InlineKeyboardButton(item, callback_data=number)
        current_row_list.append(button)
        max_length = len(' '.join([str(b.text) for b in current_row_list]))

        if max_length >= 28 or number == last_elem_index - 1:
            keyboard.append(current_row_list)
            current_row_list = []
    return keyboard


async def enter_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога. Ввод суммы"""
    await update.message.reply_text(
        'Введите сумму:',
        reply_markup=ForceReply(selective=True),
    )
    return INPUT_SUM


async def input_sum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода суммы и выбор категории."""
    user_sum = update.message.text
    pattern = r'^[0-9]+(?:\.[0-9]+)?$'
    if not re.fullmatch(pattern, user_sum):
        await update.message.reply_text("Некорректная сумма. Попробуйте ещё раз.")
        return ConversationHandler.END
    context.user_data['sum'] = user_sum
    await update.message.reply_text(f"Вы ввели сумму: {user_sum}")

    keyboard = create_keyboard(items)
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Выберите статью расхода:', reply_markup=reply_markup)
    return INPUT_ITEM


async def input_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора категории."""
    query = update.callback_query
    await query.answer()
    item_value = items[int(query.data)]
    context.user_data['item'] = item_value
    await query.edit_message_text(f"Вы ввели статью расхода: {item_value}")

    keyboard = create_keyboard(groups)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text('Выберите группу расхода:', reply_markup=reply_markup)
    return INPUT_GROUP


async def input_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка выбора группы расходов."""
    query = update.callback_query
    await query.answer()
    group_value = groups[int(query.data)]

    context.user_data['group'] = group_value
    await query.edit_message_text(f"Вы ввели группу расхода: {group_value}")

    keyboard = create_keyboard(partners)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text('Выберите партнёра:', reply_markup=reply_markup)
    return INPUT_PARTNER


async def input_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    partner = partners[int(query.data)]
    context.user_data['partner'] = partner
    await query.edit_message_text(f"Вы ввели партнёра: {partner}")
    await query.message.reply_text(
        'Введите комментарий для отчёта:',
        reply_markup=ForceReply(selective=True),
    )
    return INPUT_COMMENT


async def input_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_comment = update.message.text
    context.user_data['comment'] = user_comment
    await update.message.reply_text(f"Вы ввели комментарий: {user_comment}")
    await update.message.reply_text(
        'Введите даты начисления через пробел:',
        reply_markup=ForceReply(selective=True),
    )
    return INPUT_DATES


async def input_dates(update: Update, context: ContextTypes) -> int:
    user_dates = update.message.text
    context.user_data['dates'] = user_dates
    await update.message.reply_text(f"Вы ввели даты: {user_dates}")

    keyboard = create_keyboard(payment_types)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите тип оплаты:', reply_markup=reply_markup)
    return INPUT_PAYMENT_TYPE


async def input_payment_type(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    payment_type = payment_types[int(query.data)]

    context.user_data['payment_type'] = payment_type
    await query.edit_message_text(f'Вы ввели тип платежа: {payment_type}')
    final_command = (f"{context.user_data['sum']}, {context.user_data['item']}, "
                     f"{context.user_data['group']}, {context.user_data['partner']}, {context.user_data['comment']}, "
                     f"{context.user_data['dates']}, {context.user_data['payment_type']}")
    context.user_data['final_command'] = final_command
    buttons = [
        [InlineKeyboardButton("Подтвердить", callback_data="Подтвердить")],
        [InlineKeyboardButton("Отмена", callback_data="Отмена")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.reply_text(
        text=f"Полученная информация о счёте:\n1)Сумма: {context.user_data['sum']}\n"
             f"2)Статья: {context.user_data['item']}\n3)Группа: {context.user_data['group']}\n"
             f"4)Партнёр: {context.user_data['partner']}\n5)Комментарий: {context.user_data['comment']}\n"
             f"6)Даты начисления: {context.user_data['dates']}\n"
             f"7)Форма оплаты: {context.user_data['payment_type']}\nПроверьте правильность введённых данных!",
        reply_markup=reply_markup
    )
    return CONFIRM_COMMAND


async def confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка подтверждения команды."""
    query = update.callback_query
    await query.answer()
    if query.data == "Подтвердить":
        final_command = context.user_data.get('final_command', '')
        if final_command:
            await context.bot.send_message(chat_id=query.message.chat_id, text=f"/submit_record {final_command}")
        await query.edit_message_text(text="Информация о счёте готова к отправке. Скопируйте данное сообщение и "
                                           "пришлите в чат")
    elif query.data == "Отмена":
        await query.edit_message_text(text="Отмена операции.")
    return ConversationHandler.END


async def stop_dialog(update: Update, context: CallbackContext) -> int:
    """Обработчик команды /stop"""
    await context.bot.edit_message_text('Диалог прерван.', reply_markup=None)
    # await update.message.reply_text('Диалог прерван.')
    # message = update.effective_message
    # logger.info(message)
    # if message and message.reply_to_message and message.reply_to_message.reply_markup:
    #     await message.edit_reply_markup(reply_markup=None)
    #
    # return ConversationHandler.END
