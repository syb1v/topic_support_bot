from . import *

# Project
from database import db
from utils.logger import bot_logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from translations import strs
from bot import bot

# __router__ !DO NOT DELETE!
channel_router = Router()


async def get_channel_info_menu_inline_keyboard(lang: str, user_id: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой подписки и проверки."""
    channel_info_pref = await db.preferences.get_by_key(key='channel_info')

    if not channel_info_pref or not isinstance(channel_info_pref.value, dict):
        bot_logger.error(f"Неверный формат channel_info в БД.")
        return InlineKeyboardMarkup(inline_keyboard=[])

    channel_url = channel_info_pref.value.get('url', '#')
    button_name = channel_info_pref.value.get('button_name', 'Подписаться')

    button_list = [
        [InlineKeyboardButton(text=button_name, url=channel_url)],
        [InlineKeyboardButton(text=strs(lang=lang).check_subscription_btn, callback_data=f'channel_subscribed_btn')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)


@channel_router.callback_query(F.data == 'channel_subscribed_btn')
async def handle_channel_subscribed_button_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает кнопку 'Проверить подписку'."""
    user_id = callback.from_user.id
    user = await db.users.get_by_id(user_id)
    lang = user.lang if user else 'ru'

    channel_info_pref = await db.preferences.get_by_key('channel_info')
    if not channel_info_pref or not isinstance(channel_info_pref.value, dict) or not channel_info_pref.value.get('id'):
        await callback.answer("Ошибка: Канал для проверки не настроен.", show_alert=True)
        return

    channel_id = channel_info_pref.value['id']
    is_on = channel_info_pref.value.get('is_on', False)

    if not is_on:
        await callback.message.delete()
        await callback.message.answer(text=strs(lang=lang).channel_subscribed)
        await callback.answer()
        return

    try:
        member_status = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member_status.status in ['creator', 'administrator', 'member', 'restricted']:
            await callback.message.delete()
            await callback.message.answer(text=strs(lang=lang).channel_subscribed)
        else:
            await callback.answer(text=strs(lang=lang).channel_unsubscribed, show_alert=True)
    except Exception as e:
        bot_logger.error(f"Ошибка при повторной проверке подписки для {user_id}: {e}")
        await callback.answer(text=strs(lang=lang).channel_unsubscribed, show_alert=True)