# Third-party
import sqlalchemy.exc
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_

# Standard
from time import sleep
import traceback
from enum import Enum
from datetime import datetime, timezone, timedelta
import os
import shutil

# Project
import config as cf
from utils.logger import database_logger
from .models import Base, UserModel, TicketModel, PreferenceModel


# Enum for different types of database connections
class Type(Enum):
    SQLITE = f'sqlite:///{cf.project["storage"]}/support_bot.db'


class Database:
    # Private method to connect to the database
    def __connect_to_database(self, type_: Type):
        while True:
            database_logger.warning('Connecting to database...')
            try:
                # Creating a database engine
                self.engine = create_engine(type_.value)
                self.session_maker = sessionmaker(bind=self.engine)
                # Creating tables defined in 'Base' metadata
                Base.metadata.create_all(self.engine)

                # __connect_inner_classes__ !DO NOT DELETE!

                self.users = self.User(session_maker=self.session_maker)
                self.tickets = self.Ticket(session_maker=self.session_maker)
                self.preferences = self.Preference(session_maker=self.session_maker)

                database_logger.info('Connected to database')
                break
            except sqlalchemy.exc.OperationalError:
                # Handling database connection errors
                database_logger.error('Database error:\n' + traceback.format_exc())
                sleep(5.0)

    # Constructor to initialize the Database class
    def __init__(self, type_: Type):
        self.__connect_to_database(type_=type_)

    # __inner_classes__ !DO NOT DELETE!
    class User:
        def __init__(self, session_maker):
            self.session_maker = session_maker

        async def insert(self, user: UserModel):
            with self.session_maker() as session:
                session.add(user)
                session.commit()
                database_logger.info(f'UserModel {user.id} is created!')
                session.close()

        async def get_all(self) -> list[UserModel] | None:
            with self.session_maker() as session:
                data = session.query(UserModel).all()
                if data:
                    database_logger.info('Fetched all UserModels')
                    return data
                else:
                    database_logger.info('No UserModels in a database')
                    return None

        async def get_all_muted(self) -> list[UserModel] | None:
            with self.session_maker() as session:
                data = session.query(UserModel).filter(UserModel.mute_time.isnot(None)).all()
                if data:
                    database_logger.info('Fetched all muted UserModels')
                    return data
                else:
                    # Используем уровень DEBUG, который не будет отображаться при текущих настройках
                    database_logger.debug('No muted UserModels in a database')
                    return None

        async def get_all_managers(self) -> list[UserModel] | None:
            with self.session_maker() as session:
                data = session.query(UserModel).filter(
                    or_(UserModel.status == 'manager', UserModel.status == 'admin')
                ).all()
                if data:
                    database_logger.info('Fetched all manager and admin UserModels')
                    return data
                else:
                    database_logger.info('No manager or admin UserModels in a database')
                    return None

        async def get_all_admins(self) -> list[UserModel] | None:
            with self.session_maker() as session:
                data = session.query(UserModel).filter_by(status='admin').all()
                if data:
                    database_logger.info('Fetched all admin UserModels')
                    return data
                else:
                    database_logger.info('No admin UserModels in a database')
                    return None

        async def get_by_id(self, user_id: int) -> UserModel | None:
            with self.session_maker() as session:
                data = session.query(UserModel).filter_by(id=user_id).first()
                if data:
                    session.close()
                    return data
                else:
                    session.close()
                    return None

        async def get_by_tg_name(self, tg_name: str) -> UserModel | None:
            with self.session_maker() as session:
                data = session.query(UserModel).filter(UserModel.tg_name == tg_name).first()
                if not data:
                    data = session.query(UserModel).filter(UserModel.tg_name.ilike(f'%{tg_name}%')).first()
                if data:
                    database_logger.info(f'UserModel {tg_name} retrieved by tg_name')
                    session.close()
                    return data
                else:
                    database_logger.info(f'UserModel {tg_name} not found by tg_name')
                    session.close()
                    return None

        async def get_by_url_name(self, url_name: str) -> UserModel | None:
            with self.session_maker() as session:
                if not url_name:
                    database_logger.info('Attempted search by empty url_name')
                    return None
                data = session.query(UserModel).filter_by(url_name=url_name).first()
                if data:
                    database_logger.info(f'UserModel {url_name} retrieved by url_name')
                    session.close()
                    return data
                else:
                    database_logger.info(f'UserModel {url_name} not found by url_name')
                    session.close()
                    return None

        async def get_users_regs_in_period(self, days_ago: int | None = 7):
            with self.session_maker() as session:
                if days_ago:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days_ago)
                    data = session.query(UserModel).filter(
                        UserModel.registration_date.between(start_date, end_date)).all()
                    count = len(data) if data else 0
                    database_logger.info(f'{count} users registered in last {days_ago} days')
                    return count
                else:
                    count = session.query(UserModel).count()
                    database_logger.info(f'Total {count} users in database')
                    return count

        async def delete(self, user: UserModel):
            with self.session_maker() as session:
                session.query(UserModel).filter_by(id=user.id).delete()
                database_logger.warning(f'UserModel {user.id} is deleted!')
                session.commit()
                session.close()

        async def update(self, user: UserModel):
            with self.session_maker() as session:
                session.query(UserModel).filter_by(id=user.id).update({
                    'tg_name': user.tg_name,
                    'url_name': user.url_name,
                    'status': user.status,
                    'lang': user.lang,
                    'current_ticket_id': user.current_ticket_id,
                    'current_topic_id': user.current_topic_id,
                    'mute_time': user.mute_time,
                    'is_banned': user.is_banned,
                    'should_notificate': user.should_notificate
                })
                session.commit()
                session.close()

    class Ticket:
        def __init__(self, session_maker):
            self.session_maker = session_maker

        async def insert(self, ticket: TicketModel) -> int | None:
            with self.session_maker() as session:
                session.add(ticket)
                try:
                    session.flush()
                    ticket_id = ticket.id
                    session.commit()
                    database_logger.info(f'TicketModel {ticket_id} is created!')
                    session.close()
                    return ticket_id
                except sqlalchemy.exc.IntegrityError as e:
                    session.rollback()
                    database_logger.error(f"IntegrityError inserting TicketModel: {e}", exc_info=True)
                    session.close()
                    return None
                except Exception as e:
                    session.rollback()
                    database_logger.error(f"Error inserting TicketModel: {e}", exc_info=True)
                    session.close()
                    return None

        async def get_all(self) -> list[TicketModel] | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).order_by(desc(TicketModel.id)).all()
                if data:
                    database_logger.info('Fetched all TicketModels')
                    return data
                else:
                    database_logger.info('No TicketModels in a database')
                    return None

        async def get_by_id(self, ticket_id: str | int) -> TicketModel | None:
            if ticket_id is None or str(ticket_id).lower() == 'none':
                database_logger.info(f'Attempted get TicketModel with None ID')
                return None
            with self.session_maker() as session:
                try:
                    data = session.query(TicketModel).filter_by(id=int(ticket_id)).first()
                    if data:
                        session.close()
                        return data
                    else:
                        session.close()
                        return None
                except ValueError:
                    database_logger.error(f'Invalid ticket_id format: {ticket_id}')
                    session.close()
                    return None

        async def get_by_manager_id(self, manager_id: str | int) -> list[TicketModel] | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).filter_by(
                    manager_id=int(manager_id), close_date=None
                ).all()
                if data:
                    database_logger.info(f'Found {len(data)} active TicketModels for manager_id {manager_id}')
                    session.close()
                    return data
                else:
                    database_logger.info(f'No active TicketModels found for manager_id {manager_id}')
                    session.close()
                    return None

        async def get_by_topic_id(self, topic_id: int) -> TicketModel | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).filter_by(topic_id=topic_id).first()
                if data:
                    database_logger.info(f'TicketModel with topic_id {topic_id} retrieved')
                    session.close()
                    return data
                else:
                    database_logger.info(f'TicketModel with topic_id {topic_id} not found')
                    session.close()
                    return None

        async def get_all_opened(self) -> list[TicketModel] | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).filter_by(close_date=None).order_by(TicketModel.open_date).all()
                if data:
                    database_logger.info('Fetched all opened TicketModels')
                    return data
                else:
                    database_logger.info('No opened TicketModels in a database')
                    return None

        async def get_all_by_id(self, user_id: int, is_manager: bool) -> list[TicketModel] | None:
            with self.session_maker() as session:
                if is_manager:
                    data = session.query(TicketModel).filter_by(manager_id=user_id).order_by(desc(TicketModel.id)).all()
                else:
                    data = session.query(TicketModel).filter_by(user_id=user_id).order_by(desc(TicketModel.id)).all()
                if data:
                    role = "manager/admin" if is_manager else "user"
                    database_logger.info(f'Fetched all TicketModels with {role} id {user_id}')
                    return data
                else:
                    role = "manager/admin" if is_manager else "user"
                    database_logger.info(f'No TicketModels in a database with {role} id {user_id}')
                    return None

        async def get_all_closed_tickets(self) -> list[TicketModel] | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).filter(TicketModel.close_date.isnot(None)).order_by(
                    desc(TicketModel.id)).all()
                if data:
                    database_logger.info('Fetched all closed TicketModels')
                    return data
                else:
                    database_logger.info('No closed TicketModels in a database')
                    return None

        async def get_user_closed_tickets(self, user_id: int) -> list[TicketModel] | None:
            with self.session_maker() as session:
                data = session.query(TicketModel).filter(
                    TicketModel.user_id == user_id,
                    TicketModel.close_date.isnot(None)
                ).order_by(desc(TicketModel.id)).all()
                if data:
                    database_logger.info(f'Fetched closed TicketModels for user {user_id}')
                    return data
                else:
                    database_logger.info(f'No closed TicketModels for user {user_id}')
                    return None

        async def get_tickets_last_modified_ago(self, time_ago: int, is_hours=True) -> list[TicketModel] | None:
            with self.session_maker() as session:
                query = session.query(TicketModel)
                if is_hours:
                    query = query.filter_by(close_date=None)

                data = query.all()
                if data:
                    current_time_utc = datetime.now(timezone.utc)
                    result = []
                    for ticket in data:
                        if is_hours:  # Проверка для авто-закрытия по last_modified
                            compare_date = ticket.last_modified
                            if not compare_date: continue
                            if compare_date.tzinfo is None:
                                compare_date = compare_date.replace(tzinfo=timezone(timedelta(hours=3))).astimezone(
                                    timezone.utc)
                            elif compare_date.tzinfo != timezone.utc:
                                compare_date = compare_date.astimezone(timezone.utc)
                            delta = timedelta(hours=time_ago)
                            if (compare_date + delta) <= current_time_utc:
                                result.append(ticket)
                        else:  # Проверка для удаления старых тикетов по open_date
                            compare_date = ticket.open_date
                            if not compare_date: continue
                            if compare_date.tzinfo is None:
                                compare_date = compare_date.replace(tzinfo=timezone(timedelta(hours=3))).astimezone(
                                    timezone.utc)
                            elif compare_date.tzinfo != timezone.utc:
                                compare_date = compare_date.astimezone(timezone.utc)
                            delta = timedelta(days=30 * time_ago)  # Примерно 30 дней в месяце
                            if (compare_date + delta) <= current_time_utc:
                                result.append(ticket)

                    unit = "hours" if is_hours else "months"
                    database_logger.info(
                        f'Fetched {len(result)} tickets relevant for {unit} check (before {time_ago} {unit} ago)')
                    return result
                else:
                    database_logger.info('No matching TicketModels found for modification check')
                    return None

        async def get_tickets_count_in_period(self, days_ago: int | None = 7):
            with self.session_maker() as session:
                query = session.query(TicketModel)
                if days_ago:
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days_ago)
                    query = query.filter(TicketModel.open_date.between(start_date, end_date))
                count = query.count()
                period = f"last {days_ago} days" if days_ago else "all time"
                database_logger.info(f'Found {count} tickets created in {period}')
                return count

        async def get_medium_closing_time_in_period(self, ticket_id: int | None = None, days_ago: int | None = 7):
            with self.session_maker() as session:
                if ticket_id:
                    data = session.query(TicketModel).filter_by(id=ticket_id).first()
                    if data and data.open_date and data.close_date:
                        open_date = data.open_date
                        close_date = data.close_date
                        if not open_date.tzinfo: open_date = open_date.replace(tzinfo=timezone.utc)
                        if not close_date.tzinfo: close_date = close_date.replace(tzinfo=timezone.utc)
                        time_diff_seconds = (close_date.astimezone(timezone.utc) - open_date.astimezone(
                            timezone.utc)).total_seconds()
                        if time_diff_seconds < 0: time_diff_seconds = 0
                        time_hours = int(time_diff_seconds // 3600)
                        time_mins = int((time_diff_seconds % 3600) // 60)
                        return {'hours': time_hours, 'mins': time_mins}
                    else:
                        return {'hours': 0, 'mins': 0}
                else:
                    query = session.query(TicketModel).filter(TicketModel.close_date.isnot(None),
                                                              TicketModel.open_date.isnot(None))
                    if days_ago:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=days_ago)
                        query = query.filter(TicketModel.close_date.between(start_date, end_date))

                    data = query.all()
                    if data:
                        total_time_diff = 0
                        valid_tickets_count = 0
                        for ticket in data:
                            open_date = ticket.open_date
                            close_date = ticket.close_date
                            if not open_date.tzinfo: open_date = open_date.replace(tzinfo=timezone.utc)
                            if not close_date.tzinfo: close_date = close_date.replace(tzinfo=timezone.utc)
                            time_diff_seconds = (close_date.astimezone(timezone.utc) - open_date.astimezone(
                                timezone.utc)).total_seconds()
                            if time_diff_seconds >= 0:
                                total_time_diff += time_diff_seconds
                                valid_tickets_count += 1
                        if valid_tickets_count > 0:
                            average_time_diff = total_time_diff / valid_tickets_count
                            time_hours = int(average_time_diff // 3600)
                            time_mins = int((average_time_diff % 3600) // 60)
                            period = f"{days_ago} days" if days_ago else "all time"
                            database_logger.info(f'Avg closing time {period}: {time_hours}h {time_mins}m')
                            return {'hours': time_hours, 'mins': time_mins}
                    period = f"{days_ago} days" if days_ago else "all time"
                    database_logger.info(f'No closed tickets for avg time calc {period}')
                    return {'hours': 0, 'mins': 0}

        async def delete(self, ticket: TicketModel):
            with self.session_maker() as session:
                try:
                    destination = os.path.join(cf.project['storage'], str(ticket.id))
                    if os.path.exists(destination):
                        shutil.rmtree(destination)
                        database_logger.info(f'Removed media folder ticket {ticket.id}')
                except Exception as e:
                    database_logger.error(f'Error removing media folder T{ticket.id}: {e}')
                session.query(TicketModel).filter_by(id=ticket.id).delete()
                database_logger.warning(f'TicketModel {ticket.id} is deleted!')
                session.commit()
                session.close()

        async def update(self, ticket: TicketModel):
            with self.session_maker() as session:
                session.query(TicketModel).filter_by(id=ticket.id).update({
                    'user_id': ticket.user_id,
                    'manager_id': ticket.manager_id,
                    'topic_id': ticket.topic_id,
                    'topic_start_message_id': ticket.topic_start_message_id,
                    'username': ticket.username,
                    'user_email': ticket.user_email,
                    'tg_url': ticket.tg_url,
                    'open_date': ticket.open_date,
                    'close_date': ticket.close_date,
                    'last_modified': ticket.last_modified,
                    'content': ticket.content
                })
                session.commit()
                session.close()

    class Preference:
        def __init__(self, session_maker):
            self.session_maker = session_maker

        async def insert(self, preference: PreferenceModel):
            with self.session_maker() as session:
                session.add(preference)
                session.commit()
                database_logger.info(f'PreferenceModel {preference.key} is created!')
                session.close()

        async def get_all(self) -> list[PreferenceModel] | None:
            with self.session_maker() as session:
                data = session.query(PreferenceModel).all()
                if data:
                    database_logger.info('Fetched all PreferenceModels')
                    return data
                else:
                    database_logger.info('No PreferenceModels in a database')
                    return None

        async def get_by_key(self, key: str) -> PreferenceModel | None:
            with self.session_maker() as session:
                data = session.query(PreferenceModel).filter_by(key=key).first()
                if data:
                    session.close()
                    return data
                else:
                    database_logger.info(f'PreferenceModel {key} is not in database')
                    session.close()
                    return None

        async def delete(self, preference: PreferenceModel):
            with self.session_maker() as session:
                session.query(PreferenceModel).filter_by(key=preference.key).delete()
                database_logger.warning(f'PreferenceModel {preference.key} is deleted!')
                session.commit()
                session.close()

        async def update(self, preference: PreferenceModel):
            with self.session_maker() as session:
                session.query(PreferenceModel).filter_by(key=preference.key).update({
                    'key': preference.key,
                    'value': preference.value
                })
                session.commit()
                session.close()

        async def set_value(self, key: str, value: any):
            """Вставляет или обновляет значение по ключу."""
            with self.session_maker() as session:
                session.merge(PreferenceModel(key=key, value=value))
                session.commit()
                database_logger.info(f'PreferenceModel {key} was set/updated.')
                session.close()

        async def delete_by_key(self, key: str):
            """Удаляет запись по ключу."""
            with self.session_maker() as session:
                session.query(PreferenceModel).filter_by(key=key).delete(synchronize_session=False)
                database_logger.warning(f'PreferenceModel {key} is deleted!')
                session.commit()
                session.close()


db = Database(type_=Type.SQLITE)


async def generate_start_data():
    from translations import strs
    faq_key = 'faq'
    start_message_key = 'start_message'
    close_hours_key = 'close_hours'
    categories_key = 'categories'
    unk_message_key = 'unk_message'
    working_hours_key = 'working_hours'
    channel_info_key = 'channel_info'

    if not await db.preferences.get_by_key(key=faq_key):
        faq_pref = PreferenceModel(
            key=faq_key,
            value={'questions': [], 'footer_button': {'text': strs('ru').faq_not_found_btn, 'action': 'create_ticket'}}
        )
        await db.preferences.insert(preference=faq_pref)
        database_logger.info(f"Created default preference: {faq_key}")

    if not await db.preferences.get_by_key(key=start_message_key):
        start_info_pref = PreferenceModel(
            key=start_message_key,
            value={'message': strs(lang='ru').general_start}
        )
        await db.preferences.insert(preference=start_info_pref)
        database_logger.info(f"Created default preference: {start_message_key}")

    if not await db.preferences.get_by_key(key=close_hours_key):
        auto_close_pref = PreferenceModel(
            key=close_hours_key,
            value={'hours': 72}
        )
        await db.preferences.insert(preference=auto_close_pref)
        database_logger.info(f"Created default preference: {close_hours_key}")

    if not await db.preferences.get_by_key(key=unk_message_key):
        unk_message_pref = PreferenceModel(
            key=unk_message_key,
            value={'message': strs(lang='ru').unk_message}
        )
        await db.preferences.insert(preference=unk_message_pref)
        database_logger.info(f"Created default preference: {unk_message_key}")

    if not await db.preferences.get_by_key(key=categories_key):
        categories_pref = PreferenceModel(
            key=categories_key,
            value={'categories': ['Общие вопросы', 'Проблема с ботом', 'Другое']}
        )
        await db.preferences.insert(preference=categories_pref)
        database_logger.info(f"Created default preference: {categories_key}")

    if not await db.preferences.get_by_key(key=working_hours_key):
        default_working_hours = {
            "start_time": "09:00",
            "end_time": "18:00",
            "working_days": [0, 1, 2, 3, 4],
            "exceptions": []
        }
        working_hours_pref = PreferenceModel(
            key=working_hours_key,
            value=default_working_hours
        )
        await db.preferences.insert(preference=working_hours_pref)
        database_logger.info(f"Created default preference: {working_hours_key}")

    if not await db.preferences.get_by_key(key=channel_info_key):
        channel_info_pref = PreferenceModel(
            key=channel_info_key,
            value={
                'id': -100,
                'url': 'https://t.me/your_channel',
                'is_on': False,
                'button_name': 'Подписаться на канал'
            }
        )
        await db.preferences.insert(preference=channel_info_pref)
        database_logger.info(f"Created default preference: {channel_info_key}")