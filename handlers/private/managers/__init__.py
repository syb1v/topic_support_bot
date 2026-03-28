# Third-party
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

# Project
import handlers.filters as filters
import handlers.middleware as middle
from translations import *
from handlers.utils import handle_decline_message


# Routers
from .general import general_router
from .tickets import ticket_router
from .user_search import search_router
from .restrictions import mute_router

manager_router = Router()
sub_routers = [
    general_router, ticket_router, mute_router,
    search_router
]

for router in sub_routers:
    router.message.middleware(middle.ChannelSubscriptionCheckMiddleware())
    router.callback_query.middleware(middle.ChannelSubscriptionCheckMiddleware())
    router.message.middleware(middle.InsertUserIfNotExistMiddleware())
    router.callback_query.middleware(middle.InsertUserIfNotExistMiddleware())
    router.message.middleware(middle.LanguageMiddleware())
    router.callback_query.middleware(middle.LanguageMiddleware())

manager_router.include_routers(*sub_routers)
manager_router.callback_query.middleware(middle.LanguageMiddleware())
manager_router.message.middleware(middle.LanguageMiddleware())


@manager_router.message(filters.IsManagerOrAdmin(), F.text.in_(decline_btn))
async def process_decline_message(message: Message, state: FSMContext):
    from .general import get_menu_reply_keyboard
    lang = (await state.get_data()).get('lang', 'ru')
    menu_kb = await get_menu_reply_keyboard(user_id=message.chat.id, lang=lang)
    await handle_decline_message(message, state, menu_kb)