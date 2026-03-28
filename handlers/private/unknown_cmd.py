from json import loads

from database import db
from aiogram import Router, types
from handlers import filters
from handlers.filters import Private
from handlers.private.users import strs

unk_router = Router()

# --- фильтр, чтобы этот обработчик НЕ срабатывал для обычных пользователей и работал ТОЛЬКО в личных чатах ---
@unk_router.message(Private(), ~filters.IsUser())
async def handle_unknown_non_user_message(message: types.Message):
    # Получаем пользователя, чтобы определить язык и статус
    user = await db.users.get_by_id(user_id=message.from_user.id)
    lang = user.lang if user else 'ru' # Язык по умолчанию 'ru'

    is_manager_or_admin = await filters.IsManagerOrAdmin().__call__(message)
    is_command_or_button = await filters.IsCommandOrMenuButton().__call__(message)

    if is_manager_or_admin and is_command_or_button:
         from utils.logger import bot_logger
         bot_logger.warning(f"Manager/Admin {message.from_user.id} sent known command/button '{message.text}' but it wasn't handled by main routers. Reaching unknown_cmd handler.")
         # Можно вернуть стандартное сообщение об ошибке или просто проигнорировать
#         await message.answer(strs(lang=lang).unk_message)
         return

    # Если это не пользователь и не команда/кнопка от админа/менеджера, отправляем настроенное сообщение о неизвестной команде
    unk_msg_pref = await db.preferences.get_by_key('unk_message')
    unk_value = unk_msg_pref.value if unk_msg_pref else {}
    unk_message_content = unk_value.get('message') if isinstance(unk_value, dict) else None

    if unk_message_content and unk_message_content != strs(lang='ru').unk_message:
        try:
            if isinstance(unk_message_content, str): # Старый формат?
                 unk_message_content = loads(unk_message_content.replace('\'', '"').replace('None', 'null').replace('True', 'true').replace('False', 'false'))

            if isinstance(unk_message_content, dict): # Ожидаемый формат Message
                await types.Message(**unk_message_content).send_copy(chat_id=message.chat.id).as_(message.bot)
            else: # Иначе просто текст
                await message.answer(str(unk_message_content))
        except Exception as e:
            from utils.logger import bot_logger
            bot_logger.error(f"Error sending custom unknown command message: {e}. Content: {unk_message_content}")
            await message.answer(strs(lang=lang).unk_message) # Отправляем дефолтное в случае ошибки
    else:
        await message.answer(strs(lang=lang).unk_message) # Отправляем дефолтное