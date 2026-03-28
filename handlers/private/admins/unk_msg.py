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
unk_msg_router = Router()

# Ключи для хранения временных сообщений в БД
TEMP_UNK_MESSAGE_KEY = 'temp_unk_message'


# __states__ !DO NOT DELETE!
class UnkMsgStates(StatesGroup):
    get_msg = State()
    get_link = State()


# __callbacks__
class UnkMsgCallback(CallbackData, prefix='unk_msg'):
    action: str  # "save", "add_link", "remove_keyboard"


# __buttons__ !DO NOT DELETE!
async def get_unk_msg_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру управления сообщением."""
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).admin_save_btn, callback_data=UnkMsgCallback(action='save').pack())],
        [InlineKeyboardButton(text=strs(lang=lang).admin_add_link_btn,
                              callback_data=UnkMsgCallback(action='add_link').pack())],
        [InlineKeyboardButton(text=strs(lang=lang).admin_remove_keyboard_btn,
                              callback_data=UnkMsgCallback(action='remove_keyboard').pack())]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)


# __chat__ !DO NOT DELETE!
@unk_msg_router.message(
    filters.Private(),
    filters.IsAdmin(),
    (F.text == '/unk_msg') | F.text.in_(unk_msg_btn)
)
async def handle_unk_msg_command(message: Message, state: FSMContext):
    """
    Начало процесса изменения сообщения для неизвестной команды.
    Показывает текущее сообщение и просит прислать новое.
    """
    bot_logger.info(f'Handling command /unk_msg from user {message.chat.id}')
    await state.clear()
    lang = (await state.get_data()).get('lang', 'ru')

    await message.answer(text=strs(lang=lang).admin_unk_current)

    # Показываем текущее сообщение
    unk_info = await db.preferences.get_by_key('unk_message')
    unk_message_content = unk_info.value.get('message') if unk_info and isinstance(unk_info.value, dict) else None

    if unk_message_content and unk_message_content != strs(lang='ru').unk_message:
        try:
            await Message(**unk_message_content).send_copy(chat_id=message.chat.id).as_(message.bot)
        except Exception as e:
            bot_logger.error(f"Error sending current unknown command message: {e}. Content: {unk_message_content}")
            await message.answer(strs(lang='ru').unk_message)
    else:
        await message.answer(strs(lang='ru').unk_message)

    # Просим прислать новое
    await message.answer(text=strs(lang=lang).admin_unk_ask_msg,
                         reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(UnkMsgStates.get_msg.state)


@unk_msg_router.message(UnkMsgStates.get_msg)
async def handle_get_msg_state(message: Message, state: FSMContext):
    """
    Получает новое сообщение, сохраняет его во временную запись в БД
    и отправляет превью с кнопками управления.
    """
    bot_logger.info(f'Handling state UnkMsgStates.get_msg from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    # Сохраняем сообщение во временную запись
    message_content = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
    await db.preferences.set_value(TEMP_UNK_MESSAGE_KEY, {'message': message_content})

    # Отправляем превью
    preview_message = await message.send_copy(chat_id=message.chat.id)
    control_keyboard = await get_unk_msg_keyboard(lang=lang)
    control_message = await message.answer(text=strs(lang=lang).admin_what_to_do_with_message,
                                           reply_markup=control_keyboard)

    # Сохраняем ID сообщений для последующего редактирования/удаления
    await state.update_data(preview_message_id=preview_message.message_id,
                            control_message_id=control_message.message_id)
    await state.set_state()  # Выходим из состояния ожидания сообщения


@unk_msg_router.callback_query(UnkMsgCallback.filter(F.action == 'add_link'))
async def handle_add_link_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на 'Добавить кнопку-ссылку', запрашивает данные для кнопки."""
    bot_logger.info(f'Handling "add_link" callback for unk_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(text=strs(lang=lang).admin_ask_link_text,
                                  reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(UnkMsgStates.get_link.state)
    await callback.answer()


@unk_msg_router.message(UnkMsgStates.get_link)
async def handle_get_link_state(message: Message, state: FSMContext):
    """
    Получает текст и ссылку, добавляет кнопку к временному сообщению,
    обновляет превью.
    """
    bot_logger.info(f'Handling state UnkMsgStates.get_link for unk_msg from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()
    preview_message_id = data.get('preview_message_id')

    # Валидация формата "текст - ссылка"
    if '-' not in message.text:
        await message.answer(text=strs(lang=lang).admin_invalid_link_format)
        return

    text, url = map(str.strip, message.text.split('-', 1))
    if not text or not url:
        await message.answer(text=strs(lang=lang).admin_invalid_link_format)
        return

    # Валидация URL
    if not (url.startswith('http://') or url.startswith('https://')):
        url = 'https://' + url

    try:
        # Пробуем создать кнопку, чтобы aiogram проверил URL
        test_button = InlineKeyboardButton(text=text, url=url)
    except (TelegramBadRequest, ValueError) as e:
        bot_logger.warning(f"Invalid URL provided by user {message.chat.id}: {url}. Error: {e}")
        await message.answer(strs(lang=lang).admin_invalid_link_format)
        return

    # Достаем временное сообщение
    temp_pref = await db.preferences.get_by_key(TEMP_UNK_MESSAGE_KEY)
    msg_data = temp_pref.value.get('message', {})

    # Добавляем кнопку
    current_markup_dict = msg_data.get('reply_markup')
    if current_markup_dict and isinstance(current_markup_dict.get('inline_keyboard'), list):
        current_markup = InlineKeyboardMarkup.model_validate(current_markup_dict)
        current_markup.inline_keyboard.append([test_button])
        msg_data['reply_markup'] = current_markup.model_dump()
    else:
        new_markup = InlineKeyboardMarkup(inline_keyboard=[[test_button]])
        msg_data['reply_markup'] = new_markup.model_dump()

    # Обновляем временную запись
    await db.preferences.set_value(TEMP_UNK_MESSAGE_KEY, {'message': msg_data})

    # Обновляем превью
    if preview_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=preview_message_id,
                reply_markup=InlineKeyboardMarkup.model_validate(msg_data['reply_markup'])
            )
        except TelegramBadRequest as e:
            if "message is not modified" in e.message:
                bot_logger.warning("Tried to edit unk_msg preview with the same markup. Ignoring.")
                pass
            else:
                raise

    await message.answer(text=strs(lang=lang).admin_link_added)
    await state.set_state()  # Выходим из состояния ожидания ссылки


@unk_msg_router.callback_query(UnkMsgCallback.filter(F.action == 'remove_keyboard'))
async def handle_remove_keyboard_callback(callback: CallbackQuery, state: FSMContext):
    """Удаляет всю клавиатуру из временного сообщения и обновляет превью."""
    bot_logger.info(f'Handling "remove_keyboard" callback for unk_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()
    preview_message_id = data.get('preview_message_id')

    # Обновляем временное сообщение
    temp_pref = await db.preferences.get_by_key(TEMP_UNK_MESSAGE_KEY)
    msg_data = temp_pref.value.get('message', {})

    # Проверяем, есть ли что удалять
    if msg_data.get('reply_markup') is None:
        await callback.answer("У кнопок уже нет.", show_alert=True)
        return

    msg_data['reply_markup'] = None
    await db.preferences.set_value(TEMP_UNK_MESSAGE_KEY, {'message': msg_data})

    # Обновляем превью
    if preview_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=preview_message_id,
                reply_markup=None
            )
        except TelegramBadRequest as e:
            if "message is not modified" in e.message:
                bot_logger.warning("Tried to remove markup from unk_msg preview, but it was already gone. Ignoring.")
                pass
            else:
                raise

    await callback.answer(strs(lang=lang).admin_keyboard_removed, show_alert=True)


@unk_msg_router.callback_query(UnkMsgCallback.filter(F.action == 'save'))
async def handle_save_callback(callback: CallbackQuery, state: FSMContext):
    """
    Сохраняет сообщение из временной записи в постоянную.
    Удаляет временные сообщения и выходит из процесса.
    """
    bot_logger.info(f'Handling "save" callback for unk_msg from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()

    # Получаем финальное сообщение из временной записи
    temp_pref = await db.preferences.get_by_key(TEMP_UNK_MESSAGE_KEY)
    if not temp_pref or not temp_pref.value.get('message'):
        await callback.answer("Ошибка: не удалось найти сообщение для сохранения.", show_alert=True)
        return

    final_message_content = temp_pref.value

    # Сохраняем в постоянную запись
    await db.preferences.set_value('unk_message', final_message_content)

    # Удаляем временные сообщения и клавиатуру
    await db.preferences.delete_by_key(TEMP_UNK_MESSAGE_KEY)
    if data.get('preview_message_id'):
        await bot.delete_message(callback.message.chat.id, data.get('preview_message_id'))
    if data.get('control_message_id'):
        await bot.delete_message(callback.message.chat.id, data.get('control_message_id'))

    await callback.message.answer(text=strs(lang=lang).admin_unk_message_saved,
                                  reply_markup=await get_main_menu(lang=lang, user_id=callback.from_user.id))
    await state.clear()
    await callback.answer()