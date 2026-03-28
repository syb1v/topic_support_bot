import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from json import loads
from datetime import datetime, timezone, timedelta

import config as cf
from database import db, UserModel, TicketModel
from handlers.utils import make_up_user_info, get_main_menu
from utils.logger import bot_logger
from translations import strs
from aiogram.fsm.context import FSMContext
from handlers.private.managers.restrictions import MuteStates

topics_router = Router()


async def get_topic_menu_keyboard(lang: str, ticket: TicketModel, user: UserModel) -> InlineKeyboardMarkup:
    button_list = []
    ticket_id = ticket.id
    user_id = user.id

    button_list.append(
        [InlineKeyboardButton(text=strs(lang).topic_user_info_button,
                              callback_data=f"topic_userinfo_{user_id}_{ticket_id}")]
    )

    if not user.is_banned:
        current_time_utc = datetime.now(timezone.utc)
        # Убедимся, что mute_time - это aware datetime object
        is_muted = False
        if user.mute_time:
            mute_time_aware = user.mute_time
            if not mute_time_aware.tzinfo:
                mute_time_aware = mute_time_aware.replace(tzinfo=timezone.utc)
            if mute_time_aware > current_time_utc:
                is_muted = True

        if not is_muted:
            button_list.append(
                [InlineKeyboardButton(text=strs(lang).mute_btn,
                                      callback_data=f"topic_mute_{user_id}_{ticket_id}")]
            )

    if user.is_banned:
        button_list.append(
            [InlineKeyboardButton(text=strs(lang).unban_btn,
                                  callback_data=f"topic_unban_{user_id}_{ticket_id}")]
        )
    else:
        button_list.append(
            [InlineKeyboardButton(text=strs(lang).ban_btn,
                                  callback_data=f"topic_ban_{user_id}_{ticket_id}")]
        )

    if ticket.close_date:
        button_list.append(
            [InlineKeyboardButton(text=strs(lang).topic_reopen_button,
                                  callback_data=f"topic_reopen_{ticket_id}")]
        )
    else:
        button_list.append(
            [InlineKeyboardButton(text=strs(lang).topic_close_button,
                                  callback_data=f"topic_close_{ticket_id}")]
        )
    button_list.append([InlineKeyboardButton(text=strs(lang).delete_btn, callback_data="delete_btn")])
    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def close_ticket_logic(bot: Bot, ticket: TicketModel, manager_user_id: int) -> tuple[bool, str]:
    """
    Оптимизированная логика закрытия тикета.
    Возвращает: (Успех, Сообщение о результате)
    """
    # 1. Проверяем, не закрыт ли тикет в базе данных.
    if ticket.close_date:
        bot_logger.info(f"Attempt to close already closed ticket #{ticket.id}. Ensuring topic is closed.")
        # Дополнительно убедимся, что топик в телеграме закрыт.
        if ticket.topic_id and cf.GROUP_CHAT_ID:
            try:
                await bot.close_forum_topic(chat_id=cf.GROUP_CHAT_ID, message_thread_id=ticket.topic_id)
            except TelegramAPIError as e:
                # Игнорируем ошибку, если топик уже закрыт. Логируем другие ошибки.
                if 'topic is closed' not in str(e).lower() and 'TOPIC_NOT_MODIFIED' not in str(e).upper():
                    bot_logger.error(
                        f"Error ensuring topic {ticket.topic_id} is closed for already closed ticket {ticket.id}: {e}")
        return False, strs(lang='ru').ticket_already_closed

    # 2. Обновляем данные в БД.
    current_date = datetime.now(timezone(timedelta(hours=3)))
    original_topic_id = ticket.topic_id

    ticket.close_date = current_date
    ticket.last_modified = current_date
    ticket.topic_id = None  # Очищаем topic_id у тикета в БД
    ticket.manager_id = manager_user_id
    await db.tickets.update(ticket=ticket)

    # 3. Обновляем данные пользователя.
    user = await db.users.get_by_id(user_id=ticket.user_id)
    if user:
        user.current_ticket_id = None
        user.current_topic_id = None
        await db.users.update(user=user)
        try:
            user_main_menu = await get_main_menu(lang=user.lang, user_id=user.id)
            await bot.send_message(
                chat_id=user.id,
                text=strs(lang=user.lang).ticket_closed_by_manager,
                reply_markup=user_main_menu
            )
        except TelegramAPIError as e:
            bot_logger.error(f"Failed to send ticket closure notification to user {user.id}: {e}")

    # 4. Формируем сообщение о результате и закрываем топик в Telegram.
    result_message = strs(lang='ru').ticket_closed_in_db_msg.format(ticket.id, original_topic_id or "N/A")

    if original_topic_id and cf.GROUP_CHAT_ID:
        try:
            await bot.close_forum_topic(chat_id=cf.GROUP_CHAT_ID, message_thread_id=original_topic_id)
            result_message += "\n" + strs(lang='ru').topic_closed_msg
            bot_logger.info(f"Ticket {ticket.id} and Topic {original_topic_id} closed by Manager {manager_user_id}")
        except TelegramAPIError as e:
            # Если топик уже закрыт - это не ошибка. Логируем остальные.
            if 'topic is closed' not in str(e).lower() and 'TOPIC_NOT_MODIFIED' not in str(e).upper():
                error_message = f"Error closing forum topic {original_topic_id} for ticket {ticket.id}: {e}"
                bot_logger.error(error_message)
                result_message += f"\n❌ {error_message}"
            else:
                bot_logger.info(
                    f"Topic {original_topic_id} was already closed when trying to close ticket {ticket.id}.")
                result_message += "\n" + strs(lang='ru').topic_closed_msg  # Все равно сообщаем об успехе
    elif not original_topic_id:
        bot_logger.warning(f"Cannot close forum topic for ticket {ticket.id}: topic_id was not set.")

    return True, result_message


