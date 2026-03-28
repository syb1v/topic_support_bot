# Standard
from datetime import datetime, timezone, timedelta

# Project
from database import db
from utils.logger import background_logger


async def check_mute():
    muted_users = await db.users.get_all_muted()
    if muted_users:
        current_time_moscow = datetime.now(timezone(timedelta(hours=3)))

        for user in muted_users:
            mute_time_obj = user.mute_time

            # 1. Обработка, если mute_time хранится как строка
            if isinstance(mute_time_obj, str):
                try:
                    timestamp_main_part = mute_time_obj.split('.')[0]
                    naive_dt = datetime.strptime(timestamp_main_part, '%Y-%m-%d %H:%M:%S')
                    mute_time_obj = naive_dt.replace(tzinfo=timezone(timedelta(hours=3)))
                except ValueError as e:
                    background_logger.error(
                        f"Error converting mute_time string '{mute_time_obj}' to datetime for user {user.id}: {e}. Skipping user.")
                    continue

            # 2. Обработка, если mute_time является datetime объектом, но без информации о временной зоне (наивный)
            if isinstance(mute_time_obj, datetime) and not mute_time_obj.tzinfo:
                background_logger.info(
                    f"User {user.id} mute_time is naive datetime: {mute_time_obj}. Assuming Moscow time and making it aware.")
                mute_time_obj = mute_time_obj.replace(tzinfo=timezone(timedelta(hours=3)))
            elif mute_time_obj is not None and not isinstance(mute_time_obj, datetime):
                background_logger.warning(
                    f"User {user.id} mute_time is of unexpected type: {type(mute_time_obj)}. Value: {mute_time_obj}. Skipping.")
                continue

            # 3. Сравнение и обновление статуса
            if mute_time_obj:
                if mute_time_obj < current_time_moscow:
                    background_logger.info(f"Mute time for user {user.id} has passed ({mute_time_obj}). Unmuting.")
                    user.mute_time = None
                    await db.users.update(user=user)