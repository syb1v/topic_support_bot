from . import *
from database import db
from utils.logger import bot_logger
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from handlers.utils import CustomJSONEncoder, get_decline_reply_keyboard, get_main_menu
from json import loads, dumps
from aiogram.exceptions import TelegramBadRequest
from bot import bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# __router__ !DO NOT DELETE!
start_msg_router = Router()

# Ключи для хранения временных сообщений в БД
TEMP_START_MESSAGE_KEY = 'temp_start_message'

# __states__ !DO NOT DELETE!
class StartMsgStates(StatesGroup):
    get_msg = State()
    get_link = State()

# __callbacks__
class StartMsgCallback(CallbackData, prefix='start_msg'):
    action: str  # "save", "add_link", "remove_keyboard"

# __buttons__ !DO NOT DELETE!
async def get_start_msg_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру управления сообщением."""
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).admin_save_btn,
                              callback_data=StartMsgCallback(action='save').pack())],
        [InlineKeyboardButton(text=strs(lang=lang).admin_add_link_btn,
                              callback_data=StartMsgCallback(action='add_link').pack())],
        [InlineKeyboardButton(text=strs(lang=lang).admin_remove_keyboard_btn,
                              callback_data=StartMsgCallback(action='remove_keyboard').pack())]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)

# __chat__ !DO NOT DELETE!
@start_msg_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/start_msg') | F.text.in_(start_msg_btn))
)
async def handle_start_msg_command(message: Message, state: FSMContext):
    """
    Начало процесса изменения стартового сообщения.
    Показывает текущее сообщение и просит прислать новое.
    """
    bot_logger.info(f'Handling command /start_msg from user {message.chat.id}')
    await state.clear()
    lang = (await state.get_data()).get('lang', 'ru')

    await message.answer(text=strs(lang=lang).admin_start_current)

    # Показываем текущее сообщение
    start_info = await db.preferences.get_by_key('start_message')
    start_message_content = start_info.value.get('message') if start_info and isinstance(start_info.value,
                                                                                         dict) else None

    if start_message_content and start_message_content != strs(lang='ru').general_start:
        try:
            await Message(**start_message_content).send_copy(chat_id=message.chat.id).as_(message.bot)
        except Exception as e:
            bot_logger.error(f"Error sending current start message: {e}. Content: {start_message_content}")
            await message.answer(text=strs(lang='ru').general_start)
    else:
        await message.answer(text=strs(lang='ru').general_start)

    # Просим прислать новое
    await message.answer(text=strs(lang=lang).admin_start_ask_msg,
                         reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(StartMsgStates.get_msg.state)


@start_msg_router.message(StartMsgStates.get_msg)
async def handle_get_msg_state(message: Message, state: FSMContext):
    """
    Получает новое сообщение, сохраняет его во временную запись в БД
    и отправляет превью с кнопками управления.
    """
    bot_logger.info(f'Handling state StartMsgStates.get_msg from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    message_content = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    await db.preferences.set_value(TEMP_START_MESSAGE_KEY, {'message': message_content})

    preview_message = await message.send_copy(chat_id=message.chat.id)
    control_keyboard = await get_start_msg_keyboard(lang=lang)
    control_message = await message.answer(text=strs(lang=lang).admin_what_to_do_with_message,
                                           reply_markup=control_keyboard)

    await state.update_data(preview_message_id=preview_message.message_id,
                            control_message_id=control_message.message_id)
    await state.set_state()


@start_msg_router.callback_query(StartMsgCallback.filter(F.action == 'add_link'))
async def handle_add_link_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на 'Добавить кнопку-ссылку', запрашивает данные для кнопки."""
    bot_logger.info(f'Handling "add_link" callback for start_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(text=strs(lang=lang).admin_ask_link_text,
                                  reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(StartMsgStates.get_link.state)
    await callback.answer()


@start_msg_router.message(StartMsgStates.get_link)
async def handle_get_link_state(message: Message, state: FSMContext):
    """
    Получает текст и ссылку, добавляет кнопку к временному сообщению,
    обновляет превью.
    """
    bot_logger.info(f'Handling state StartMsgStates.get_link for start_msg from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()
    preview_message_id = data.get('preview_message_id')

    if '-' not in message.text:
        await message.answer(text=strs(lang=lang).admin_invalid_link_format)
        return

    text, url = map(str.strip, message.text.split('-', 1))
    if not text or not url:
        await message.answer(text=strs(lang=lang).admin_invalid_link_format)
        return

    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url

    try:
        test_button = InlineKeyboardButton(text=text, url=url)
    except (TelegramBadRequest, ValueError) as e:
        bot_logger.warning(f"Invalid URL provided by user {message.chat.id}: {url}. Error: {e}")
        await message.answer(strs(lang=lang).admin_invalid_link_format)
        return

    temp_pref = await db.preferences.get_by_key(TEMP_START_MESSAGE_KEY)
    msg_data = temp_pref.value.get('message', {})

    current_markup_dict = msg_data.get('reply_markup')
    if current_markup_dict and isinstance(current_markup_dict.get('inline_keyboard'), list):
        current_markup = InlineKeyboardMarkup.model_validate(current_markup_dict)
        current_markup.inline_keyboard.append([test_button])
        msg_data['reply_markup'] = current_markup.model_dump()
    else:
        new_markup = InlineKeyboardMarkup(inline_keyboard=[[test_button]])
        msg_data['reply_markup'] = new_markup.model_dump()

    await db.preferences.set_value(TEMP_START_MESSAGE_KEY, {'message': msg_data})

    if preview_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=preview_message_id,
                reply_markup=InlineKeyboardMarkup.model_validate(msg_data['reply_markup'])
            )
        except TelegramBadRequest as e:
            if "message is not modified" in e.message:
                bot_logger.warning("Tried to edit start_msg preview with the same markup. Ignoring.")
                pass
            else:
                raise

    await message.answer(text=strs(lang=lang).admin_link_added)
    await state.set_state()


@start_msg_router.callback_query(StartMsgCallback.filter(F.action == 'remove_keyboard'))
async def handle_remove_keyboard_callback(callback: CallbackQuery, state: FSMContext):
    """Удаляет всю клавиатуру из временного сообщения и обновляет превью."""
    bot_logger.info(f'Handling "remove_keyboard" callback for start_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()
    preview_message_id = data.get('preview_message_id')

    temp_pref = await db.preferences.get_by_key(TEMP_START_MESSAGE_KEY)
    msg_data = temp_pref.value.get('message', {})

    if msg_data.get('reply_markup') is None:
        await callback.answer("У кнопок уже нет.", show_alert=True)
        return

    msg_data['reply_markup'] = None
    await db.preferences.set_value(TEMP_START_MESSAGE_KEY, {'message': msg_data})

    if preview_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=preview_message_id,
                reply_markup=None
            )
        except TelegramBadRequest as e:
            if "message is not modified" in e.message:
                bot_logger.warning("Tried to remove markup from start_msg preview, but it was already gone. Ignoring.")
                pass
            else:
                raise

    await callback.answer(strs(lang=lang).admin_keyboard_removed, show_alert=True)


@start_msg_router.callback_query(StartMsgCallback.filter(F.action == 'save'))
async def handle_save_callback(callback: CallbackQuery, state: FSMContext):
    """
    Сохраняет сообщение из временной записи в постоянную.
    Удаляет временные сообщения и выходит из процесса.
    """
    bot_logger.info(f'Handling "save" callback for start_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()

    temp_pref = await db.preferences.get_by_key(TEMP_START_MESSAGE_KEY)
    if not temp_pref or not temp_pref.value.get('message'):
        await callback.answer("Ошибка: не удалось найти сообщение для сохранения.", show_alert=True)
        return

    final_message_content = temp_pref.value

    await db.preferences.set_value('start_message', final_message_content)

    await db.preferences.delete_by_key(TEMP_START_MESSAGE_KEY)
    if data.get('preview_message_id'):
        await bot.delete_message(callback.message.chat.id, data.get('preview_message_id'))
    if data.get('control_message_id'):
        await bot.delete_message(callback.message.chat.id, data.get('control_message_id'))

    await callback.message.answer(text=strs(lang=lang).admin_start_message_saved,
                                  reply_markup=await get_main_menu(lang=lang, user_id=callback.from_user.id))
    await state.clear()
    await callback.answer()