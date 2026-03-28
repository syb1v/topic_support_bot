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
from .channel import channel_router

user_router = Router()
sub_routers = [
    general_router, ticket_router,
    channel_router,
]

for router in sub_routers:
    router.message.middleware(middle.ChannelSubscriptionCheckMiddleware())
    router.callback_query.middleware(middle.ChannelSubscriptionCheckMiddleware())
    router.message.middleware(middle.InsertUserIfNotExistMiddleware())
    router.callback_query.middleware(middle.InsertUserIfNotExistMiddleware())
    router.message.middleware(middle.LanguageMiddleware())
    router.callback_query.middleware(middle.LanguageMiddleware())

user_router.include_routers(*sub_routers)
user_router.callback_query.middleware(middle.LanguageMiddleware())
user_router.message.middleware(middle.LanguageMiddleware())


@user_router.message(filters.IsUser(), F.text.in_(decline_btn))
async def process_decline_message(message: Message, state: FSMContext):
    from .general import get_menu_reply_keyboard
    lang = (await state.get_data()).get('lang', 'ru')
    menu_kb = await get_menu_reply_keyboard(lang=lang)
    await handle_decline_message(message, state, menu_kb)