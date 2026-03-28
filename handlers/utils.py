# Standard
from datetime import datetime, timezone, timedelta
from json import JSONEncoder, loads
import os

# Third-party
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

# Project
from database import db, UserModel, TicketModel
import config as cf
from translations import strs
from utils.logger import bot_logger


BATCH = 3

async def get_decline_reply_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Creates a reply keyboard with a single 'Decline' button."""
    button_list = [
        [KeyboardButton(text=strs(lang=lang).decline_btn)],
    ]
    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True, one_time_keyboard=True)


# Custom JSON Encoder that handles datetime objects
class CustomJSONEncoder(JSONEncoder):
     def default(self, obj):
         if isinstance(obj, datetime): return obj.isoformat()
         if hasattr(obj, 'model_dump'):
             try: return obj.model_dump(mode='json')
             except Exception: pass
         try: return repr(obj)
         except Exception: return JSONEncoder.default(self, obj)

# Function to get the appropriate main menu based on user status
async def get_main_menu(lang: str, user_id: int) -> ReplyKeyboardMarkup:
     """Возвращает соответствующую ReplyKeyboard главного меню для пользователя."""
     user = await db.users.get_by_id(user_id=user_id)
     if not user:
         from handlers.private.users.general import get_menu_reply_keyboard as user_kb
         bot_logger.warning(f"User {user_id} not found in get_main_menu. Returning default user keyboard.")
         return await user_kb(lang=lang)
     if user.status == 'admin':
         from handlers.private.admins.general import get_menu_reply_keyboard as admin_kb
         return await admin_kb(lang=lang)
     elif user.status == 'manager':
         from handlers.private.managers.general import get_menu_reply_keyboard as manager_kb
         return await manager_kb(user_id=user_id, lang=lang)
     else: # user
         from handlers.private.users.general import get_menu_reply_keyboard as user_kb
         return await user_kb(lang=lang)

# Function to handle the decline message
async def handle_decline_message(message: Message, state: FSMContext, menu_keyboard: ReplyKeyboardMarkup = None):
    """Handles the decline button press, clearing state and showing the appropriate menu."""
    bot_logger.info(f'Handling decline state from user {message.from_user.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    if menu_keyboard is None:
        menu_keyboard = await get_main_menu(lang=lang, user_id=message.from_user.id)

    current_state = await state.get_state()
    reply_markup_to_send = menu_keyboard
    should_remove_kb_first = False

    if current_state is not None and message.text == strs(lang=lang).decline_btn:
         reply_markup_to_send = ReplyKeyboardRemove()
         should_remove_kb_first = True

    await message.answer(
        text=strs(lang=lang).decline_msg,
        reply_markup=reply_markup_to_send
    )

    if should_remove_kb_first:
         await message.answer(
              text=strs(lang=lang).use_help,
              reply_markup=menu_keyboard
         )

    await state.clear()

# Адаптация под новую структуру content
async def make_up_ticket_page_text(lang: str, page: int, content, ticket: TicketModel, extended_info: bool = False) -> str:
    """Formats the text for a page of ticket history."""
    if content is None:
        return strs(lang=lang).ticket_no_history
    if isinstance(content, str):
        try:
            content_str = content.replace('\'', '"').replace('None', 'null').replace('True', 'true').replace('False', 'false')
            content = loads(content_str)
            if not isinstance(content, list): raise ValueError("Content is not a list")
        except Exception as e:
             bot_logger.error(f"Error decoding ticket content JSON for ticket {ticket.id}: {e}")
             content = []
    elif not isinstance(content, list):
        bot_logger.error(f"Ticket content for {ticket.id} is not a list or string, type: {type(content)}")
        content = []

    upper = page * BATCH if len(content) > page * BATCH else len(content)
    lower = upper - BATCH if upper - BATCH >= 0 else 0
    message_text = strs(lang=lang).history_ticket(upper, len(content))

    for i in range(lower, upper):
        try:
            # Получаем запись истории
            history_entry = content[i]
            if not isinstance(history_entry, dict) or "original_message" not in history_entry:
                bot_logger.warning(f"Skipping invalid history entry at index {i} in ticket {ticket.id}: type/structure {type(history_entry)}")
                continue
            message_info = history_entry["original_message"] # Получаем словарь сообщения
            if not isinstance(message_info, dict):
                 bot_logger.warning(f"Skipping invalid message_info inside entry at index {i} in ticket {ticket.id}: type {type(message_info)}")
                 continue

            message = Message(**message_info)
            media_group_id = message.media_group_id
            media_group_text = str(media_group_id) if media_group_id else "None"
            sender_info = message_info.get('from_user') or message_info.get('chat')
            sender_id = sender_info.get('id') if sender_info else None

            if not sender_id:
                bot_logger.warning(f"Sender ID not found in message_info at index {i} for ticket {ticket.id}. Message info: {message_info}")
                continue

            is_user_sender = (sender_id == ticket.user_id)
            is_manager = not is_user_sender
            text = message.html_text
            msg_caption = message.caption
            message_id = message.message_id
            sender_info_text = ""
            has_media = message.content_type != 'text'

            if extended_info:
                if is_manager:
                    manager_user = await db.users.get_by_id(user_id=sender_id)
                    manager_name = manager_user.tg_name if manager_user else f"ID: {sender_id}"
                    sender_info_text = strs(lang=lang).manager_extended(manager_name, message_id, media_group_text)
                else:
                    sender_info_text = strs(lang=lang).user_extended(ticket.user_id, message_id, media_group_text)
            else:
                if is_manager:
                    sender_info_text = strs(lang=lang).manager_usual(message_id, media_group_text)
                else:
                    sender_info_text = strs(lang=lang).user_usual(message_id, media_group_text)

            message_text += sender_info_text

            if text:
                if msg_caption:
                    message_text += strs(lang=lang).media_files_in_msg if has_media else ""
                    message_text += f"Caption: {msg_caption}\nText: {text}"
                else:
                    message_text += strs(lang=lang).media_files_in_msg if has_media else ""
                    message_text += text
            elif msg_caption:
                 message_text += strs(lang=lang).media_files_in_msg
                 message_text += msg_caption
            elif has_media:
                message_text += strs(lang=lang).media_files_in_msg

            message_text += '\n____________________________________\n\n'

        except Exception as e:
            bot_logger.error(f"Error processing message index {i} in ticket {ticket.id}: {e}")
            message_text += f"[Error processing message {i}]\n____________________________________\n\n"
    return message_text

# Адаптация под новую структуру content
async def get_media_messages(lang: str, page: int, ticket: TicketModel) -> list[Message]:
    """Extracts media messages for the specified ticket history page."""
    content = ticket.content
    if not content: return []
    if isinstance(content, str):
        try: content = loads(content.replace('\'', '"').replace('None', 'null').replace('True', 'true').replace('False', 'false'))
        except: return []
    if not isinstance(content, list): return []

    upper = page * BATCH if len(content) > page * BATCH else len(content)
    lower = upper - BATCH if upper - BATCH >= 0 else 0

    messages_to_return = []
    media_info_path = os.path.join(cf.project["storage"], str(ticket.id), 'media_info.txt')
    media_info_dict = {}
    if os.path.exists(media_info_path):
        try:
            with open(media_info_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split(' ', 2)
                    # ID сообщения теперь в 1 элементе
                    if len(parts) >= 1 and parts[0].isdigit():
                        msg_id = int(parts[0])
                        media_info_dict[msg_id] = line.strip()
        except Exception as e: bot_logger.error(f"Err read media_info.txt T{ticket.id}: {e}")

    for i in range(lower, upper):
        try:
            # Получаем запись истории
            history_entry = content[i]
            if not isinstance(history_entry, dict) or "original_message" not in history_entry:
                 continue
            msg_info = history_entry["original_message"] # Получаем словарь сообщения
            if not isinstance(msg_info, dict): continue

            message_id_from_content = msg_info.get('message_id')
            if not message_id_from_content: continue

            # Проверяем наличие message_id в media_info_dict
            if msg_info.get('content_type') != 'text' and message_id_from_content in media_info_dict:
                message = Message(**msg_info)
                media_group_text = str(message.media_group_id) if message.media_group_id else "None"
                new_caption = strs(lang=lang).msg_caption(message.message_id, media_group_text)
                if message.caption: new_caption += f"\n\n{message.caption}"
                msg_info_copy = msg_info.copy(); msg_info_copy['caption'] = new_caption
                try: messages_to_return.append(Message(**msg_info_copy))
                except Exception as e_recon: bot_logger.error(f"Err reconstruct msg {message_id_from_content}: {e_recon}")
        except Exception as e: bot_logger.error(f"Err proc msg {i} T{ticket.id} get_media: {e}")
    return messages_to_return

# Остальной код без изменений
async def make_up_tickets_info_page(lang: str, page: int, tickets: list[TicketModel], is_manager_view: bool = False):
    """Formats the text for a page of ticket information (for archive view)."""
    if tickets is None: return strs(lang=lang).ticket_empty
    upper = page * BATCH if len(tickets) > page * BATCH else len(tickets)
    lower = upper - BATCH if upper - BATCH >= 0 else 0
    tickets_info_text = strs(lang=lang).conversations(upper, len(tickets))
    for i in range(lower, upper):
        ticket = tickets[i]
        opened = str(ticket.open_date).split('.')[0] if ticket.open_date else "N/A"
        closed = str(ticket.close_date).split('.')[0] if ticket.close_date else "N/A"

        # Используем имя пользователя из тикета
        name = ticket.username or "N/A"
        tg_url = ticket.tg_url or "N/A"

        manager_name_str = "N/A"
        if is_manager_view and ticket.manager_id:
            manager_user = await db.users.get_by_id(user_id=ticket.manager_id)
            if manager_user:
                manager_name_str = manager_user.tg_name or f"ID: {ticket.manager_id}"
            else:
                manager_name_str = f"ID: {ticket.manager_id} (not found)"

        from_open_time = {'hours': 0, 'mins': 0}
        if ticket.close_date:
            try:
                from_open_time = await db.tickets.get_medium_closing_time_in_period(ticket_id=ticket.id)
            except Exception as e:
                bot_logger.error(f"Err calc time T{ticket.id}: {e}"); from_open_time = {'hours': 'err', 'mins': 'err'}

        format_string_lambda = strs(lang=lang).tickets_info
        format_string = format_string_lambda(is_manager_view=is_manager_view)

        try:
            # Собираем аргументы для форматирования.
            args = [ticket.id, opened, closed, name, tg_url]
            if is_manager_view:
                args.append(manager_name_str)
            args.extend([from_open_time.get('hours', 0), from_open_time.get('mins', 0)])

            ticket_entry = format_string.format(*args)
        except Exception as e:
            bot_logger.error(f"Err format T{ticket.id} L:{lang} M:{is_manager_view}: {e}")
            ticket_entry = f"Ticket #{ticket.id} (Format Err)\n"

        tickets_info_text += ticket_entry
    return tickets_info_text

async def make_up_opened_tickets_page(lang: str, page: int, tickets: list[TicketModel]):
    """Formats the text for a page of OPENED tickets (brief info)."""
    if not tickets: return strs(lang=lang).ticket_no_opened_tickets
    upper = page * BATCH if len(tickets) > page * BATCH else len(tickets)
    lower = upper - BATCH if upper - BATCH >= 0 else 0
    tickets_info_text = strs(lang=lang).active_tickets_title(upper, len(tickets))
    for i in range(lower, upper):
        ticket = tickets[i]; opened_dt = ticket.open_date; opened_str = "N/A"
        if opened_dt:
            try:
                if opened_dt.tzinfo == timezone.utc: opened_dt = opened_dt.astimezone(timezone(timedelta(hours=3)))
                opened_str = opened_dt.strftime('%d.%m.%Y %H:%M')
            except Exception as e: bot_logger.warning(f"Err format date T{ticket.id}: {e}"); opened_str = str(opened_dt).split('.')[0]
        name = ticket.username or "N/A"
        ticket_entry = f"<b>Тикет #{ticket.id}</b>\nПользователь: {name}\nСоздан: {opened_str} МСК\n____________________________________\n\n"
        tickets_info_text += ticket_entry
    return tickets_info_text

async def make_up_user_info(lang: str, user: UserModel) -> tuple[bool, str]:
    """Formats the text for user information."""
    if not user: return False, "User not found"
    tg_name=user.tg_name; tg_id=int(user.id); status=user.status; mute_time=user.mute_time; is_banned=user.is_banned; url_name=user.url_name or "None"
    try: as_user_tickets_len = 0 # Placeholder
    except Exception as e: bot_logger.error(f"Err fetch tickets U{tg_id}: {e}"); as_user_tickets_len = "Error"
    is_manager = False; status_text = strs(lang=lang).status_usual
    if status == 'manager': is_manager = True; status_text = strs(lang=lang).status_manager
    elif status == 'admin': is_manager = True; status_text = strs(lang=lang).status_admin
    text = strs(lang=lang).user_info.format(tg_name or "N/A", tg_id, url_name, status_text, as_user_tickets_len)
    if is_banned: text += strs(lang=lang).user_is_banned(is_banned)
    else:
        mute_time_str = "Нет"
        if mute_time:
            try:
                if isinstance(mute_time, str): mute_dt = datetime.fromisoformat(mute_time.split('.')[0])
                else: mute_dt = mute_time
                if not mute_dt.tzinfo: mute_dt = mute_dt.replace(tzinfo=timezone.utc)
                if mute_dt > datetime.now(timezone.utc): mute_time_str = mute_dt.astimezone(timezone(timedelta(hours=3))).strftime('%Y-%m-%d %H:%M:%S') + " МСК"
            except Exception as e: bot_logger.error(f"Err proc mute '{mute_time}' U{tg_id}: {e}"); mute_time_str = "Ошибка"
        text += strs(lang=lang).user_restricted.format(mute_time_str)
        text += strs(lang=lang).user_is_banned(False)
    return is_manager, text

def safe_get_callback_data(data, index, default=None, convert_type=None):
    """Safely extracts data from callback_data list."""
    try:
        value = data[index] if index < len(data) else default
        if value is default and default is not None and convert_type is not None:
            try: return convert_type(default)
            except (ValueError, TypeError): return default
        if convert_type is not None and value is not None:
            try: return convert_type(value)
            except (ValueError, TypeError): return default
        return value
    except Exception as e:
        bot_logger.error(f"Unexpected error in safe_get_callback_data: {e}, data={data}, index={index}")
        return default