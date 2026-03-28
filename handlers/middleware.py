# Third-party
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
import traceback

# Project
from bot import bot
import config as cf
from utils.logger import bot_logger
from translations import strs
from database import db, UserModel
from .private.users.channel import get_channel_info_menu_inline_keyboard


class InsertUserIfNotExistMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_info = data.get('event_from_user')
        if not user_info:
            bot_logger.warning("Middleware: Не удалось получить event_from_user")
            return await handler(event, data)

        user_id = user_info.id
        full_name = user_info.full_name
        user_name = user_info.username
        user = await db.users.get_by_id(user_id=user_id)

        if not user:
            status = 'user'
            if user_id in cf.admin_ids: status = 'admin'
            user_lang = 'ru'

            user_to_insert = UserModel()
            user_to_insert.id = user_id
            user_to_insert.registration_date = datetime.now(timezone(timedelta(hours=3)))
            user_to_insert.tg_name = full_name
            user_to_insert.url_name = user_name.lower() if user_name else ""
            user_to_insert.status = status
            user_to_insert.lang = user_lang
            await db.users.insert(user=user_to_insert)
            bot_logger.info(f"Middleware: Добавлен новый пользователь: ID={user_id}, Lang={user_lang}")

        elif user.tg_name != full_name or (user_name and user.url_name != user_name.lower()):
            user.tg_name = full_name
            if user_name: user.url_name = user_name.lower()
            await db.users.update(user=user)
            bot_logger.info(f'Middleware: Обновлены данные пользователя {user_id}')

        return await handler(event, data)


class LanguageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_info = data.get('event_from_user')
        state = data.get('state')
        user_lang = 'ru'

        if user_info:
            user = await db.users.get_by_id(user_id=user_info.id)
            if user:
                user_lang = user.lang
        elif state:
            state_data = await state.get_data()
            user_lang = state_data.get('lang', 'ru')

        if state:
            await state.update_data({'lang': user_lang})

        return await handler(event, data)


class ChannelSubscriptionCheckMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_info = data.get('event_from_user')
        if not user_info:
            return await handler(event, data)

        user_id = user_info.id
        user = await db.users.get_by_id(user_id)

        # Пропускаем администраторов и менеджеров
        if user and user.status in ['admin', 'manager']:
            return await handler(event, data)

        channel_info_pref = await db.preferences.get_by_key('channel_info')
        if not channel_info_pref or not isinstance(channel_info_pref.value, dict):
            return await handler(event, data)

        channel_settings = channel_info_pref.value
        is_on = channel_settings.get('is_on', False)
        if not is_on:
            return await handler(event, data)

        channel_id = channel_settings.get('id')
        if not channel_id:
            return await handler(event, data)

        try:
            member_status = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member_status.status in ['creator', 'administrator', 'member', 'restricted']:
                return await handler(event, data)
        except (TelegramBadRequest, TelegramAPIError) as e:
            bot_logger.error(f"Ошибка API при проверке подписки {user_id} на {channel_id}: {e}")
            return await handler(event, data)
        except Exception as e:
            bot_logger.error(
                f"Непредвиденная ошибка при проверке подписки {user_id} на {channel_id}: {e}\n{traceback.format_exc()}")
            return await handler(event, data)

        # Если пользователь не подписан
        user_lang = user.lang if user else 'ru'
        target_chat_id = None
        if isinstance(event, CallbackQuery):
            if event.message:
                target_chat_id = event.message.chat.id
        elif hasattr(event, 'chat'):
            target_chat_id = event.chat.id

        if target_chat_id:
            keyboard = await get_channel_info_menu_inline_keyboard(user_id=user_id, lang=user_lang)
            await bot.send_message(
                chat_id=target_chat_id,
                text=strs(lang=user_lang).middle_check_channel,
                reply_markup=keyboard
            )
            if isinstance(event, CallbackQuery):
                await event.answer()

        return CancelHandler()