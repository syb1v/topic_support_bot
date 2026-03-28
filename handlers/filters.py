# Third-party
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_type import ChatType

# Project
from database import db
# --- ИЗМЕНЕНИЕ: Импортируем commands и reply_buttons ---
from translations import strs, commands, reply_buttons
import config as cf
from datetime import datetime, timezone, timedelta # Добавлен импорт для IsRestricted

# --- Фильтры статусов ---
class IsUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        if not user: return True # Считаем незарегистрированного пользователем
        return user.status == 'user' and message.from_user.id not in cf.admin_ids

class IsManagerOrAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        if not user: return False
        return user.status in ['manager', 'admin']

class IsManager(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        return user and user.status == 'manager' and message.from_user.id not in cf.admin_ids

class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        return user and user.status == 'admin' and message.from_user.id in cf.admin_ids

# --- Фильтр активного обращения ---
class InTicket(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        """Проверяет, находится ли пользователь в активном тикете (имеет current_topic_id)."""
        user = await db.users.get_by_id(user_id=message.from_user.id)
        # --- ИЗМЕНЕНИЕ: Используем новый фильтр IsCommandOrMenuButton для проверки ---
        is_command_or_button = await IsCommandOrMenuButton().__call__(message)

        if user and user.current_topic_id:
            # Проверяем, что тикет действительно активен (на всякий случай)
            ticket = await db.tickets.get_by_topic_id(topic_id=user.current_topic_id)
            if ticket and not ticket.close_date:
                 # Сообщение считается "в тикете", если это не команда и не кнопка
                 if not is_command_or_button:
                     return True
        return False

# --- Фильтр ограничений ---
class IsRestricted(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await db.users.get_by_id(user_id=message.from_user.id)
        if not user:
             from utils.logger import bot_logger
             bot_logger.warning(f"User {message.from_user.id} not found in IsRestricted filter. Allowing action.")
             return True

        if user.is_banned:
            await message.answer(text=strs(lang=user.lang).restriction_banned_forever)
            return False

        if user.mute_time:
            mute_time_obj = user.mute_time
            current_time_utc = datetime.now(timezone.utc)

            if isinstance(mute_time_obj, str):
                try:
                    time_str = mute_time_obj.split('.')[0]
                    # Предполагаем UTC, если нет информации о зоне
                    mute_time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                except ValueError:
                    from utils.logger import bot_logger
                    bot_logger.error(f"Could not parse mute_time string '{user.mute_time}' for user {user.id}. Allowing action.")
                    user.mute_time = None # Сбрасываем некорректное время
                    await db.users.update(user=user)
                    return True

            if mute_time_obj and not mute_time_obj.tzinfo:
                 mute_time_obj = mute_time_obj.replace(tzinfo=timezone.utc)

            if mute_time_obj and mute_time_obj > current_time_utc:
                try:
                    msk_tz = timezone(timedelta(hours=3))
                    mute_time_msk = mute_time_obj.astimezone(msk_tz)
                    mute_time_str = mute_time_msk.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    mute_time_str = mute_time_obj.strftime('%Y-%m-%d %H:%M:%S') + " UTC"

                await message.answer(text=strs(lang=user.lang).restriction_before(mute_time_str))
                return False
            elif mute_time_obj and mute_time_obj <= current_time_utc:
                 user.mute_time = None
                 await db.users.update(user=user)
                 return True

        return True

# --- Фильтр состояния FSM ---
class NotInState(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current_state = await state.get_state()
        return current_state is None

# --- Фильтр приватного чата ---
class Private(BaseFilter):
    def __init__(self):
        self.chat_type = ChatType.PRIVATE

    async def __call__(self, message: Message) -> bool:
        return message.chat.type == self.chat_type

# --- Проверка, является ли сообщение командой или кнопкой меню ---
class IsCommandOrMenuButton(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        text = message.text
        if text:
            # Проверяем, начинается ли текст с / (команда)
            if text.startswith('/'):
                # Дополнительно проверяем, есть ли такая команда в нашем списке
                command_part = text.split()[0] # Берем только саму команду
                return command_part in commands
            # Проверяем, совпадает ли текст с одной из кнопок ReplyKeyboard
            if text in reply_buttons:
                return True
        return False