# Third-party
from sqlalchemy import *
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import PickleType

# Standard
from uuid import uuid4

# Project
from translations import Language

class Base(DeclarativeBase):
    pass

def get_uuid() -> str:
    return str(uuid4())[:10]


# WHEN CHANGING CURRENT MODELS DON'T FORGET TO MODIFY update() METHOD IN database.py
class UserModel(Base):
    __tablename__ = 'Users'
    id = Column(BigInteger, primary_key=True)
    tg_name = Column(String)
    url_name = Column(String, nullable=True)
    status = Column(String) # 'user', 'manager', 'admin'
    lang = Column(String, default=Language.RU.value)
    registration_date = Column(DateTime)
    current_ticket_id = Column(String, default='') # ID тикета (может быть устаревшим, лучше ориентироваться на topic_id)
    current_topic_id = Column(Integer, default=None, nullable=True) # ID активного топика пользователя
    mute_time = Column(DateTime, default=None, nullable=True)
    is_banned = Column(Boolean, default=False)
    should_notificate = Column(Boolean, default=True)


class TicketModel(Base):
    __tablename__ = 'Tickets'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    manager_id = Column(BigInteger, default=None, nullable=True) # ID последнего ответившего менеджера (для истории)
    topic_id = Column(Integer, default=None, nullable=True) # ID топика в супергруппе
    topic_start_message_id = Column(Integer, default=None, nullable=True) # ID первого сообщения бота в топике (для ссылки)
    username = Column(String)
    user_email = Column(String, default=None, nullable=True)
    tg_url = Column(String, nullable=True)
    open_date = Column(DateTime)
    last_modified = Column(DateTime)
    close_date = Column(DateTime, default=None, nullable=True)
    content = Column(PickleType, default=[])


class PreferenceModel(Base):
    __tablename__ = 'Preferences'
    key = Column(String, primary_key=True)
    value = Column(PickleType, default={})