from aiogram import Router
from .topics import topics_router

group_router = Router()
group_router.include_router(topics_router)

# Можно добавить middleware специфичные для группы, если нужно
# group_router.message.middleware(...)