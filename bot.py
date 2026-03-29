# Third-party
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

# Project
import config as cf

# Подготовка сессии с прокси, если он задан и корректен
proxy_url = cf.bot.get('proxy')
session = None
if proxy_url:
    proxy_url = proxy_url.strip()
    if proxy_url.startswith(('http://', 'https://', 'socks5://')):
        session = AiohttpSession(proxy=proxy_url)

bot = Bot(
    token=cf.bot['token'],
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dispatcher = Dispatcher()