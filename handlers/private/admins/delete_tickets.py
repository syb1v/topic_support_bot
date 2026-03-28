from . import *
import config as cf
from database import db
from utils.logger import bot_logger
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import bot

# __router__ !DO NOT DELETE!
delete_tickets_router = Router()

# ОБРАБОТЧИКИ КОЛБЭКОВ
@delete_tickets_router.callback_query(F.data.startswith('yes_btn'))
async def handle_yes_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling sure_menu yes button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык

    if len(data) < 2:
        bot_logger.error(f"Invalid callback data length for yes_btn: {callback.data}")
        await callback.answer("Ошибка данных.", show_alert=True)
        # Возвращаем к предыдущему меню
        await callback.message.edit_text(
            text=strs(lang=lang).admin_delete,
            reply_markup=await get_delete_menu_inline_keyboard(lang=lang) # Передаем lang
        )
        return

    month_amount = int(data[1])
    count = 0
    # Ищем по дате ОТКРЫТИЯ, а не last_modified для удаления
    tickets = await db.tickets.get_tickets_last_modified_ago(time_ago=month_amount, is_hours=False) # is_hours=False ищет по open_date

    if tickets:
        for ticket in tickets:
            if ticket.topic_id and cf.GROUP_CHAT_ID:
                try:
                    # Используем импортированный bot
                    await bot.delete_forum_topic(chat_id=cf.GROUP_CHAT_ID, message_thread_id=ticket.topic_id)
                    bot_logger.info(f"Topic {ticket.topic_id} for ticket {ticket.id} deleted before ticket deletion.")
                except Exception as e:
                     # Не прерываем удаление тикета, если топик не удалился
                     bot_logger.error(f"Failed to delete topic {ticket.topic_id} before deleting ticket {ticket.id}: {e}")
            await db.tickets.delete(ticket=ticket) # db.tickets.delete теперь удаляет и папку медиа
            count += 1

    # Возвращаемся к основному меню удаления
    await callback.message.edit_text(
        text=strs(lang=lang).admin_delete,
        reply_markup=await get_delete_menu_inline_keyboard(lang=lang) # Передаем lang
    )

    await callback.answer(
        text=strs(lang=lang).admin_delete_tickets(count=count), show_alert=True # Показываем alert
    )

@delete_tickets_router.callback_query(F.data.startswith('no_btn'))
async def handle_no_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling sure_menu no button callback from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык
    # Возвращаемся к основному меню удаления
    await callback.message.edit_text(
        text=strs(lang=lang).admin_delete,
        reply_markup=await get_delete_menu_inline_keyboard(lang=lang) # Передаем lang
    )
    await callback.answer()

@delete_tickets_router.callback_query(F.data.startswith('month_btn'))
async def handle_month_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling delete_menu month button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык

    if len(data) < 2:
        bot_logger.error(f"Invalid callback data length for month_btn: {callback.data}")
        await callback.answer("Ошибка данных.", show_alert=True)
        return

    month_amount = int(data[1])
    count = 0
    # Ищем по дате ОТКРЫТИЯ для удаления
    tickets = await db.tickets.get_tickets_last_modified_ago(time_ago=month_amount, is_hours=False)
    if tickets:
        count = len(tickets) # Сразу получаем количество

    # Показываем подтверждение перед удалением
    await callback.message.edit_text(
        text=strs(lang=lang).admin_delete_sure.format(count),
        reply_markup=await get_sure_menu_inline_keyboard(month_amount=month_amount, lang=lang) # Передаем lang
    )
    await callback.answer() # Отвечаем на нажатие кнопки

# __buttons__ !DO NOT DELETE!
async def get_sure_menu_inline_keyboard(month_amount: int, lang: str) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).yes, callback_data=f'yes_btn {month_amount}'),
         InlineKeyboardButton(text=strs(lang=lang).no, callback_data='no_btn')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_delete_menu_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    # ИСПРАВЛЕНА ИНИЦИАЛИЗАЦИЯ СПИСКА
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).month_btn_1, callback_data='month_btn 1'),
         InlineKeyboardButton(text=strs(lang=lang).month_btn_3, callback_data='month_btn 3')],
        [InlineKeyboardButton(text=strs(lang=lang).month_btn_6, callback_data='month_btn 6'),
         InlineKeyboardButton(text=strs(lang=lang).month_btn_12, callback_data='month_btn 12')],
        [InlineKeyboardButton(text=strs(lang=lang).delete_btn, callback_data='delete_btn')] # Кнопка закрытия меню
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!

# Обработчик для кнопки
@delete_tickets_router.message(
    filters.Private(), filters.IsAdmin(),
    F.text.in_(delete_tickets_btn)
)
async def handle_delete_tickets_button(message: Message, state: FSMContext):
    """Обрабатывает кнопку удаления старых тикетов."""
    await handle_delete_tickets_command(message, state)

# Обработчик для команды
@delete_tickets_router.message(
    filters.Private(), filters.IsAdmin(),
    Command('delete_tickets')
)
async def handle_delete_tickets_command(message: Message, state: FSMContext):
    """Обрабатывает команду удаления старых тикетов."""
    bot_logger.info(f'Handling /delete_tickets or button from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык

    await message.answer(
        text=strs(lang=lang).admin_delete,
        reply_markup=await get_delete_menu_inline_keyboard(lang=lang)
    )