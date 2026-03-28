from utils.logger import bot_logger
from math import ceil

# Third-party imports
from aiogram.types import (
    InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument,
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

# Project Imports
from handlers.private.managers import *
import handlers.utils as utils
from database import db, TicketModel
from handlers.utils import (
    get_media_messages,
    make_up_ticket_page_text,
    make_up_tickets_info_page,
    make_up_user_info,
)
from translations import strs, my_tickets_btn, opened_tickets_btn
import config as cf

# __router__ !DO NOT DELETE!
ticket_router = Router()


# --- Functions for Keyboard Generation ---
async def create_media_controls_keyboard(lang: str, current_index: int, total_count: int, ticket_id: str, history_page: int) -> InlineKeyboardMarkup:
    """Creates keyboard for media navigation."""
    nav_row = [
        InlineKeyboardButton(
            text='⏪',
            callback_data=f'media_nav_prev_{ticket_id}_{history_page}'
        ),
        InlineKeyboardButton(
            text=f'{current_index + 1}/{total_count}',
            callback_data='media_page_counter'
        ),
        InlineKeyboardButton(
            text='⏩',
            callback_data=f'media_nav_next_{ticket_id}_{history_page}'
        )
    ]
    buttons = [
        nav_row,
        [InlineKeyboardButton(
            text=strs(lang=lang).delete_btn, # Используется текст "Закрыть"
            callback_data=f'media_nav_close_{ticket_id}_{history_page}'
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_media_from_info(client_bot: Bot, chat_id: int, message_info: dict, reply_markup=None):
    """Sends media file from message_info dictionary."""
    message_obj = Message(**message_info) # Переименовано, чтобы не конфликтовать с импортом Message
    caption = message_obj.caption
    sent_message = None
    try:
        if message_obj.photo:
            sent_message = await client_bot.send_photo(chat_id=chat_id, photo=message_obj.photo[-1].file_id, caption=caption, reply_markup=reply_markup)
        elif message_obj.video:
            sent_message = await client_bot.send_video(chat_id=chat_id, video=message_obj.video.file_id, caption=caption, reply_markup=reply_markup)
        elif message_obj.document:
            sent_message = await client_bot.send_document(chat_id=chat_id, document=message_obj.document.file_id, caption=caption, reply_markup=reply_markup)
        elif message_obj.audio:
            sent_message = await client_bot.send_audio(chat_id=chat_id, audio=message_obj.audio.file_id, caption=caption, reply_markup=reply_markup)
        elif message_obj.voice:
            sent_message = await client_bot.send_voice(chat_id=chat_id, voice=message_obj.voice.file_id, caption=caption, reply_markup=reply_markup)
        elif message_obj.video_note:
            sent_message = await client_bot.send_video_note(chat_id=chat_id, video_note=message_obj.video_note.file_id)
            if reply_markup: await client_bot.send_message(chat_id, strs('ru').media_btn, reply_markup=reply_markup) # Текст кнопки как заголовок
        elif message_obj.sticker:
             sent_message = await client_bot.send_sticker(chat_id=chat_id, sticker=message_obj.sticker.file_id)
             if reply_markup: await client_bot.send_message(chat_id, strs('ru').media_btn, reply_markup=reply_markup) # Текст кнопки как заголовок
        else:
            bot_logger.warning(f"Unsupported media type for sending: {message_obj.content_type}")
            sent_message = await client_bot.send_message(chat_id, f"[Unsupported media type: {message_obj.content_type}]\n{caption if caption else ''}", reply_markup=reply_markup)
    except TelegramAPIError as e:
        bot_logger.error(f"Telegram API Error sending media ({getattr(message_obj, 'content_type', 'unknown')}): {e}", exc_info=True)
        try:
            sent_message = await client_bot.send_message(chat_id, "Failed to load media.", reply_markup=reply_markup)
        except TelegramAPIError as e_fallback:
            bot_logger.error(f"Critical Telegram API error sending fallback media error message: {e_fallback}", exc_info=True)
    except Exception as e: # Более общее исключение для других ошибок
        bot_logger.error(f"Unexpected error sending media ({getattr(message_obj, 'content_type', 'unknown')}): {e}", exc_info=True)
        # Попытка отправить запасное сообщение может также провалиться, если бот заблокирован и т.д.
    return sent_message


async def get_opened_tickets_pagination_keyboard(lang: str, tickets: list[TicketModel], page: int) -> InlineKeyboardMarkup:
    """Creates keyboard for paginating OPEN tickets"""
    button_list = []
    max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
    if page > max_pages > 0: page = max_pages # Коррекция, если страница стала невалидной
    if page < 1: page = 1

    upper = page * utils.BATCH if tickets and len(tickets) > page * utils.BATCH else (len(tickets) if tickets else 0)
    lower = upper - utils.BATCH if upper - utils.BATCH >= 0 else 0

    if tickets:
        for i in range(lower, upper):
            ticket = tickets[i]
            ticket_id_str = str(ticket.id) # ID тикета для callback_data
            ticket_buttons_for_row = [InlineKeyboardButton(text=f'#{ticket_id_str} - {ticket.username or "N/A"}', callback_data='no_action')]
            if ticket.topic_id and ticket.topic_start_message_id and cf.GROUP_CHAT_ID:
                chat_id_str = str(cf.GROUP_CHAT_ID)
                if chat_id_str.startswith("-100"):
                    chat_id_for_url = chat_id_str[4:]
                    topic_url = f"https://t.me/c/{chat_id_for_url}/{ticket.topic_id}/{ticket.topic_start_message_id}"
                    ticket_buttons_for_row.append(InlineKeyboardButton(
                        text=strs(lang=lang).link_to_topic_btn,
                        url=topic_url
                    ))
                else:
                     bot_logger.warning(f"Cannot form standard topic link for GROUP_CHAT_ID: {cf.GROUP_CHAT_ID}")
            button_list.append(ticket_buttons_for_row)

    if max_pages > 1:
        nav_row_buttons = [
            InlineKeyboardButton(text="◀️", callback_data=f"opened_page_prev_{page}"),
            InlineKeyboardButton(text=f"{page}/{max_pages}", callback_data="no_action"),
            InlineKeyboardButton(text="▶️", callback_data=f"opened_page_next_{page}")
        ]
        button_list.append(nav_row_buttons)

    button_list.append([InlineKeyboardButton(
        text=strs(lang=lang).delete_btn, # Текст "Закрыть"
        callback_data="hide_btn" # Действие "Спрятать" (удалить сообщение)
    )])

    return InlineKeyboardMarkup(inline_keyboard=button_list)


async def get_archive_menu_inline_keyboard(lang: str, tickets: list[TicketModel], page: int) -> InlineKeyboardMarkup:
    """ Keyboard for manager's archive navigation """
    button_list = []
    max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
    if page > max_pages > 0: page = max_pages
    if page < 1: page = 1

    upper = page * utils.BATCH if tickets and len(tickets) > page * utils.BATCH else (len(tickets) if tickets else 0)
    lower = upper - utils.BATCH if upper - utils.BATCH >= 0 else 0

    if tickets:
        for i in range(lower, upper):
            ticket = tickets[i]
            button_list.append(
                [InlineKeyboardButton(text=f'{strs(lang=lang).ticket} #{ticket.id}',
                                      callback_data=f'archive_ticket_btn {ticket.id} {page} True')]
            )
    nav_row = []
    if max_pages > 1:
        nav_row = [
            InlineKeyboardButton(text='⏪', callback_data=f'archive_prev_btn {page}'),
            InlineKeyboardButton(text=f'{page} / {max_pages}', callback_data='archive_page_counter'),
            InlineKeyboardButton(text='⏩', callback_data=f'archive_next_btn {page}')
        ]
        button_list.append(nav_row)

    button_list.append([InlineKeyboardButton(text=strs(lang=lang).back_btn, callback_data=f'archive_back_to_main_menu')])
    return InlineKeyboardMarkup(inline_keyboard=button_list)

async def get_ticket_history_inline_keyboard(
    lang: str, ticket_id: str, page: int, ticket: TicketModel,
    viewer_id: int | None = None,
    target_user_id: int | None = None,
    is_manager_view: bool = True,
    history_is_empty: bool = False,
    from_user_archive: bool = False,
) -> InlineKeyboardMarkup:
    button_list = []
    content = ticket.content
    max_pages = ceil(len(content) / utils.BATCH) if content else 1
    if page > max_pages > 0: page = max_pages
    if page < 1: page = 1

    if not history_is_empty:
        nav_row = []
        if max_pages > 1:
            callback_prefix = f'{ticket_id} {page} {viewer_id or "None"} {int(is_manager_view)} {int(from_user_archive)}'
            nav_row = [
                InlineKeyboardButton(text='⏪', callback_data=f'history_prev_btn {callback_prefix} {target_user_id or "None"}'),
                InlineKeyboardButton(text=f'{page} / {max_pages}', callback_data='no_action'),
                InlineKeyboardButton(text='⏩', callback_data=f'history_next_btn {callback_prefix} {target_user_id or "None"}')
            ]
            button_list.append(nav_row)
        button_list.append([InlineKeyboardButton(text=strs(lang=lang).media_btn, callback_data=f'history_open_media_btn {ticket_id} {page}')])

    if is_manager_view and viewer_id:
        button_list.append([InlineKeyboardButton(text=strs(lang=lang).user_info_btn, callback_data=f'ticket_user_info {ticket.user_id}')])
        viewer = await db.users.get_by_id(user_id=viewer_id)
        if viewer and viewer.status == 'admin':
             button_list.append([InlineKeyboardButton(text=strs(lang=lang).ticket_delete_btn, callback_data=f'ticket_delete {ticket_id}')])

    back_callback_data = 'history_back_to_manager_archive'
    if from_user_archive and target_user_id:
        back_callback_data = f'history_back_to_user_archive {target_user_id}'

    button_list.append([InlineKeyboardButton(text=strs(lang=lang).back_btn, callback_data=back_callback_data)])
    return InlineKeyboardMarkup(inline_keyboard=button_list)

# --- HANDLERS FOR BUTTONS AND COMMANDS ---

@ticket_router.message(
    filters.Private(), filters.IsManagerOrAdmin(),
    F.text.in_(my_tickets_btn)
)
async def handle_my_tickets_button_manager(message: Message, state: FSMContext):
    bot_logger.info(f'Handling my_tickets_btn button from manager/admin {message.chat.id}')
    await handle_manager_archive_button(message, state)

@ticket_router.message(
    filters.Private(), filters.IsManagerOrAdmin(),
    F.text.in_(opened_tickets_btn)
)
async def handle_opened_tickets_button(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot_logger.info(f'Handling opened_tickets_btn from manager/admin {user_id}')
    lang = (await state.get_data()).get('lang', 'ru')

    opened_tickets = await db.tickets.get_all_opened()
    await state.update_data(cached_opened_tickets=opened_tickets, last_opened_page=1)

    if opened_tickets:
        page = 1
        text = await utils.make_up_opened_tickets_page(
            page=page, tickets=opened_tickets, lang=lang
        )
        keyboard = await get_opened_tickets_pagination_keyboard(
            tickets=opened_tickets, page=page, lang=lang
        )
        await message.answer(text=text, reply_markup=keyboard)
    else:
        await message.answer(strs(lang=lang).ticket_no_opened_tickets)

async def handle_opened_tickets_pagination(callback: CallbackQuery, state: FSMContext, direction: str):
    bot_logger.info(f'Handling opened tickets pagination ({direction}) for user {callback.message.chat.id}')
    data = callback.data.split('_')
    try:
        current_page_from_callback = int(data[-1])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid page number in opened tickets pagination callback: {callback.data}")
        await callback.answer("Navigation error.", show_alert=True)
        return

    user_data = await state.get_data()
    lang = user_data.get('lang', 'ru')
    opened_tickets = user_data.get('cached_opened_tickets')

    if opened_tickets is None:
        opened_tickets = await db.tickets.get_all_opened()
        await state.update_data(cached_opened_tickets=opened_tickets)

    if not opened_tickets:
        await callback.answer(text=strs(lang=lang).ticket_no_opened_tickets, show_alert=True)
        try: await callback.message.delete()
        except TelegramAPIError as e: bot_logger.warning(f"Could not delete message on no opened tickets: {e}")
        except Exception as e: bot_logger.error(f"Unexpected error deleting message: {e}", exc_info=True)
        return

    max_pages = ceil(len(opened_tickets) / utils.BATCH) if opened_tickets else 1
    page_to_show = current_page_from_callback # Используем страницу из callback как текущую

    if direction == 'prev':
        page_to_show = current_page_from_callback - 1 if current_page_from_callback > 1 else max_pages
    elif direction == 'next':
        page_to_show = current_page_from_callback + 1 if current_page_from_callback < max_pages else 1

    if page_to_show != current_page_from_callback or user_data.get('last_opened_page') != page_to_show : # Обновляем только если страница изменилась
        text = await utils.make_up_opened_tickets_page(
            page=page_to_show, tickets=opened_tickets, lang=lang
        )
        keyboard = await get_opened_tickets_pagination_keyboard(
            tickets=opened_tickets, page=page_to_show, lang=lang
        )
        try:
            await callback.message.edit_text(text=text, reply_markup=keyboard)
            await state.update_data(last_opened_page=page_to_show)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message (opened tickets pagination): {e}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message (opened tickets pagination): {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith('opened_page_prev_'), filters.IsManagerOrAdmin())
async def handle_opened_page_prev_button(callback: CallbackQuery, state: FSMContext):
    await handle_opened_tickets_pagination(callback, state, 'prev')

@ticket_router.callback_query(F.data.startswith('opened_page_next_'), filters.IsManagerOrAdmin())
async def handle_opened_page_next_button(callback: CallbackQuery, state: FSMContext):
    await handle_opened_tickets_pagination(callback, state, 'next')

@ticket_router.callback_query(F.data == 'delete_btn', filters.IsManagerOrAdmin())
async def handle_delete_button_callback(callback: CallbackQuery):
    bot_logger.info(f'Handling delete_btn callback from user {callback.message.chat.id}')
    try: await callback.message.delete()
    except TelegramAPIError as e: bot_logger.warning(f"Could not delete message via delete_btn: {e}")
    except Exception as e: bot_logger.error(f"Unexpected error deleting message via delete_btn: {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith('hide_btn'), filters.IsManagerOrAdmin())
async def handle_hide_button_callback(callback: CallbackQuery):
    bot_logger.info(f'Handling hide button callback from user {callback.message.chat.id}')
    try: await callback.message.delete()
    except TelegramAPIError as e: bot_logger.warning(f"Could not delete message via hide_btn: {e}")
    except Exception as e: bot_logger.error(f"Unexpected error deleting message via hide_btn: {e}", exc_info=True)
    await callback.answer()

# --- ARCHIVE HANDLERS ---

async def handle_manager_archive_button(message_or_callback: Message | CallbackQuery, state: FSMContext):
    user_id = message_or_callback.from_user.id
    current_message = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message

    bot_logger.info(f'Showing archive for manager/admin {user_id}')
    lang = (await state.get_data()).get('lang', 'ru')

    closed_tickets = await db.tickets.get_all_closed_tickets()
    manager = await db.users.get_by_id(user_id=user_id)
    if manager: # Логируем статус, если менеджер найден
        if manager.status == 'admin':
            bot_logger.info(f"Fetched all closed tickets for admin {user_id}")
        elif manager.status == 'manager':
            bot_logger.info(f"Fetched all closed tickets for manager {user_id}")

    await state.update_data(cached_closed_tickets=closed_tickets, last_archive_page=1)

    if closed_tickets:
        page = 1
        text = await utils.make_up_tickets_info_page(
            page=page, tickets=closed_tickets, is_manager_view=True, lang=lang
        )
        keyboard = await get_archive_menu_inline_keyboard(
            tickets=closed_tickets, page=page, lang=lang
        )
        try:
            if isinstance(message_or_callback, CallbackQuery):
                await current_message.edit_text(text=text, reply_markup=keyboard)
            else:
                 await current_message.answer(text=text, reply_markup=keyboard)
        except TelegramAPIError as e:
             bot_logger.error(f"Telegram API Error showing manager archive: {e}", exc_info=True)
             if isinstance(message_or_callback, CallbackQuery): # Если это callback, то сообщение уже есть
                 try:
                     if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower() :
                         await current_message.answer(text=text, reply_markup=keyboard) # Отправляем новое
                     elif "message is not modified" not in str(e).lower(): # Логируем, только если это не "not modified"
                        bot_logger.error(f"Failed to edit_text for manager archive: {e}", exc_info=True)
                 except Exception as e_send:
                     bot_logger.error(f"Error sending new message for manager archive after edit fail: {e_send}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error showing manager archive: {e}", exc_info=True)
        if isinstance(message_or_callback, CallbackQuery):
            await message_or_callback.answer()
    else:
        no_archive_text = strs(lang=lang).ticket_empty
        if isinstance(message_or_callback, CallbackQuery):
             await message_or_callback.answer(text=no_archive_text, show_alert=True)
        else:
             await current_message.answer(text=no_archive_text)

@ticket_router.callback_query(F.data == 'archive_btn', filters.IsManagerOrAdmin())
async def handle_manager_archive_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling archive_btn callback from manager/admin {callback.message.chat.id}')
    await handle_manager_archive_button(callback, state)

@ticket_router.callback_query(F.data.startswith('archive_ticket_btn'), filters.IsManagerOrAdmin())
async def handle_archive_ticket_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling archive_menu ticket button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        ticket_id = data[1]
        archive_page = int(data[2])
        # is_manager_archive_str = data[3] # Не используется
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Error parsing callback_data for archive_ticket_btn: {callback.data}, {e}", exc_info=True)
        await callback.answer("Error opening ticket.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)

    if not ticket:
        await callback.answer(text=strs(lang=lang).ticket_not_found, show_alert=True)
        return

    await state.update_data(last_archive_page=archive_page)
    content = ticket.content
    history_is_empty = not content
    current_page = 1 # История всегда начинается с первой страницы

    if not content:
        ticket_text = strs(lang=lang).ticket_no_history
        keyboard = await get_ticket_history_inline_keyboard(
            lang=lang, ticket_id=ticket_id, page=current_page,
            viewer_id=callback.from_user.id,
            is_manager_view=True, ticket=ticket, history_is_empty=True
        )
    else:
        ticket_text = await make_up_ticket_page_text(
            page=current_page, content=content, ticket=ticket, extended_info=True, lang=lang
        )
        keyboard = await get_ticket_history_inline_keyboard(
            lang=lang, ticket_id=ticket_id, page=current_page,
            viewer_id=callback.from_user.id,
            is_manager_view=True, ticket=ticket
        )
    try:
        await callback.message.edit_text(text=ticket_text, reply_markup=keyboard)
    except TelegramAPIError as e:
         if "message is not modified" not in str(e).lower():
             bot_logger.error(f"Telegram API Error editing message for history from archive: {e}", exc_info=True)
         # Если не "not modified", можно попробовать удалить и отправить заново
         if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower() :
             try:
                 await callback.message.delete()
                 await callback.message.answer(text=ticket_text, reply_markup=keyboard)
             except Exception as e_send:
                  bot_logger.error(f"Error sending new message for history from archive after edit fail: {e_send}", exc_info=True)
    except Exception as e:
        bot_logger.error(f"Unexpected error editing message for history from archive: {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith(('archive_prev_btn', 'archive_next_btn')), filters.IsManagerOrAdmin())
async def handle_archive_page_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling archive_menu page button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    action = data[0].split('_')[1] # prev or next
    try:
        current_page_from_callback = int(data[1])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid page number in archive pagination callback: {callback.data}", exc_info=True)
        await callback.answer("Navigation error.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    user_data = await state.get_data()
    tickets = user_data.get('cached_closed_tickets')

    if tickets is None:
        tickets = await db.tickets.get_all_closed_tickets()
        await state.update_data(cached_closed_tickets=tickets)

    if not tickets:
        await callback.answer(text=strs(lang=lang).ticket_empty, show_alert=True)
        return

    max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
    page_to_show = current_page_from_callback

    if action == 'next':
        page_to_show = current_page_from_callback + 1 if current_page_from_callback < max_pages else 1
    elif action == 'prev':
        page_to_show = current_page_from_callback - 1 if current_page_from_callback > 1 else max_pages

    if page_to_show != current_page_from_callback or user_data.get('last_archive_page') != page_to_show:
        text = await make_up_tickets_info_page(page=page_to_show, tickets=tickets, is_manager_view=True, lang=lang)
        keyboard = await get_archive_menu_inline_keyboard(lang=lang, tickets=tickets, page=page_to_show)
        try:
            await callback.message.edit_text(text=text, reply_markup=keyboard)
            await state.update_data(last_archive_page=page_to_show)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message (archive pagination): {e}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message (archive pagination): {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data == 'archive_page_counter', filters.IsManagerOrAdmin())
async def handle_archive_page_counter_callback(callback: CallbackQuery):
    await callback.answer()

@ticket_router.callback_query(F.data == 'archive_back_to_main_menu', filters.IsManagerOrAdmin())
async def handle_archive_back_to_main_menu_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling archive_back_to_main_menu callback from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    user = await db.users.get_by_id(user_id=callback.message.chat.id)

    await state.update_data(cached_closed_tickets=None, last_archive_page=None)

    from handlers.utils import get_main_menu # Локальный импорт, чтобы избежать циклического
    # Ошибка типа клавиатуры была здесь. get_main_menu возвращает ReplyKeyboardMarkup.
    # edit_text ожидает InlineKeyboardMarkup. Нужно отправлять новое сообщение.
    main_menu_kb = await get_main_menu(lang=lang, user_id=user.id)
    help_text = strs(lang).admin_general_help if user and user.status == 'admin' else strs(lang).manager_general_help

    try:
        await callback.message.delete() # Сначала удаляем старое сообщение с инлайн-клавиатурой
        await callback.message.answer(text=help_text, reply_markup=main_menu_kb) # Отправляем новое с ReplyKeyboard
    except TelegramAPIError as e:
        bot_logger.error(f"Telegram API Error returning to main menu from archive: {e}", exc_info=True)
        # Если удаление не удалось, все равно пытаемся отправить новое
        try:
            await callback.message.answer(text=help_text, reply_markup=main_menu_kb)
        except Exception as e2:
             bot_logger.error(f"Error sending new message for main menu after delete fail: {e2}", exc_info=True)
    except Exception as e:
        bot_logger.error(f"Unexpected error returning to main menu from archive: {e}", exc_info=True)
    await callback.answer()


# --- HANDLERS FOR SPECIFIC USER'S ARCHIVE ---

@ticket_router.callback_query(F.data.startswith('ticket_user_tickets'), filters.IsManagerOrAdmin())
async def handle_user_tickets_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_user_tickets button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        user_id = int(data[1])
        # data[2] (is_manager_str) не используется
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Error parsing callback_data for ticket_user_tickets: {callback.data}, {e}", exc_info=True)
        await callback.answer("Error fetching user tickets.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    tickets = await db.tickets.get_all_by_id(user_id=user_id, is_manager=False)

    if tickets:
        await state.update_data(cached_user_specific_tickets=tickets, viewing_target_user_id=user_id, last_user_archive_page=1)
        text = await make_up_tickets_info_page(page=1, tickets=tickets, is_manager_view=True, lang=lang)
        keyboard = await get_user_specific_archive_menu_inline_keyboard(
             lang=lang, tickets=tickets, page=1, target_user_id=user_id
        )
        try:
            await callback.message.edit_text(text=text, reply_markup=keyboard)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message in handle_user_tickets_button_callback: {e}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message in handle_user_tickets_button_callback: {e}", exc_info=True)

    else:
        await callback.answer(f"User {user_id} has no tickets.", show_alert=True)
    await callback.answer()

async def get_user_specific_archive_menu_inline_keyboard(lang: str, tickets: list[TicketModel], page: int, target_user_id: int) -> InlineKeyboardMarkup:
    button_list = []
    max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
    if page > max_pages > 0: page = max_pages
    if page < 1: page = 1

    upper = page * utils.BATCH if tickets and len(tickets) > page * utils.BATCH else (len(tickets) if tickets else 0)
    lower = upper - utils.BATCH if upper - utils.BATCH >= 0 else 0

    if tickets:
        for i in range(lower, upper):
            ticket = tickets[i]
            button_list.append(
                [InlineKeyboardButton(text=f'{strs(lang=lang).ticket} #{ticket.id}',
                                      callback_data=f'user_archive_ticket_btn {ticket.id} {page} {target_user_id} True')]
            )
    nav_row = []
    if max_pages > 1:
        nav_row = [
            InlineKeyboardButton(text='⏪', callback_data=f'user_archive_prev_btn {page} {target_user_id}'),
            InlineKeyboardButton(text=f'{page} / {max_pages}', callback_data='archive_page_counter'),
            InlineKeyboardButton(text='⏩', callback_data=f'user_archive_next_btn {page} {target_user_id}')
        ]
        button_list.append(nav_row)

    button_list.append([InlineKeyboardButton(text=strs(lang=lang).back_btn, callback_data=f'user_archive_back_to_info {target_user_id}')])
    return InlineKeyboardMarkup(inline_keyboard=button_list)

@ticket_router.callback_query(F.data.startswith('user_archive_ticket_btn'), filters.IsManagerOrAdmin())
async def handle_user_archive_ticket_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_archive_ticket_btn callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        ticket_id = data[1]
        archive_page = int(data[2])
        target_user_id = int(data[3])
        # data[4] (is_manager_archive_str) не используется
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Error parsing callback_data for user_archive_ticket_btn: {callback.data}, {e}", exc_info=True)
        await callback.answer("Error opening ticket.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)

    if not ticket:
        await callback.answer(text=strs(lang=lang).ticket_not_found, show_alert=True)
        return

    if ticket.user_id != target_user_id:
        bot_logger.warning(f"Manager {callback.from_user.id} tried to access ticket {ticket_id} belonging to {ticket.user_id} via target user {target_user_id}'s archive.")
        await callback.answer("Access to this ticket is restricted.", show_alert=True)
        return

    await state.update_data(last_user_archive_page=archive_page, viewing_target_user_id=target_user_id)
    content = ticket.content
    history_is_empty = not content
    current_page = 1

    if not content:
        ticket_text = strs(lang=lang).ticket_no_history
        keyboard = await get_ticket_history_inline_keyboard(
            lang=lang, ticket_id=ticket_id, page=current_page,
            viewer_id=callback.from_user.id,
            target_user_id=target_user_id,
            is_manager_view=True, ticket=ticket, history_is_empty=True,
            from_user_archive=True
        )
    else:
        ticket_text = await utils.make_up_ticket_page_text(
            page=current_page, content=content, ticket=ticket, extended_info=True, lang=lang
        )
        keyboard = await get_ticket_history_inline_keyboard(
            lang=lang, ticket_id=ticket_id, page=current_page,
            viewer_id=callback.from_user.id,
            target_user_id=target_user_id,
            is_manager_view=True, ticket=ticket,
            from_user_archive=True
        )
    try:
        await callback.message.edit_text(text=ticket_text, reply_markup=keyboard)
    except TelegramAPIError as e:
         if "message is not modified" not in str(e).lower():
             bot_logger.error(f"Error editing message in handle_user_archive_ticket_button_callback: {e}", exc_info=True)
    except Exception as e:
        bot_logger.error(f"Unexpected error editing message in handle_user_archive_ticket_button_callback: {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith(('user_archive_prev_btn', 'user_archive_next_btn')), filters.IsManagerOrAdmin())
async def handle_user_archive_page_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_archive page button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    action = data[0].split('_')[2]
    try:
        current_page_from_callback = int(data[1])
        target_user_id = int(data[2])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid page/user_id in user archive pagination callback: {callback.data}", exc_info=True)
        await callback.answer("Navigation error.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    user_data = await state.get_data()
    tickets = user_data.get('cached_user_specific_tickets')

    if tickets is None or user_data.get('viewing_target_user_id') != target_user_id:
        tickets = await db.tickets.get_all_by_id(user_id=target_user_id, is_manager=False)
        await state.update_data(cached_user_specific_tickets=tickets, viewing_target_user_id=target_user_id)

    if not tickets:
        await callback.answer(f"User {target_user_id} has no tickets.", show_alert=True)
        return

    max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
    page_to_show = current_page_from_callback

    if action == 'next':
        page_to_show = current_page_from_callback + 1 if current_page_from_callback < max_pages else 1
    elif action == 'prev':
        page_to_show = current_page_from_callback - 1 if current_page_from_callback > 1 else max_pages

    if page_to_show != current_page_from_callback or user_data.get('last_user_archive_page') != page_to_show:
        text = await make_up_tickets_info_page(page=page_to_show, tickets=tickets, is_manager_view=True, lang=lang)
        keyboard = await get_user_specific_archive_menu_inline_keyboard(
            lang=lang, tickets=tickets, page=page_to_show, target_user_id=target_user_id
        )
        try:
            await callback.message.edit_text(text=text, reply_markup=keyboard)
            await state.update_data(last_user_archive_page=page_to_show)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message (user archive pagination): {e}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message (user archive pagination): {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith('user_archive_back_to_info'), filters.IsManagerOrAdmin())
async def handle_user_archive_back_to_info_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_archive_back_to_info callback from user {callback.message.chat.id}')
    try:
        target_user_id = int(callback.data.split()[-1])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid user_id in user_archive_back_to_info callback: {callback.data}", exc_info=True)
        await callback.answer("Error returning.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    await state.update_data(cached_user_specific_tickets=None, viewing_target_user_id=None)

    target_user = await db.users.get_by_id(user_id=target_user_id)
    if not target_user:
        await callback.answer("Could not find user information.", show_alert=True)
        return

    current_user = await db.users.get_by_id(user_id=callback.message.chat.id)
    is_current_user_admin = current_user.status == 'admin' if current_user else False

    from handlers.private.managers.user_search import get_user_actions_inline_keyboard
    is_target_manager, info_text = await make_up_user_info(user=target_user, lang=lang)
    keyboard = await get_user_actions_inline_keyboard(
        lang=lang,
        user_id=target_user_id,
        ticket_id=target_user.current_ticket_id,
        user_is_manager=is_target_manager,
        is_user_admin=is_current_user_admin
    )
    try:
        await callback.message.edit_text(text=info_text, reply_markup=keyboard)
    except TelegramAPIError as e:
         if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Error editing message when returning to user info: {e}", exc_info=True)
            try:
                await callback.message.delete()
                await callback.message.answer(text=info_text, reply_markup=keyboard)
            except Exception as e2:
                 bot_logger.error(f"Error sending new message when returning to user info: {e2}", exc_info=True)
    except Exception as e:
        bot_logger.error(f"Unexpected error editing message when returning to user info: {e}", exc_info=True)
    await callback.answer()

# --- HISTORY HANDLERS ---

@ticket_router.callback_query(F.data.startswith(('history_prev_btn', 'history_next_btn')), filters.IsManagerOrAdmin())
async def handle_ticket_history_pagination_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_history pagination callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        action = data[0].split('_')[1]
        ticket_id = data[1]
        current_page_from_callback = int(data[2])
        viewer_id_str = data[3]
        viewer_id = int(viewer_id_str) if viewer_id_str != "None" else None
        is_manager_view = bool(int(data[4]))
        from_user_archive = bool(int(data[5]))
        target_user_id_str = data[6]
        target_user_id = int(target_user_id_str) if target_user_id_str != 'None' else None
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Error parsing callback_data for history pagination: {callback.data}, {e}", exc_info=True)
        await callback.answer("Pagination error.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)

    if not ticket or not ticket.content:
        await callback.answer(strs(lang=lang).ticket_no_history, show_alert=True)
        return

    max_pages = ceil(len(ticket.content) / utils.BATCH)
    page_to_show = current_page_from_callback

    if action == 'prev':
        page_to_show = current_page_from_callback - 1 if current_page_from_callback > 1 else max_pages
    else: # next
        page_to_show = current_page_from_callback + 1 if current_page_from_callback < max_pages else 1

    if page_to_show != current_page_from_callback:
        ticket_text = await make_up_ticket_page_text(
            page=page_to_show, content=ticket.content, ticket=ticket, extended_info=is_manager_view, lang=lang
        )
        keyboard = await get_ticket_history_inline_keyboard(
            lang=lang, ticket_id=ticket_id, page=page_to_show, viewer_id=viewer_id,
            is_manager_view=is_manager_view, ticket=ticket,
            from_user_archive=from_user_archive,
            target_user_id=target_user_id
        )
        try:
            await callback.message.edit_text(text=ticket_text, reply_markup=keyboard)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message (history pagination): {e}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message (history pagination): {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith('ticket_user_info'), filters.IsManagerOrAdmin())
async def handle_history_user_info_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_history user_info button callback from user {callback.message.chat.id}')
    try:
        target_user_id = int(callback.data.split()[1])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid user_id in ticket_user_info callback: {callback.data}", exc_info=True)
        await callback.answer("User data error.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    target_user = await db.users.get_by_id(user_id=target_user_id)
    if not target_user:
        await callback.answer("User not found.", show_alert=True)
        return

    current_user_who_is_viewing = await db.users.get_by_id(user_id=callback.message.chat.id)
    is_current_user_admin = current_user_who_is_viewing.status == 'admin' if current_user_who_is_viewing else False

    from handlers.private.managers.user_search import get_user_actions_inline_keyboard
    is_target_manager, info_text = await make_up_user_info(user=target_user, lang=lang)
    keyboard = await get_user_actions_inline_keyboard(
        lang=lang,
        user_id=target_user_id,
        ticket_id=target_user.current_ticket_id,
        user_is_manager=is_target_manager,
        is_user_admin=is_current_user_admin
    )
    try:
        await callback.message.edit_text(text=info_text, reply_markup=keyboard)
    except TelegramAPIError as e:
         if "message is not modified" not in str(e).lower():
             bot_logger.error(f"Error editing message showing user info from history: {e}", exc_info=True)
             try:
                 await callback.message.delete()
                 await callback.message.answer(text=info_text, reply_markup=keyboard)
             except Exception as e2:
                  bot_logger.error(f"Error sending new message showing user info from history: {e2}", exc_info=True)
    except Exception as e:
        bot_logger.error(f"Unexpected error editing message showing user info: {e}", exc_info=True)
    await callback.answer()

@ticket_router.callback_query(F.data.startswith('history_open_media_btn'), filters.IsManagerOrAdmin())
async def handle_history_open_media_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling history_open_media button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        ticket_id = data[1]
        history_page_from_callback = int(data[2])
    except (IndexError, ValueError) as e:
        bot_logger.error(f"Error parsing callback_data for history_open_media_btn: {callback.data}, {e}", exc_info=True)
        await callback.answer("Error opening media.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    user_data_from_state = await state.get_data()
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if not ticket:
        await callback.answer(strs(lang=lang).ticket_not_found, show_alert=True)
        return

    media_messages_info = await get_media_messages(lang=lang, page=history_page_from_callback, ticket=ticket)

    if not media_messages_info:
        await callback.answer(text=strs(lang=lang).ticket_no_media_on_page, show_alert=True)
        return

    try:
        media_messages_list = [msg.model_dump(mode='json') for msg in media_messages_info]
    except Exception as e:
        bot_logger.error(f"Error serializing media messages: {e}", exc_info=True)
        await callback.answer("Error preparing media.", show_alert=True)
        return

    await state.update_data(
        current_media_list=media_messages_list,
        current_media_index=0,
        media_history_page=history_page_from_callback,
        media_ticket_id=ticket_id,
        from_user_archive = user_data_from_state.get('from_user_archive', False), # Сохраняем/переносим флаги
        viewing_target_user_id = user_data_from_state.get('viewing_target_user_id', None)
    )

    media_count = len(media_messages_list)
    current_media_index = 0

    try:
        controls_keyboard = await create_media_controls_keyboard(
            lang=lang, current_index=current_media_index, total_count=media_count,
            ticket_id=ticket_id, history_page=history_page_from_callback
        )
        sent_media_msg = await send_media_from_info(
            client_bot=callback.bot, chat_id=callback.message.chat.id,
            message_info=media_messages_list[current_media_index],
            reply_markup=controls_keyboard
        )
        if sent_media_msg:
            await state.update_data(media_display_message_id=sent_media_msg.message_id)
            try: await callback.message.delete()
            except TelegramAPIError as e: bot_logger.warning(f"Could not delete history message: {e}")
            except Exception as e: bot_logger.error(f"Unexpected error deleting history message: {e}", exc_info=True)
        else:
            await callback.message.answer("Failed to display media.")
    except Exception as e:
        bot_logger.error(f"Error sending first media with controls: {e}", exc_info=True)
        await callback.message.answer("Failed to display media.")
    await callback.answer()


@ticket_router.callback_query(F.data.startswith('media_nav_'), filters.IsManagerOrAdmin())
async def handle_media_navigation_callback(callback: CallbackQuery, state: FSMContext):
    query_data = callback.data.split('_')
    action = query_data[2]
    lang = (await state.get_data()).get('lang', 'ru')

    try:
        ticket_id_from_callback = query_data[3]
        history_page_from_callback = int(query_data[4])
    except (IndexError, ValueError):
         bot_logger.error(f"Invalid data in media pagination callback: {callback.data}", exc_info=True)
         await callback.answer("Navigation error.", show_alert=True)
         return

    user_data = await state.get_data()
    media_display_message_id = user_data.get('media_display_message_id')

    if action == "close":
        if media_display_message_id:
            try: await callback.bot.delete_message(callback.message.chat.id, media_display_message_id)
            except TelegramAPIError as e: bot_logger.warning(f"Could not delete media message on close: {e}")
            except Exception as e: bot_logger.error(f"Unexpected error deleting media message on close: {e}", exc_info=True)

        ticket_id_for_return = user_data.get('media_ticket_id', ticket_id_from_callback)
        hist_page_to_return_to = user_data.get('media_history_page', history_page_from_callback)
        from_user_archive_flag_for_return = user_data.get('from_user_archive', False)
        target_user_id_for_return = user_data.get('viewing_target_user_id')


        await state.update_data( # Очищаем только состояние медиа просмотра
            current_media_list=None, current_media_index=None,
            media_display_message_id=None
            # media_history_page, media_ticket_id, from_user_archive, viewing_target_user_id остаются в state
            # для get_ticket_history_inline_keyboard
        )

        if ticket_id_for_return:
            ticket = await db.tickets.get_by_id(ticket_id=ticket_id_for_return)
            if ticket:
                content = ticket.content
                history_is_empty = not content
                max_hist_pages = ceil(len(content) / utils.BATCH) if content else 1
                if hist_page_to_return_to > max_hist_pages > 0 : hist_page_to_return_to = max_hist_pages
                if hist_page_to_return_to < 1: hist_page_to_return_to = 1

                ticket_text = await make_up_ticket_page_text(
                    page=hist_page_to_return_to, content=content, ticket=ticket, extended_info=True, lang=lang
                ) if content else strs(lang=lang).ticket_no_history

                keyboard = await get_ticket_history_inline_keyboard(
                    lang=lang, ticket_id=ticket_id_for_return, page=hist_page_to_return_to,
                    viewer_id=callback.from_user.id,
                    is_manager_view=True, ticket=ticket, history_is_empty=history_is_empty,
                    from_user_archive=from_user_archive_flag_for_return,
                    target_user_id=target_user_id_for_return
                )
                try:
                    await callback.message.answer(text=ticket_text, reply_markup=keyboard)
                except Exception as e_send:
                     bot_logger.error(f"Error sending history message after closing media: {e_send}", exc_info=True)
            else:
                 await callback.message.answer("Ticket not found. Returning to main menu...")
                 from handlers.utils import get_main_menu
                 main_menu_kb = await get_main_menu(lang=lang, user_id=callback.from_user.id)
                 await callback.message.answer(
                      text=strs(lang).manager_general_help,
                      reply_markup=main_menu_kb
                 )
        else:
            await callback.message.answer("State error (no ticket_id). Returning to main menu...")
            from handlers.utils import get_main_menu
            main_menu_kb = await get_main_menu(lang=lang, user_id=callback.from_user.id)
            await callback.message.answer(
                 text=strs(lang).manager_general_help,
                 reply_markup=main_menu_kb
            )
        await callback.answer()
        return

    media_list = user_data.get('current_media_list')
    current_index = user_data.get('current_media_index')

    if media_list is None or current_index is None or media_display_message_id is None:
        await callback.answer("Error: Media view state lost.", show_alert=True)
        if media_display_message_id:
            try: await callback.bot.delete_message(callback.message.chat.id, media_display_message_id)
            except: pass # Игнорируем ошибку, если сообщение уже удалено
        return

    media_count = len(media_list)
    if media_count == 0 : # Если список медиа пуст, хотя не должен быть здесь
        await callback.answer("No media to display.", show_alert=True)
        return
    if media_count == 1 and (action == "prev" or action == "next"): # Нечего переключать
        await callback.answer()
        return

    new_index = current_index
    if action == "prev": new_index = (current_index - 1 + media_count) % media_count
    elif action == "next": new_index = (current_index + 1) % media_count

    await state.update_data(current_media_index=new_index)

    new_controls_keyboard = await create_media_controls_keyboard(
        lang=lang, current_index=new_index, total_count=media_count,
        ticket_id=ticket_id_from_callback, history_page=history_page_from_callback
    )

    new_message_info_dict = media_list[new_index]
    media_type = None
    possible_media_keys = ['photo', 'video', 'audio', 'document', 'animation', 'voice', 'video_note', 'sticker']
    for key in possible_media_keys:
        if key in new_message_info_dict and new_message_info_dict[key]:
            media_type = key
            break

    can_edit_media = media_type in ['photo', 'video', 'audio', 'document', 'animation']
    new_sent_media_msg_id = None
    try:
        if can_edit_media:
             input_media = None
             file_id = None
             caption = new_message_info_dict.get('caption')
             if media_type == 'photo':
                 file_id = new_message_info_dict['photo'][-1]['file_id']
                 input_media = InputMediaPhoto(media=file_id, caption=caption)
             elif media_type == 'video':
                 file_id = new_message_info_dict['video']['file_id']
                 input_media = InputMediaVideo(media=file_id, caption=caption)
             elif media_type == 'audio':
                 file_id = new_message_info_dict['audio']['file_id']
                 input_media = InputMediaAudio(media=file_id, caption=caption)
             elif media_type == 'document':
                 file_id = new_message_info_dict['document']['file_id']
                 input_media = InputMediaDocument(media=file_id, caption=caption)

             if input_media:
                  edited_message = await callback.bot.edit_message_media(
                      media=input_media,
                      chat_id=callback.message.chat.id,
                      message_id=media_display_message_id,
                      reply_markup=new_controls_keyboard
                  )
                  new_sent_media_msg_id = edited_message.message_id
             else: raise ValueError(f"Could not create InputMedia for edit, type: {media_type}")
        else:
            raise ValueError(f"Media type '{media_type}' does not support editing with InputMedia. Deleting and resending.")
    except Exception as edit_error:
        bot_logger.warning(f"Could not edit media ({media_type}): {edit_error}. Deleting old and sending new.", exc_info=True)
        try: await callback.bot.delete_message(callback.message.chat.id, media_display_message_id)
        except Exception as delete_error: bot_logger.error(f"Could not delete old media message during pagination: {delete_error}", exc_info=True)

        new_sent_media_msg_obj = await send_media_from_info( # Переименована переменная
            client_bot=callback.bot, chat_id=callback.message.chat.id,
            message_info=new_message_info_dict, reply_markup=new_controls_keyboard
        )
        if new_sent_media_msg_obj: new_sent_media_msg_id = new_sent_media_msg_obj.message_id

    if new_sent_media_msg_id:
        await state.update_data(media_display_message_id=new_sent_media_msg_id)
    else:
        await state.update_data(media_display_message_id=None)
        try: # Если сообщение не отправилось, информируем пользователя
            await callback.message.answer("Failed to load next/previous media.")
        except Exception as e:
            bot_logger.error(f"Failed to notify user about media load failure: {e}", exc_info=True)
    await callback.answer()


@ticket_router.callback_query(F.data.startswith('history_back_to_manager_archive'), filters.IsManagerOrAdmin())
async def handle_history_back_to_manager_archive_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling history_back_to_manager_archive callback from user {callback.message.chat.id}')
    user_data = await state.get_data()
    page = user_data.get('last_archive_page', 1)
    lang = user_data.get('lang', 'ru')

    tickets = user_data.get('cached_closed_tickets')
    if tickets is None:
        tickets = await db.tickets.get_all_closed_tickets()
        await state.update_data(cached_closed_tickets=tickets)

    if tickets:
        max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
        if page < 1: page = 1
        if page > max_pages > 0 : page = max_pages

        text = await make_up_tickets_info_page(page=page, tickets=tickets, is_manager_view=True, lang=lang)
        keyboard = await get_archive_menu_inline_keyboard(lang=lang, tickets=tickets, page=page)
        try:
            await callback.message.edit_text(text=text, reply_markup=keyboard)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message when returning to general archive: {e}", exc_info=True)
                 try:
                     await callback.message.delete()
                     await callback.message.answer(text=text, reply_markup=keyboard)
                 except Exception as e2:
                      bot_logger.error(f"Error sending new message when returning to general archive: {e2}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message when returning to general archive: {e}", exc_info=True)
    else:
        await callback.answer(strs(lang=lang).ticket_empty, show_alert=True)
        from handlers.utils import get_main_menu
        main_menu_kb = await get_main_menu(lang=lang, user_id=callback.from_user.id)
        current_user = await db.users.get_by_id(user_id=callback.message.chat.id) # Переименовано, чтобы не конфликтовать
        help_text = strs(lang).admin_general_help if current_user and current_user.status == 'admin' else strs(lang).manager_general_help
        try: # Заменяем edit_text на delete + answer, так как get_main_menu возвращает ReplyKeyboard
            await callback.message.delete()
            await callback.message.answer(text=help_text, reply_markup=main_menu_kb)
        except Exception as e:
            bot_logger.error(f"Error replacing message for main menu (manager archive): {e}", exc_info=True)
    await callback.answer()


@ticket_router.callback_query(F.data.startswith('history_back_to_user_archive'), filters.IsManagerOrAdmin())
async def handle_history_back_to_user_archive_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling history_back_to_user_archive callback from user {callback.message.chat.id}')
    try:
        target_user_id = int(callback.data.split()[-1])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid user_id in history_back_to_user_archive callback: {callback.data}", exc_info=True)
        await callback.answer("Error returning.", show_alert=True)
        return

    user_data = await state.get_data()
    page = user_data.get('last_user_archive_page', 1)
    lang = user_data.get('lang', 'ru')
    tickets = user_data.get('cached_user_specific_tickets')

    if tickets is None or user_data.get('viewing_target_user_id') != target_user_id:
        tickets = await db.tickets.get_all_by_id(user_id=target_user_id, is_manager=False)
        await state.update_data(cached_user_specific_tickets=tickets, viewing_target_user_id=target_user_id)

    if tickets:
        max_pages = ceil(len(tickets) / utils.BATCH) if tickets else 1
        if page < 1: page = 1
        if page > max_pages > 0 : page = max_pages

        text = await make_up_tickets_info_page(page=page, tickets=tickets, is_manager_view=True, lang=lang)
        keyboard = await get_user_specific_archive_menu_inline_keyboard(
            lang=lang, tickets=tickets, page=page, target_user_id=target_user_id
        )
        try:
             await callback.message.edit_text(text=text, reply_markup=keyboard)
        except TelegramAPIError as e:
             if "message is not modified" not in str(e).lower():
                 bot_logger.error(f"Error editing message when returning to user archive: {e}", exc_info=True)
                 try:
                     await callback.message.delete()
                     await callback.message.answer(text=text, reply_markup=keyboard)
                 except Exception as e2:
                      bot_logger.error(f"Error sending new message when returning to user archive: {e2}", exc_info=True)
        except Exception as e:
            bot_logger.error(f"Unexpected error editing message when returning to user archive: {e}", exc_info=True)
    else:
        await callback.answer(f"User {target_user_id} has no tickets.", show_alert=True)
        # Если тикетов нет, возвращаемся к информации о пользователе
        original_callback_data = callback.data # Сохраняем, чтобы не потерять при изменении
        callback.data = f'user_archive_back_to_info {target_user_id}' # Имитируем нажатие
        await handle_user_archive_back_to_info_callback(callback, state)
        callback.data = original_callback_data # Восстанавливаем для корректного ответа на исходный callback
        return # Предотвращаем двойной callback.answer()
    await callback.answer()


@ticket_router.callback_query(F.data.startswith('ticket_delete'), filters.IsAdmin())
async def handle_delete_ticket_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_delete button callback from user {callback.message.chat.id}')
    try:
        ticket_id = callback.data.split()[1]
    except IndexError:
        bot_logger.error(f"Invalid ticket_id in ticket_delete callback: {callback.data}", exc_info=True)
        await callback.answer("Error deleting ticket.", show_alert=True)
        return

    lang = (await state.get_data()).get('lang', 'ru')
    ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
    if ticket:
        original_topic_id = ticket.topic_id
        try:
            await db.tickets.delete(ticket)
            if original_topic_id and cf.GROUP_CHAT_ID:
                try:
                    await callback.bot.delete_forum_topic(chat_id=cf.GROUP_CHAT_ID, message_thread_id=original_topic_id)
                    bot_logger.info(f"Topic {original_topic_id} deleted after ticket {ticket_id} deletion by admin {callback.from_user.id}")
                except TelegramAPIError as topic_del_e:
                    bot_logger.warning(f"Could not delete topic {original_topic_id} after deleting ticket {ticket_id}: {topic_del_e}")
                except Exception as topic_del_e:
                    bot_logger.error(f"Unexpected error deleting topic {original_topic_id}: {topic_del_e}", exc_info=True)
            await callback.answer("Ticket deleted from database.", show_alert=True)
            await handle_history_back_to_manager_archive_callback(callback, state)
        except Exception as e:
             bot_logger.error(f"Error deleting ticket {ticket_id}: {e}", exc_info=True)
             await callback.answer("Error deleting ticket.", show_alert=True)
    else:
        await callback.answer(strs(lang=lang).ticket_not_found, show_alert=True)


@ticket_router.callback_query(F.data == 'no_action', filters.IsManagerOrAdmin())
async def handle_no_action_callback(callback: CallbackQuery):
    """Handles callbacks with no action (e.g., page counters)."""
    await callback.answer()