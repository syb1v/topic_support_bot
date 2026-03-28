from . import *
from database import db
from database.models import UserModel
from utils.logger import bot_logger
import config as cf

# Standard
from datetime import datetime, timezone, timedelta
from json import loads

# Project
from handlers.utils import get_main_menu
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# __router__ !DO NOT DELETE!
general_router = Router()


# __states__ !DO NOT DELETE!


# __buttons__ !DO NOT DELETE!
async def get_menu_reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру с основными действиями для пользователя."""
    button_list = [
        [KeyboardButton(text=strs(lang=lang).create_ticket_btn)], # Написать менеджеру
        [KeyboardButton(text=strs(lang=lang).faq_btn)],          # FAQ
        [KeyboardButton(text=strs(lang=lang).choose_lang_btn)]   # Eng / Рус
    ]
    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)


async def get_choose_lang_inline_keyboard() -> InlineKeyboardMarkup:
    """Возвращает Inline клавиатуру для выбора языка."""
    button_list = [
        [InlineKeyboardButton(text='🇷🇺 Русский', callback_data='lang_btn ru'),
         InlineKeyboardButton(text='🇺🇸 English', callback_data='lang_btn en')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)


# --- Обработчик для смены языка (callback от inline кнопок) ---
@general_router.callback_query(F.data.startswith('lang_btn'))
async def handle_lang_button_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие кнопки выбора языка, обновляет БД и state, отправляет новое меню."""
    bot_logger.info(f'Handling language change button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    if len(data) < 2:
        await callback.answer("Error: Invalid language data.", show_alert=True)
        return
    new_lang = data[1]
    if new_lang not in ['ru', 'en']:
        await callback.answer(f"Error: Unsupported language code '{new_lang}'.", show_alert=True)
        return

    user = await db.users.get_by_id(user_id=callback.message.chat.id)
    if not user:
        await callback.answer("Error: User not found.", show_alert=True)
        bot_logger.error(f"User {callback.message.chat.id} not found during language change.")
        return
    if user.lang == new_lang:
        await callback.answer(); return # Ничего не делаем

    # Обновляем БД и state
    user.lang = new_lang
    await db.users.update(user=user)
    await state.update_data(lang=new_lang)
    bot_logger.info(f"User {user.id} language updated to '{new_lang}' in DB and state.")

    # Получаем и отправляем новое меню
    keyboard = await get_main_menu(lang=new_lang, user_id=user.id)
    await callback.message.answer(text=strs(new_lang).language_updated, reply_markup=keyboard)
    try: await callback.message.delete() # Пытаемся удалить старое сообщение
    except Exception as e: bot_logger.warning(f"Could not delete lang selection msg for user {user.id}: {e}")
    await callback.answer()


# __chat__ !DO NOT DELETE!
@general_router.message(Command('start'), filters.Private())
async def handle_start_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /start from user {message.chat.id}')
    await state.clear()
    user = await db.users.get_by_id(user_id=message.chat.id)
    user_lang = 'ru'

    if not user:
        status = 'user'; name = message.from_user.full_name; uname = message.from_user.username
        if message.chat.id in cf.admin_ids: status = 'admin'
        user = UserModel(
            id=message.chat.id, registration_date=datetime.now(timezone(timedelta(hours=3))),
            tg_name=name, url_name=uname.lower() if uname else "", status=status, lang=user_lang
        )
        await db.users.insert(user=user)
        bot_logger.info(f"Created new user {user.id} via /start with lang 'ru'")
    else:
        user_lang = user.lang

    await state.update_data({'lang': user_lang})
    keyboard = await get_main_menu(lang=user_lang, user_id=user.id)
    start_info = await db.preferences.get_by_key('start_message')
    start_msg_content = start_info.value.get('message') if start_info and isinstance(start_info.value, dict) else None

    # Проверка на кастомное сообщение
    if start_msg_content and start_msg_content != strs(lang='ru').general_start:
        try:
            if isinstance(start_msg_content, str):
                 start_msg_content = loads(start_msg_content.replace('\'', '"').replace('None', 'null').replace('True', 'true').replace('False', 'false'))

            if isinstance(start_msg_content, dict):
                 message_to_send = Message(**start_msg_content)
                 # Отправляем кастомное сообщение с его собственной inline-клавиатурой
                 await message_to_send.send_copy(chat_id=message.chat.id).as_(message.bot)
                 # Отдельно отправляем сообщение, чтобы показать reply-клавиатуру главного меню
                 await message.answer(text=strs(user_lang).use_help, reply_markup=keyboard)
            else:
                 await message.answer(text=str(start_msg_content), reply_markup=keyboard)
        except Exception as e:
             bot_logger.error(f"Error sending custom start message: {e}. Content: {start_msg_content}", exc_info=True)
             # Откат к стандартному сообщению
             await message.answer(text=strs(lang=user_lang).general_start, reply_markup=keyboard)
    else:
        # Стандартное поведение
         await message.answer(text=strs(lang=user_lang).general_start, reply_markup=keyboard)


@general_router.message(Command('help'), filters.Private())
async def handle_help_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /help from user {message.chat.id}')
    await state.clear()
    user = await db.users.get_by_id(user_id=message.chat.id)
    if not user: # Создаем, если нет
        status = 'user'; name = message.from_user.full_name; uname = message.from_user.username
        if message.chat.id in cf.admin_ids: status = 'admin'
        user = UserModel(
            id=message.chat.id, registration_date=datetime.now(timezone(timedelta(hours=3))),
            tg_name=name, url_name=uname.lower() if uname else "", status=status, lang='ru'
        )
        await db.users.insert(user=user)
        bot_logger.info(f"Created new user {user.id} via /help with lang 'ru'")

    await state.update_data({'lang': user.lang})
    keyboard = await get_main_menu(lang=user.lang, user_id=user.id)
    help_text = ""
    if user.status == 'admin': help_text = strs(user.lang).admin_general_help
    elif user.status == 'manager': help_text = strs(user.lang).manager_general_help
    else: help_text = strs(user.lang).general_help
    await message.answer(text=help_text, reply_markup=keyboard)


@general_router.message(
    filters.Private(),
    (F.text == '/lang') | (F.text.in_(choose_lang_btn))
)
async def handle_lang_command(message: Message, state: FSMContext):
    """Отправляет сообщение с кнопками выбора языка."""
    bot_logger.info(f'Handling command /lang or button from user {message.chat.id}')
    user = await db.users.get_by_id(user_id=message.chat.id)
    current_lang = user.lang if user else 'ru'
    await state.update_data({'lang': current_lang})
    await message.answer(
        text=strs(lang=current_lang).general_lang,
        reply_markup=await get_choose_lang_inline_keyboard()
        )