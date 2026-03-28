from . import *
from utils.logger import bot_logger

# Standard
from datetime import datetime, timezone, timedelta
from json import loads
import os

# Third-party
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Project
from handlers.utils import get_decline_reply_keyboard, get_main_menu
from database import db, TicketModel
from translations import strs, create_ticket_btn, end_conversation_btn
import config as cf
from bot import bot
from aiogram.exceptions import TelegramAPIError
from handlers.private.admins.working_hours import is_working_time
from handlers import filters


# __router__ !DO NOT DELETE!
ticket_router = Router()


# __states__ !DO NOT DELETE!
class CreateTicketStates(StatesGroup):
    # get_name = State() # УДАЛЕНО
    # get_contact = State() # УДАЛЕНО
    get_first_message = State()


# async def get_skip_contact_keyboard(lang: str) -> ReplyKeyboardMarkup: # ФУНКЦИЯ УДАЛЕНА

async def get_active_request_reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    button_list = [[KeyboardButton(text=strs(lang).end_conversation_btn)]]
    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True, one_time_keyboard=False)

@ticket_router.message(filters.Private(), filters.IsUser(), ((F.text == '/create_ticket') | (F.text.in_(create_ticket_btn))), filters.IsRestricted())
async def handle_create_ticket_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /create_ticket or button from user {message.chat.id}')
    user = await db.users.get_by_id(user_id=message.chat.id)
    current_topic_id = user.current_topic_id if user else None
    lang = (await state.get_data()).get('lang', user.lang if user else 'ru')

    if not current_topic_id:
        # Сразу запрашиваем первое сообщение тикета
        await message.answer(text=strs(lang=lang).ticket_ask_message, reply_markup=await get_decline_reply_keyboard(lang=lang))
        await state.set_state(CreateTicketStates.get_first_message.state)
        return

    ticket = await db.tickets.get_by_topic_id(topic_id=current_topic_id)
    if ticket and not ticket.close_date:
        await message.answer(text=strs(lang=lang).ticket_opened_already)
        await message.answer("Вы можете продолжить диалог или завершить текущее обращение.", reply_markup=await get_active_request_reply_keyboard(lang=lang))
    else:
        if user:
            user.current_ticket_id = None
            user.current_topic_id = None
            await db.users.update(user=user)
        # Сразу запрашиваем первое сообщение тикета
        await message.answer(text=strs(lang=lang).ticket_ask_message, reply_markup=await get_decline_reply_keyboard(lang=lang))
        await state.set_state(CreateTicketStates.get_first_message.state)


