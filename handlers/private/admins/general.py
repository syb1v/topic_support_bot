from . import *
from database import db
from utils.logger import bot_logger
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from translations import my_tickets_btn
from handlers.private.managers.tickets import handle_manager_archive_button

# __router__ !DO NOT DELETE!
general_router = Router()

# __buttons__ !DO NOT DELETE!
async def get_menu_reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    button_list = [
        [KeyboardButton(text=strs(lang=lang).change_faq_btn),
         KeyboardButton(text=strs(lang=lang).working_hours_btn)],
        [KeyboardButton(text=strs(lang=lang).change_subscription_channel_btn)],
        [KeyboardButton(text=strs(lang=lang).find_user_btn),
         KeyboardButton(text=strs(lang=lang).my_tickets_btn)],
        [KeyboardButton(text=strs(lang=lang).opened_tickets_btn),
         KeyboardButton(text=strs(lang=lang).statistic_btn)],
        [KeyboardButton(text=strs(lang=lang).send_mailing_btn),
         KeyboardButton(text=strs(lang=lang).start_msg_btn)],
        [KeyboardButton(text=strs(lang=lang).delete_tickets_btn),
         KeyboardButton(text=strs(lang=lang).change_unk_message)],
        [KeyboardButton(text=strs(lang=lang).choose_lang_btn)],
        [KeyboardButton(text=strs(lang=lang).change_close_time_btn)],
        [KeyboardButton(text=strs(lang=lang).manager_mode_btn)]
    ]

    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)


@general_router.message(
        filters.Private(), filters.IsAdmin(),
        F.text.in_(statistic_btn)
)
async def statistic_handler(message: Message, state: FSMContext):
    bot_logger.info(f'Handling statistic_handler from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык из state
    tickets_7 = await db.tickets.get_tickets_count_in_period(days_ago=7)
    tickets_30 = await db.tickets.get_tickets_count_in_period(days_ago=30)
    tickets_all = await db.tickets.get_tickets_count_in_period(days_ago=None)

    users_7 = await db.users.get_users_regs_in_period(days_ago=7)
    users_30 = await db.users.get_users_regs_in_period(days_ago=30)
    users_all = await db.users.get_users_regs_in_period(days_ago=None)

    time_close_30 = await db.tickets.get_medium_closing_time_in_period(ticket_id=None, days_ago=30)
    time_close_all = await db.tickets.get_medium_closing_time_in_period(ticket_id=None, days_ago=None)

    await message.answer(text=strs(lang=lang).statistic_composition.format(
                                                                            users_7, users_30, users_all,
                                                                            tickets_7, tickets_30, tickets_all,
                                                                            time_close_30['hours'], time_close_30['mins'],
                                                                            time_close_all['hours'], time_close_all['mins']
                                                                            ))

@general_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/to_manager') | (F.text.in_(manager_mode_btn)))
)
async def handle_to_manager_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /to_manager from user {message.chat.id}')

    user = await db.users.get_by_id(user_id=message.chat.id)
    if not user: return

    lang = (await state.get_data()).get('lang', user.lang)
    user.status = 'manager'
    await db.users.update(user=user)

    from ..managers.general import get_menu_reply_keyboard
    await message.answer(text=strs(lang=lang).admin_general_now_manager,
                         reply_markup=await get_menu_reply_keyboard(user_id=message.chat.id, lang=lang))

@general_router.message(
    filters.Private(), filters.IsAdmin(),
    F.text.in_(my_tickets_btn)
)
async def handle_my_tickets_button_admin(message: Message, state: FSMContext):
    """ Обрабатывает кнопку 'Мои обращения' для админа, показывая архив """
    bot_logger.info(f'Handling my_tickets_btn button from admin {message.chat.id}')
    # Вызываем общую функцию показа архива из обработчиков менеджера
    await handle_manager_archive_button(message, state)