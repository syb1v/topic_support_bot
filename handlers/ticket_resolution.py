from datetime import datetime, timedelta, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

import config as cf
from database import db, TicketModel, UserModel
from translations import strs
from handlers.utils import get_main_menu
from utils.logger import bot_logger


resolution_router = Router()


def now_moscow() -> datetime:
    return datetime.now(timezone(timedelta(hours=3)))


def get_resolution_keyboard(lang: str, ticket_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=strs(lang).ticket_resolution_close_btn,
            callback_data=f'ticket_resolution_close:{ticket_id}',
        )],
        [InlineKeyboardButton(
            text=strs(lang).ticket_resolution_continue_btn,
            callback_data=f'ticket_resolution_continue:{ticket_id}',
        )],
    ])


async def send_resolution_prompt(bot: Bot, ticket: TicketModel) -> bool:
    ticket = await db.tickets.get_by_id(ticket.id)
    if not ticket or ticket.close_date:
        return False
    user = await db.users.get_by_id(ticket.user_id)
    if not user:
        return False
    if ticket.resolution_prompt_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=user.id,
                message_id=ticket.resolution_prompt_message_id,
                reply_markup=None,
            )
        except TelegramAPIError:
            pass
    try:
        sent_message = await bot.send_message(
            chat_id=user.id,
            text=strs(user.lang).ticket_resolution_prompt,
            reply_markup=get_resolution_keyboard(user.lang, ticket.id),
        )
    except TelegramAPIError as error:
        bot_logger.error(f'Failed to send resolution prompt for Ticket {ticket.id}: {error}')
        return False
    ticket.resolution_prompt_sent_at = now_moscow()
    ticket.resolution_prompt_message_id = sent_message.message_id
    await db.tickets.update(ticket)
    return True


async def record_user_activity(bot: Bot, ticket: TicketModel) -> None:
    if ticket.resolution_prompt_message_id:
        try:
            await bot.edit_message_reply_markup(
                chat_id=ticket.user_id,
                message_id=ticket.resolution_prompt_message_id,
                reply_markup=None,
            )
        except TelegramAPIError:
            pass
    activity_time = now_moscow()
    ticket.last_user_activity = activity_time
    ticket.last_modified = activity_time
    ticket.resolution_prompt_sent_at = None
    ticket.resolution_prompt_message_id = None
    await db.tickets.update(ticket)


async def close_ticket_by_user(bot: Bot, ticket: TicketModel, user: UserModel) -> bool:
    ticket = await db.tickets.get_by_id(ticket.id)
    if not ticket or ticket.close_date:
        return False
    current_date = now_moscow()
    original_topic_id = ticket.topic_id
    ticket.close_date = current_date
    ticket.last_modified = current_date
    ticket.manager_id = None
    ticket.topic_id = None
    ticket.resolution_prompt_message_id = None
    await db.tickets.update(ticket)
    user.current_ticket_id = None
    user.current_topic_id = None
    await db.users.update(user)
    if original_topic_id and cf.GROUP_CHAT_ID:
        try:
            user_name = user.tg_name or f'ID: {user.id}'
            await bot.send_message(
                cf.GROUP_CHAT_ID,
                f'❗️ Пользователь ({user_name}) завершил обращение #{ticket.id}.',
                message_thread_id=original_topic_id,
            )
            await bot.close_forum_topic(cf.GROUP_CHAT_ID, original_topic_id)
        except TelegramAPIError as error:
            bot_logger.error(f'Failed to close Topic {original_topic_id}: {error}')
    return True


@resolution_router.callback_query(F.data.startswith('ticket_resolution_close:'))
async def handle_resolution_close(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.rsplit(':', 1)[1])
    ticket = await db.tickets.get_by_id(ticket_id)
    user = await db.users.get_by_id(callback.from_user.id)
    if not ticket or not user or ticket.user_id != user.id or ticket.close_date:
        await callback.answer('Обращение уже закрыто', show_alert=True)
        return
    if not await close_ticket_by_user(callback.bot, ticket, user):
        await callback.answer('Не удалось закрыть обращение', show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        strs(user.lang).ticket_closed_by_user,
        reply_markup=await get_main_menu(lang=user.lang, user_id=user.id),
    )
    await callback.answer()


@resolution_router.callback_query(F.data.startswith('ticket_resolution_continue:'))
async def handle_resolution_continue(callback: CallbackQuery) -> None:
    ticket_id = int(callback.data.rsplit(':', 1)[1])
    ticket = await db.tickets.get_by_id(ticket_id)
    user = await db.users.get_by_id(callback.from_user.id)
    if not ticket or not user or ticket.user_id != user.id or ticket.close_date:
        await callback.answer('Обращение уже закрыто', show_alert=True)
        return
    await record_user_activity(callback.bot, ticket)
    await callback.message.answer(
        strs(user.lang).ticket_resolution_continue_message,
        reply_markup=ReplyKeyboardRemove(),
    )
    await callback.answer()


@resolution_router.message(Command('bye'))
async def handle_manual_resolution_prompt(message: Message) -> None:
    actor = await db.users.get_by_id(message.from_user.id)
    is_configured_admin = message.from_user.id in cf.admin_ids
    has_staff_role = actor is not None and actor.status in {'manager', 'admin'}
    if not is_configured_admin and not has_staff_role:
        await message.answer('Команда доступна только менеджерам и администраторам.')
        return
    if message.chat.type != 'private' and message.chat.id != cf.GROUP_CHAT_ID:
        await message.answer('Команда /bye работает только в группе поддержки или в личном чате с ботом.')
        return
    command_parts = (message.text or '').split(maxsplit=1)
    ticket = None
    if len(command_parts) == 2 and command_parts[1].strip().isdigit():
        ticket = await db.tickets.get_by_id(int(command_parts[1].strip()))
    elif message.message_thread_id:
        ticket = await db.tickets.get_by_topic_id(message.message_thread_id)
    if not ticket or ticket.close_date:
        await message.answer('Укажите открытое обращение: /bye <ticket_id>')
        return
    if await send_resolution_prompt(message.bot, ticket):
        await message.answer(f'Предложение отправлено пользователю по обращению #{ticket.id}.')
    else:
        await message.answer(f'Не удалось отправить предложение по обращению #{ticket.id}.')