@ticket_router.callback_query(F.data == 'faq_create_ticket', filters.IsUser())
async def handle_faq_create_ticket_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling faq_create_ticket callback from user {callback.from_user.id}')
    user = await db.users.get_by_id(user_id=callback.from_user.id)
    lang = (await state.get_data()).get('lang', user.lang if user else 'ru')

    if user and user.current_topic_id:
        ticket = await db.tickets.get_by_topic_id(topic_id=user.current_topic_id)
        if ticket and not ticket.close_date:
            await callback.answer(strs(lang=lang).ticket_opened_already, show_alert=True)
            try:
                await callback.message.delete()
                await callback.message.answer("Вы можете продолжить диалог или завершить текущее обращение.", reply_markup=await get_active_request_reply_keyboard(lang=lang))
            except Exception as e:
                bot_logger.warning(f"Could not delete/reply on faq_create_ticket: {e}")
            return

    try:
        await callback.message.delete()
    except Exception as e:
        bot_logger.warning(f"Could not delete FAQ message on faq_create_ticket: {e}")

    # Сразу запрашиваем первое сообщение тикета
    await callback.message.answer(text=strs(lang=lang).ticket_ask_message, reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(CreateTicketStates.get_first_message.state)
    await callback.answer()


# handle_get_name_state был УДАЛЕН
# handle_get_contact_state был УДАЛЕН


@ticket_router.message(CreateTicketStates.get_first_message, F.content_type.in_({'text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'video_note'}))
async def handle_get_first_message_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states CreateTicketStates.get_first_message from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    user = await db.users.get_by_id(user_id=message.chat.id)

    if not user: # Доп. проверка, хотя middleware должен обеспечивать наличие пользователя
        await message.answer("Произошла ошибка. Пользователь не найден. Пожалуйста, начните сначала командой /start.", reply_markup=ReplyKeyboardRemove())
        await state.clear()
        return

    # Используем имя пользователя из его профиля Telegram или стандартное имя
    name_to_save = user.tg_name if user.tg_name else f"User {user.id}"
    contact_info_to_save = None # Контактная информация больше не собирается

    first_message_original_info = None
    try:
        first_message_original_info = message.model_dump(mode='json')
    except Exception as e:
        bot_logger.error(f"Error serializing first message: {e}")
        await message.answer("Ошибка обработки вашего сообщения. Пожалуйста, начните заново.", reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        await state.clear()
        return

    current_time = datetime.now(timezone(timedelta(hours=3)))
    ticket = TicketModel(
        user_id=message.chat.id,
        username=name_to_save,
        user_email=contact_info_to_save, # Будет None
        tg_url=user.url_name or "",
        open_date=current_time,
        last_modified=current_time,
        content=[]
    )
    ticket_id_saved = None
    try:
        ticket_id_saved = await db.tickets.insert(ticket=ticket)
        if not ticket_id_saved:
            raise Exception("Failed to get ticket ID after insert")

        bot_logger.info(f"Ticket #{ticket_id_saved} created for user {user.id}")
        topic_name = f"Обращение #{ticket_id_saved} - {name_to_save}"
        topic_id = None
        topic_start_message_id = None
        first_message_topic_id = None

        if not cf.GROUP_CHAT_ID:
            bot_logger.error("GROUP_CHAT_ID is not configured!")
            await message.answer("Ошибка конфигурации бота. Обратитесь к администратору.", reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
            if ticket_id_saved:
                try:
                    ticket_to_remove = await db.tickets.get_by_id(ticket_id=ticket_id_saved)
                    if ticket_to_remove:
                        await db.tickets.delete(ticket=ticket_to_remove)
                        bot_logger.info(f"Ticket {ticket_id_saved} deleted due to missing GROUP_CHAT_ID.")
                except Exception as del_err:
                    bot_logger.error(f"Error deleting ticket {ticket_id_saved} after GROUP_CHAT_ID config error: {del_err}")
            await state.clear()
            return

        try:
            created_topic = await bot.create_forum_topic(chat_id=cf.GROUP_CHAT_ID, name=topic_name)
            topic_id = created_topic.message_thread_id
            bot_logger.info(f"Topic {topic_id} '{topic_name}' created for ticket {ticket_id_saved}")

            topic_info_text = strs('ru').ticket_created_topic_info(
                ticket_id=ticket_id_saved,
                user_name=name_to_save,
                user_id=user.id,
                user_url=user.url_name or "None",
            )
            topic_start_message = await bot.send_message(cf.GROUP_CHAT_ID, topic_info_text, message_thread_id=topic_id)
            topic_start_message_id = topic_start_message.message_id

            try:
                copied_first_message = await message.copy_to(cf.GROUP_CHAT_ID, message_thread_id=topic_id)
                first_message_topic_id = copied_first_message.message_id
                bot_logger.info(f"Successfully copied first message U{user.id} to T{topic_id} (msg ID: {first_message_topic_id})")
            except Exception as copy_err:
                bot_logger.error(f"Error copying first message U{user.id} to T{topic_id}: {copy_err}")

            ticket_from_db = await db.tickets.get_by_id(ticket_id=ticket_id_saved)
            if not ticket_from_db:
                raise Exception(f"Ticket {ticket_id_saved} not found after insert and topic creation.")

            history_entry = {
                "original_message": first_message_original_info,
                "topic_message_id": first_message_topic_id,
                "user_private_chat_message_id": message.message_id
            }
            ticket_from_db.content = [history_entry]
            ticket_from_db.topic_id = topic_id
            ticket_from_db.topic_start_message_id = topic_start_message_id
            await db.tickets.update(ticket=ticket_from_db)

            user.current_ticket_id = str(ticket_id_saved)
            user.current_topic_id = topic_id
            await db.users.update(user=user)

        except Exception as e_topic:
            bot_logger.error(f"Error during topic creation/update for Ticket {ticket_id_saved}: {e_topic}", exc_info=True)
            await message.answer("Ошибка создания чата поддержки. Пожалуйста, попробуйте позже.", reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
            if ticket_id_saved:
                try:
                    ticket_to_remove = await db.tickets.get_by_id(ticket_id=ticket_id_saved)
                    if ticket_to_remove:
                        await db.tickets.delete(ticket=ticket_to_remove)
                        bot_logger.info(f"Ticket {ticket_id_saved} deleted after topic creation failure.")
                except Exception as del_err:
                    bot_logger.error(f"Error deleting ticket {ticket_id_saved} after topic failure: {del_err}")
            await state.clear()
            return

        final_message_text = strs(lang=lang).ticket_opened
        working_hours_pref = await db.preferences.get_by_key("working_hours")
        settings = working_hours_pref.value if working_hours_pref else None
        is_working, schedule_text = is_working_time(settings, lang=lang)

        final_message_text += "\n\n" + strs(lang).support_schedule_info.format(schedule_text=schedule_text)
        if not is_working:
            final_message_text += "\n\n" + strs(lang).non_working_hours_notice

        await message.answer(text=final_message_text, reply_markup=await get_active_request_reply_keyboard(lang=lang), reply_to_message_id=None)
        await state.clear()

    except Exception as e:
        bot_logger.error(f"Unexpected error in final step of ticket creation for user {message.chat.id}: {e}", exc_info=True)
        await message.answer("Произошла непредвиденная ошибка при создании обращения. Пожалуйста, попробуйте позже.", reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        if ticket_id_saved:
            try:
                ticket_to_remove = await db.tickets.get_by_id(ticket_id=ticket_id_saved)
                if ticket_to_remove:
                    await db.tickets.delete(ticket=ticket_to_remove)
                    bot_logger.info(f"Ticket {ticket_id_saved} deleted after unexpected error.")
            except Exception as del_err:
                bot_logger.error(f"Error deleting ticket {ticket_id_saved} after unexpected error: {del_err}")
        await state.clear()


@ticket_router.message(filters.Private(), filters.IsUser(), F.text.in_(end_conversation_btn), filters.NotInState())
async def handle_end_conversation_button(message: Message, state: FSMContext):
    bot_logger.info(f"Handling 'End request' button from user {message.from_user.id}")
    lang = (await state.get_data()).get('lang', 'ru')
    user = await db.users.get_by_id(user_id=message.from_user.id)

    if not (user and user.current_topic_id):
        await message.answer(strs(lang=lang).ticket_no_opened, reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        return

    ticket = await db.tickets.get_by_topic_id(topic_id=user.current_topic_id)
    if not ticket or ticket.close_date:
        if user:
            user.current_ticket_id = None
            user.current_topic_id = None
            await db.users.update(user=user)
        await message.answer(strs(lang=lang).ticket_no_opened, reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        return

    current_date = datetime.now(timezone(timedelta(hours=3)))
    ticket.close_date = current_date
    ticket.last_modified = current_date
    original_topic_id = ticket.topic_id
    ticket.manager_id = None
    ticket.topic_id = None
    await db.tickets.update(ticket=ticket)

    user.current_ticket_id = None
    user.current_topic_id = None
    await db.users.update(user=user)

    if original_topic_id and cf.GROUP_CHAT_ID:
        try:
            user_display_name = user.tg_name if user.tg_name else f"ID: {user.id}"
            await bot.send_message(cf.GROUP_CHAT_ID, f"❗️ Пользователь ({user_display_name}) завершил обращение #{ticket.id}.", message_thread_id=original_topic_id)
            await bot.close_forum_topic(cf.GROUP_CHAT_ID, original_topic_id)
        except Exception as e:
            bot_logger.error(f"Failed to close topic {original_topic_id} or send notification: {e}")

    await message.answer(strs(lang=lang).ticket_closed_by_user, reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))


@ticket_router.message(
    filters.Private(), filters.IsUser(), filters.InTicket(),
    filters.NotInState(), filters.IsRestricted()
)
async def handle_user_ticket_message(message: Message, state: FSMContext):
    user = await db.users.get_by_id(user_id=message.chat.id)
    lang = user.lang if user else 'ru'
    current_topic_id = user.current_topic_id if user else None

    if not current_topic_id:
        await message.answer(strs(lang=lang).ticket_no_opened, reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        return

    ticket = await db.tickets.get_by_topic_id(topic_id=current_topic_id)
    if not ticket or ticket.close_date:
        if user:
            user.current_ticket_id = None
            user.current_topic_id = None
            await db.users.update(user=user)
        await message.answer(strs(lang=lang).ticket_already_closed, reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id))
        return

    reply_to_topic_message_id = None
    if message.reply_to_message:
        replied_to_user_private_chat_message_id = message.reply_to_message.message_id
        bot_logger.info(f"User reply detected in private chat. Replied to user msg ID: {replied_to_user_private_chat_message_id}")
        try:
            history_content = ticket.content
            history = []
            if isinstance(history_content, str):
                history = loads(history_content.replace("'", "\"").replace("None", "null").replace("True", "true").replace("False", "false"))
            elif isinstance(history_content, list):
                history = history_content

            if isinstance(history, list):
                found_target_id = None
                for entry in reversed(history):
                    if isinstance(entry, dict) and entry.get("user_private_chat_message_id") == replied_to_user_private_chat_message_id:
                        original_msg_data = entry.get("original_message")
                        if isinstance(original_msg_data, dict):
                            sender_info = original_msg_data.get('from_user') or original_msg_data.get('chat')
                            if sender_info and sender_info.get('id') != user.id:
                                found_target_id = entry.get("topic_message_id")
                                if found_target_id:
                                    bot_logger.info(f"Found corresponding manager topic message ID: {found_target_id}")
                                    break
                if not found_target_id:
                    bot_logger.info(f"Manager message not found for reply to {replied_to_user_private_chat_message_id}. Searching for user's own message...")
                    for entry in reversed(history):
                         if isinstance(entry, dict) and entry.get("user_private_chat_message_id") == replied_to_user_private_chat_message_id:
                            original_msg_data = entry.get("original_message")
                            if isinstance(original_msg_data, dict):
                                sender_info = original_msg_data.get('from_user') or original_msg_data.get('chat')
                                if sender_info and sender_info.get('id') == user.id:
                                    found_target_id = entry.get("topic_message_id")
                                    if found_target_id:
                                        bot_logger.info(f"Found corresponding user's own topic message ID: {found_target_id}")
                                        break
                reply_to_topic_message_id = found_target_id

            if not reply_to_topic_message_id:
                bot_logger.warning(f"Could not find corresponding topic message ID for user reply to {replied_to_user_private_chat_message_id} in T{ticket.id}")
        except Exception as e:
            bot_logger.error(f"Error searching for message ID in T{ticket.id} history: {e}")

    topic_message_id = None
    if cf.GROUP_CHAT_ID and ticket.topic_id:
        try:
            copied_message = await message.copy_to(
                cf.GROUP_CHAT_ID,
                message_thread_id=ticket.topic_id,
                reply_to_message_id=reply_to_topic_message_id
            )
            topic_message_id = copied_message.message_id
            log_reply_info = f" replying to topic msg {reply_to_topic_message_id}" if reply_to_topic_message_id else ""
            bot_logger.info(f"Copied message from U{message.chat.id} to T{ticket.topic_id} (msg ID: {topic_message_id}){log_reply_info}")
        except TelegramAPIError as e:
            bot_logger.error(f"Error copying message U{message.chat.id} to T{ticket.topic_id}: {e}")
        except Exception as e:
             bot_logger.error(f"Unexpected error copying message U{message.chat.id} to T{ticket.topic_id}: {e}")

    try:
        original_message_info = message.model_dump(mode='json')
        history_entry = {
            "original_message": original_message_info,
            "topic_message_id": topic_message_id,
            "user_private_chat_message_id": message.message_id
        }
        current_content = []
        if isinstance(ticket.content, str):
            try:
                current_content = loads(ticket.content.replace("'", "\"").replace("None", "null").replace("True", "true").replace("False", "false"))
            except Exception as load_err:
                bot_logger.warning(f"Could not decode history for Ticket {ticket.id}: {load_err}. Resetting history.")
                current_content = []
        elif isinstance(ticket.content, list):
            current_content = ticket.content
        elif ticket.content is None:
            current_content = []
        else:
            bot_logger.warning(f"Ticket {ticket.id} content is of unexpected type: {type(ticket.content)}. Resetting history.")
            current_content = []

        current_content.append(history_entry)
        ticket.content = current_content
        ticket.last_modified = datetime.now(timezone(timedelta(hours=3)))
        await db.tickets.update(ticket=ticket)

        if message.content_type != 'text':
            media_file_id = None
            if message.photo: media_file_id = message.photo[-1].file_id
            elif message.video: media_file_id = message.video.file_id
            elif message.audio: media_file_id = message.audio.file_id
            elif message.document: media_file_id = message.document.file_id
            elif message.sticker: media_file_id = message.sticker.file_id
            elif message.voice: media_file_id = message.voice.file_id
            elif message.video_note: media_file_id = message.video_note.file_id

            if media_file_id:
                try:
                    destination_folder = os.path.join(cf.project['storage'], str(ticket.id))
                    os.makedirs(destination_folder, exist_ok=True)
                    media_info_path = os.path.join(destination_folder, 'media_info.txt')
                    media_group_id_str = str(message.media_group_id) if message.media_group_id else "None"
                    media_info_line = f'{message.message_id} {media_group_id_str} {media_file_id}'
                    with open(media_info_path, 'a', encoding='utf-8') as f:
                        f.write(media_info_line + '\n')
                except Exception as e:
                    bot_logger.error(f"Error saving user media info for Ticket {ticket.id}: {e}")
            else:
                bot_logger.warning(f'Could not get file_id for user media (Type: {message.content_type}) in Ticket {ticket.id}')
    except Exception as e:
         bot_logger.error(f"Error saving message to history for Ticket {ticket.id}: {e}", exc_info=True)


@ticket_router.message(
    filters.Private(), filters.IsUser(), filters.NotInState(),
    ~filters.IsCommandOrMenuButton(), filters.IsRestricted(),
    F.content_type.in_({'text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'video_note', 'animation'})
)
async def handle_direct_user_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot_logger.info(f"Handling direct message from user {user_id}")
    user = await db.users.get_by_id(user_id=user_id)
    lang = user.lang if user else 'ru'
    await state.update_data({'lang': lang})

    if user and user.current_topic_id:
        ticket = await db.tickets.get_by_topic_id(topic_id=user.current_topic_id)
        if ticket and not ticket.close_date:
            bot_logger.info(f"User {user_id} has active ticket {ticket.id}. Handling direct message within ticket.")
            await handle_user_ticket_message(message, state)
            return
        else:
            if user:
                user.current_ticket_id = None
                user.current_topic_id = None
                await db.users.update(user=user)

    bot_logger.info(f"User {user_id} has no active ticket or previous ticket was closed. Initiating creation process from direct message.")
    # Сразу запрашиваем первое сообщение тикета
    await message.answer(text=strs(lang=lang).ticket_ask_message, reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(CreateTicketStates.get_first_message.state)