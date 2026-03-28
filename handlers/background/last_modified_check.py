# Standard
from datetime import datetime, timezone, timedelta

# Project
import config as cf
from database import db
from utils.logger import background_logger
from bot import bot
from translations import strs
from handlers.utils import get_main_menu


async def close_check():
    background_logger.warning('Starting close check for outdated tickets')
    close = await db.preferences.get_by_key('close_hours')
    if not close or 'hours' not in close.value:
        background_logger.error("Could not get 'close_hours' setting. Check cancelled.")
        return
    try:
        hours_ago = int(close.value.get('hours'))
    except (ValueError, TypeError):
        background_logger.error(f"Invalid 'close_hours': {close.value.get('hours')}. Check cancelled.")
        return

    more_than_hours_tickets = await db.tickets.get_tickets_last_modified_ago(time_ago=hours_ago, is_hours=True)

    if more_than_hours_tickets:
        current_date = datetime.now(timezone(timedelta(hours=3)))

        for ticket in more_than_hours_tickets:
            if ticket.close_date: continue # Пропускаем уже закрытые

            ticket.close_date = current_date
            ticket.last_modified = current_date
            ticket.manager_id = None
            original_topic_id = ticket.topic_id
            ticket.topic_id = None
            await db.tickets.update(ticket=ticket)

            if original_topic_id and cf.GROUP_CHAT_ID:
                 # ... (код закрытия топика) ...
                 try: await bot.delete_forum_topic(cf.GROUP_CHAT_ID, original_topic_id)
                 except Exception as e: background_logger.error(f"Fail close T{original_topic_id} auto: {e}")

            user_id = ticket.user_id
            user = await db.users.get_by_id(user_id=user_id)
            if user:
                user.current_ticket_id = None
                user.current_topic_id = None
                await db.users.update(user=user)

                try:
                    # Отправляем главное меню пользователю при авто-закрытии
                    user_main_menu = await get_main_menu(lang=user.lang, user_id=user.id)
                    await bot.send_message(
                        chat_id=user_id,
                        text=strs(lang=user.lang).last_modified_outdated(time=hours_ago),
                        reply_markup=user_main_menu # Отправляем стандартное меню
                    )
                except Exception as e:
                    background_logger.error(f"Error send auto-close notify U{user_id}: {e}")