@topics_router.message(F.chat.id == cf.GROUP_CHAT_ID, F.message_thread_id.is_not(None), Command(commands=["close"]))
async def handle_close_command(message: Message):
    topic_id = message.message_thread_id
    manager_user_id = message.from_user.id
    bot_logger.info(f"Handling /close command from Manager {manager_user_id} in Topic {topic_id}")

    ticket = await db.tickets.get_by_topic_id(topic_id=topic_id)
    if not ticket:
        await message.reply(strs(lang='ru').ticket_not_found_for_topic)
        return

    _, result_text = await close_ticket_logic(bot=message.bot, ticket=ticket, manager_user_id=manager_user_id)
    await message.reply(result_text)


@topics_router.message(F.chat.id == cf.GROUP_CHAT_ID, F.message_thread_id.is_not(None), Command(commands=["menu"]))
async def handle_menu_command(message: Message):
    topic_id = message.message_thread_id
    manager_user_id = message.from_user.id
    bot_logger.info(f"Handling /menu command from Manager {manager_user_id} in Topic {topic_id}")

    ticket = await db.tickets.get_by_topic_id(topic_id=topic_id)
    if not ticket:
        await message.reply(strs(lang='ru').ticket_not_found_for_topic)
        return

    user = await db.users.get_by_id(user_id=ticket.user_id)
    if not user:
        await message.reply(f"User (ID: {ticket.user_id}) associated with ticket not found.")
        return

    keyboard = await get_topic_menu_keyboard(lang='ru', ticket=ticket, user=user)
    ticket_status_str = strs(lang='ru').ticket_closed if ticket.close_date else strs(lang='ru').ticket_active
    await message.reply(f"Ticket Menu #{ticket.id} (Status: {ticket_status_str}):", reply_markup=keyboard)


@topics_router.message(F.chat.id == cf.GROUP_CHAT_ID, F.message_thread_id.is_not(None), F.text.startswith('/'))
async def handle_unknown_topic_command(message: Message):
    # Убедимся, что это не /close или /menu, которые уже обработаны
    if message.text.lower().strip() not in ['/close', '/menu']:
        await message.reply(strs(lang='ru').topic_invalid_command)


async def get_back_to_menu_keyboard(lang: str, ticket_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=strs(lang).back_btn,
                              callback_data=f"topic_back_to_menu_{ticket_id}_{user_id}")]
    ])


