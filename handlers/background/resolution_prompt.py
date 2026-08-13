from datetime import datetime, timedelta, timezone

from bot import bot
from database import db
from handlers.ticket_resolution import send_resolution_prompt
from utils.logger import background_logger


INACTIVITY_PERIOD = timedelta(hours=1)


def is_resolution_prompt_due(ticket, now: datetime) -> bool:
    if ticket.close_date or ticket.resolution_prompt_sent_at:
        return False
    activities = [value for value in (ticket.last_user_activity, ticket.last_modified, ticket.open_date) if value]
    last_activity = max(activities) if activities else None
    if not last_activity:
        return False
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone(timedelta(hours=3)))
    return last_activity.astimezone(timezone.utc) + INACTIVITY_PERIOD <= now.astimezone(timezone.utc)


async def resolution_prompt_check():
    now = datetime.now(timezone.utc)
    open_tickets = await db.tickets.get_all_opened() or []
    for ticket in open_tickets:
        if not is_resolution_prompt_due(ticket, now):
            continue
        try:
            if await send_resolution_prompt(bot, ticket):
                background_logger.info(f'Sent inactivity resolution prompt for Ticket {ticket.id}')
        except Exception as error:
            background_logger.error(
                f'Error sending inactivity resolution prompt for Ticket {ticket.id}: {error}',
                exc_info=True,
            )
