# Project
from bot import bot
import config as cf
from translations import strs
from database import db
from utils.logger import background_logger


async def notify_delete():
    background_logger.info('Notifying admin to delete tickets!')
    for admin_id in cf.admin_ids:
        admin = await db.users.get_by_id(user_id=admin_id)
        if admin.should_notificate:
            await bot.send_message(
                chat_id=admin_id,
                text=strs(lang=admin.lang).admin_delete_notification
            )