@topics_router.callback_query(F.data.startswith("topic_userinfo_"))
async def handle_topic_userinfo_callback(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        ticket_id = int(parts[3])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_userinfo: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    bot_logger.info(f"Handling topic_userinfo callback for User {user_id} from Manager {callback.from_user.id}")
    user = await db.users.get_by_id(user_id=user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    _, info_text = await make_up_user_info(user=user, lang='ru')
    back_keyboard = await get_back_to_menu_keyboard(lang='ru', ticket_id=ticket_id, user_id=user_id)

    try:
        await callback.message.edit_text(text=info_text, reply_markup=back_keyboard)
    except TelegramAPIError as e:
        if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Error editing message for user info: {e}")
    await callback.answer()


@topics_router.callback_query(F.data.startswith("topic_back_to_menu_"))
async def handle_topic_back_to_menu_callback(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        ticket_id = int(parts[4])
        user_id = int(parts[5])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_back_to_menu: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    bot_logger.info(f"Handling topic_back_to_menu callback for Ticket {ticket_id} from Manager {callback.from_user.id}")
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    user = await db.users.get_by_id(user_id=user_id)

    if not ticket or not user:
        await callback.answer("Error: Cannot retrieve ticket or user data.", show_alert=True)
        try:
            await callback.message.delete()
        except:
            pass
        return

    keyboard = await get_topic_menu_keyboard(lang='ru', ticket=ticket, user=user)
    ticket_status_str = strs(lang='ru').ticket_closed if ticket.close_date else strs(lang='ru').ticket_active
    menu_text = f"Ticket Menu #{ticket.id} (Status: {ticket_status_str}):"
    try:
        await callback.message.edit_text(text=menu_text, reply_markup=keyboard)
    except TelegramAPIError as e:
        if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Error editing message for back_to_menu: {e}")
    await callback.answer()


@topics_router.callback_query(F.data.startswith("topic_mute_"))
async def handle_topic_mute_callback(callback: CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split("_")
        user_id = int(parts[2])
        ticket_id_str = parts[3]
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_mute: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    bot_logger.info(
        f"Handling topic_mute callback for User {user_id} from Manager {callback.from_user.id} (Ticket: {ticket_id_str})")
    user = await db.users.get_by_id(user_id=user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    current_time_utc = datetime.now(timezone.utc)
    is_muted = False
    if user.mute_time:
        mute_time_aware = user.mute_time
        if not mute_time_aware.tzinfo:
            mute_time_aware = mute_time_aware.replace(tzinfo=timezone.utc)
        if mute_time_aware > current_time_utc:
            is_muted = True

    if is_muted:
        await callback.answer("User is already restricted.", show_alert=True)
        return

    await state.set_state(MuteStates.get_mute_time)
    await state.update_data({
        'user_id': user_id,
        'ticket_id': ticket_id_str if ticket_id_str.isdigit() else None,
        'source': 'topic',
        'topic_id': callback.message.message_thread_id,
        'topic_message_id': callback.message.message_id,
        'lang': 'ru'
    })

    try:
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            message_thread_id=callback.message.message_thread_id,
            text=strs(lang='ru').ticket_get_mute
        )
        await callback.message.delete()
    except TelegramAPIError as e:
        bot_logger.error(f"Error sending mute prompt in Topic {callback.message.message_thread_id}: {e}")
        await callback.answer("Error: Could not send mute prompt.", show_alert=True)
        await state.clear()
    await callback.answer()


@topics_router.callback_query(F.data.startswith(("topic_ban_", "topic_unban_")))
async def handle_topic_ban_unban_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    try:
        user_id = int(callback.data.split("_")[2])
        ticket_id = int(callback.data.split("_")[3])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_ban/unban: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    bot_logger.info(
        f"Handling topic_{action} callback for User {user_id} from Manager {callback.from_user.id} for Ticket {ticket_id}")
    user = await db.users.get_by_id(user_id=user_id)
    if not user:
        await callback.answer("User not found.", show_alert=True)
        return

    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if not ticket:
        await callback.answer("Ticket not found.", show_alert=True)
        return

    response_text = ""
    # original_text = callback.message.text.split("\n\n✅")[0]

    if action == "ban":
        if user.is_banned:
            await callback.answer("User is already banned.", show_alert=True)
            return
        user.is_banned = True
        response_text = strs(lang='ru').restriction_banned_successfully
        if not ticket.close_date:
            await close_ticket_logic(bot=callback.bot, ticket=ticket, manager_user_id=callback.from_user.id)
        try:
            await callback.bot.send_message(user_id, text=strs(lang=user.lang).restriction_banned_forever)
        except TelegramAPIError as e:
            bot_logger.error(f"Failed to notify User {user_id} about ban: {e}")
    elif action == "unban":
        if not user.is_banned:
            await callback.answer("User is not banned.", show_alert=True)
            return
        user.is_banned = False
        response_text = strs(lang='ru').restriction_unbanned_successfully
        try:
            await callback.bot.send_message(user_id, text=strs(lang=user.lang).restriction_unbanned)
        except TelegramAPIError as e:
            bot_logger.error(f"Failed to notify User {user_id} about unban: {e}")

    await db.users.update(user=user)

    try:
        updated_ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        new_keyboard = await get_topic_menu_keyboard(lang='ru', ticket=updated_ticket or ticket, user=user)
        ticket_status_str = strs(lang='ru').ticket_closed if (updated_ticket and updated_ticket.close_date) else strs(
            lang='ru').ticket_active

        await callback.message.edit_text(
            text=f"Ticket Menu #{ticket.id} (Status: {ticket_status_str})\n\n✅ {response_text}",
            reply_markup=new_keyboard
        )
    except TelegramAPIError as e:
        if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Error updating topic menu after {action}: {e}")
            await callback.message.answer(f"✅ {response_text}")
    await callback.answer(response_text)


@topics_router.callback_query(F.data.startswith("topic_close_"))
async def handle_topic_close_callback(callback: CallbackQuery):
    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_close: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    manager_user_id = callback.from_user.id
    bot_logger.info(f"Handling topic_close callback for Ticket {ticket_id} from Manager {manager_user_id}")
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if not ticket:
        await callback.answer(strs(lang='ru').ticket_not_found, show_alert=True)
        return

    success, result_text = await close_ticket_logic(bot=callback.bot, ticket=ticket, manager_user_id=manager_user_id)

    if success:
        try:
            await callback.message.edit_text(
                text=f"Ticket Menu #{ticket_id} (Status: {strs(lang='ru').ticket_closed})\n\n{result_text}",
                reply_markup=None
            )
        except TelegramAPIError as e:
            if "message is not modified" not in str(e).lower():
                bot_logger.error(f"Error editing topic menu message after close: {e}")
                await callback.message.answer(result_text)
        await callback.answer("Request closed successfully.")
    else:
        await callback.answer(result_text, show_alert=True)


@topics_router.callback_query(F.data.startswith("topic_reopen_"))
async def handle_topic_reopen_callback(callback: CallbackQuery):
    try:
        ticket_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Invalid callback data for topic_reopen: {callback.data}, Error: {e}")
        await callback.answer("Error: Invalid data format.", show_alert=True)
        return

    bot_logger.info(f"Handling topic_reopen callback for Ticket {ticket_id} from Manager {callback.from_user.id}")
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if not ticket:
        await callback.answer(strs(lang='ru').ticket_not_found, show_alert=True)
        return

    if not ticket.close_date:
        await callback.answer("Request is already open.", show_alert=True)
        return

    current_topic_id = callback.message.message_thread_id
    if not current_topic_id:
        bot_logger.error(f"Cannot reopen Ticket {ticket.id}: message_thread_id is missing.")
        await callback.answer("Error: Cannot determine the topic to reopen.", show_alert=True)
        return

    user = await db.users.get_by_id(user_id=ticket.user_id)
    if not user:
        await callback.answer(f"User (ID: {ticket.user_id}) not found.", show_alert=True)
        return

    if user.current_topic_id and user.current_topic_id != current_topic_id:
        await callback.answer(
            f"User (ID: {user.id}) already has another active request in Topic {user.current_topic_id}.",
            show_alert=True
        )
        return

    ticket.close_date = None
    ticket.last_modified = datetime.now(timezone(timedelta(hours=3)))
    ticket.topic_id = current_topic_id
    ticket.manager_id = None
    await db.tickets.update(ticket=ticket)

    user.current_ticket_id = str(ticket.id)
    user.current_topic_id = ticket.topic_id
    await db.users.update(user=user)

    reopen_notification = ""
    if cf.GROUP_CHAT_ID:
        try:
            await callback.bot.reopen_forum_topic(chat_id=cf.GROUP_CHAT_ID, message_thread_id=ticket.topic_id)
            reopen_notification = strs(lang='ru').ticket_reopened_in_db_msg.format(ticket.id, ticket.topic_id) + \
                                  "\n" + strs(lang='ru').topic_reopened_msg
            bot_logger.info(f"Ticket {ticket.id} & Topic {ticket.topic_id} reopened by Manager {callback.from_user.id}")
            try:
                await callback.bot.send_message(user.id, text=strs(lang=user.lang).ticket_reopened_by_manager)
            except TelegramAPIError as e_user_notify:
                bot_logger.error(f"Failed to notify User {user.id} about reopen: {e_user_notify}")
                reopen_notification += "\n⚠️ Failed to notify user."
        except TelegramAPIError as e_topic_reopen:
            error_msg = f"Error reopening forum topic {ticket.topic_id}: {e_topic_reopen}"
            bot_logger.error(error_msg)
            reopen_notification = f"✅ Request #{ticket.id} reopened in DB.\n❌ {error_msg}"
            await callback.answer(f"Error reopening topic: {e_topic_reopen}", show_alert=True)
        except Exception as e_unexpected:
            error_msg = f"Unexpected error during topic reopen for ticket {ticket.id}: {e_unexpected}"
            bot_logger.error(error_msg, exc_info=True)
            reopen_notification = f"✅ Request #{ticket.id} reopened in DB.\n❌ Unexpected error: {e_unexpected}"
            await callback.answer(f"Unexpected error: {e_unexpected}", show_alert=True)

    try:
        new_keyboard = await get_topic_menu_keyboard(lang='ru', ticket=ticket, user=user)
        status_str = strs(lang='ru').ticket_active
        new_text = f"Ticket Menu #{ticket.id} (Status: {status_str}):\n\n{reopen_notification}"
        await callback.message.edit_text(text=new_text, reply_markup=new_keyboard)
    except TelegramAPIError as e:
        if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Failed to edit message after reopen for Ticket {ticket.id}: {e}")
            await callback.message.answer(reopen_notification)
    await callback.answer("Request reopened.")


@topics_router.message(
    F.chat.id == cf.GROUP_CHAT_ID,
    F.message_thread_id.is_not(None),
    F.from_user.is_bot == False,
    F.content_type.in_({'text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'video_note', 'animation'}),
    ~(F.text.startswith('/'))
)
async def handle_topic_message_forwarding(message: Message):
    topic_id = message.message_thread_id
    manager_user_id = message.from_user.id
    bot_logger.info(f"Received message {message.message_id} from Manager {manager_user_id} in Topic {topic_id}")

    ticket = await db.tickets.get_by_topic_id(topic_id=topic_id)

    if not ticket:
        bot_logger.warning(f"Received message in Topic {topic_id}, but no associated ticket found.")
        return

    if ticket.close_date:
        bot_logger.warning(
            f"Received message from Manager {manager_user_id} in Topic {topic_id} for a closed Ticket {ticket.id}.")
        try:
            await message.reply(strs(lang='ru').ticket_already_closed)
        except TelegramAPIError as e:
            bot_logger.error(f"Could not reply in Topic {topic_id} for closed ticket: {e}")
        return

    user_id_to_send = ticket.user_id
    if not user_id_to_send:
        bot_logger.error(f"Ticket {ticket.id} (Topic {topic_id}) has no user_id. Cannot forward message.")
        return

    reply_to_user_message_id = None
    if message.reply_to_message:
        replied_topic_message_id = message.reply_to_message.message_id
        bot_logger.info(
            f"Manager reply detected in Topic {topic_id}. Replied to Topic Message ID: {replied_topic_message_id}")
        try:
            history_content = ticket.content
            history = []
            if isinstance(history_content, str):
                history = loads(
                    history_content.replace("'", "\"").replace("None", "null").replace("True", "true").replace("False",
                                                                                                               "false"))
            elif isinstance(history_content, list):
                history = history_content

            if isinstance(history, list):
                for entry in reversed(history):
                    if isinstance(entry, dict) and entry.get("topic_message_id") == replied_topic_message_id:
                        reply_to_user_message_id = entry.get('user_private_chat_message_id')
                        if reply_to_user_message_id:
                            bot_logger.info(
                                f"Found original user's private chat message ID: {reply_to_user_message_id}")
                            break
            if not reply_to_user_message_id:
                bot_logger.warning(
                    f"Could not determine original private chat message ID for reply to Topic Message {replied_topic_message_id} in Ticket {ticket.id}")
        except Exception as e_hist:
            bot_logger.error(f"Error processing history for reply in Ticket {ticket.id}: {e_hist}")

    user_private_chat_message_id = None
    try:
        copied_to_user_msg = await message.copy_to(
            chat_id=user_id_to_send,
            reply_to_message_id=reply_to_user_message_id
        )
        user_private_chat_message_id = copied_to_user_msg.message_id
        log_reply_info = f" replying to PM msg {reply_to_user_message_id}" if reply_to_user_message_id else ""
        bot_logger.info(
            f"Copied Manager {manager_user_id}'s message from Topic {topic_id} to User {user_id_to_send} (PM Msg ID: {user_private_chat_message_id}){log_reply_info}")
    except TelegramAPIError as e:
        bot_logger.error(f"Failed to copy message to User {user_id_to_send} from Topic {topic_id}: {e}")
        try:
            await message.reply(f"❌ Failed to deliver message to user (ID: {user_id_to_send}). Error: {e.message}")
        except TelegramAPIError as reply_e:
            bot_logger.error(f"Could not reply in Topic {topic_id} about send error: {reply_e}")
        return
    except Exception as e_unexp:
        bot_logger.error(f"Unexpected error copying message to User {user_id_to_send} from Topic {topic_id}: {e_unexp}",
                         exc_info=True)
        try:
            await message.reply(f"❌ Unexpected error sending message to user {user_id_to_send}.")
        except TelegramAPIError as reply_e:
            bot_logger.error(f"Could not reply in Topic {topic_id} about unexpected send error: {reply_e}")
        return

    try:
        manager_message_info = message.model_dump(mode='json')
        history_entry = {
            "original_message": manager_message_info,
            "topic_message_id": message.message_id,
            "user_private_chat_message_id": user_private_chat_message_id
        }
        current_content = []
        if isinstance(ticket.content, str):
            try:
                current_content = loads(
                    ticket.content.replace("'", "\"").replace("None", "null").replace("True", "true").replace("False",
                                                                                                              "false"))
            except Exception as e_load:
                bot_logger.warning(f"Could not decode history for Ticket {ticket.id}: {e_load}. Resetting history.")
                current_content = []
        elif isinstance(ticket.content, list):
            current_content = ticket.content
        elif ticket.content is None:
            current_content = []
        else:
            bot_logger.warning(
                f"Ticket {ticket.id} content is of unexpected type: {type(ticket.content)}. Resetting history.")
            current_content = []

        current_content.append(history_entry)
        ticket.content = current_content
        ticket.last_modified = datetime.now(timezone(timedelta(hours=3)))
        ticket.manager_id = manager_user_id
        await db.tickets.update(ticket=ticket)
        bot_logger.info(
            f"Saved Manager {manager_user_id}'s message {message.message_id} to history of Ticket {ticket.id}")

        if message.content_type != 'text':
            media_file_id = None
            if message.photo:
                media_file_id = message.photo[-1].file_id
            elif message.video:
                media_file_id = message.video.file_id
            elif message.audio:
                media_file_id = message.audio.file_id
            elif message.document:
                media_file_id = message.document.file_id
            elif message.sticker:
                media_file_id = message.sticker.file_id
            elif message.voice:
                media_file_id = message.voice.file_id
            elif message.video_note:
                media_file_id = message.video_note.file_id

            if media_file_id:
                try:
                    destination_folder = os.path.join(cf.project['storage'], str(ticket.id))
                    os.makedirs(destination_folder, exist_ok=True)
                    media_info_path = os.path.join(destination_folder, 'media_info.txt')
                    media_group_id_str = str(message.media_group_id) if message.media_group_id else "None"
                    media_info_line = f'{message.message_id} {media_group_id_str} {media_file_id}'
                    with open(media_info_path, 'a', encoding='utf-8') as f:
                        f.write(media_info_line + '\n')
                except Exception as e_media_save:
                    bot_logger.error(f"Error saving manager media info for Ticket {ticket.id}: {e_media_save}",
                                     exc_info=True)
            else:
                bot_logger.warning(
                    f'Could not get file_id for manager media (Type: {message.content_type}) in Topic {topic_id}')
    except Exception as e_hist_save:
        bot_logger.error(f"Error saving manager message to history for Ticket {ticket.id}: {e_hist_save}",
                         exc_info=True)