# Third-party
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

# Project
import handlers.filters as filters
import handlers.middleware as middle
from translations import *
from handlers.utils import handle_decline_message, get_main_menu

# Routers
from .general import general_router
from .mailing import mailing_router
from .faq import faq_router
from .start_msg import start_msg_router
from .delete_tickets import delete_tickets_router
from .unk_msg import unk_msg_router
from .categories_manage import categories_router
from .close_time import close_time_router
from .working_hours import working_hours_router
from .subscription import subs_router

admin_router = Router()
sub_routers = [
    general_router, faq_router, mailing_router,
    start_msg_router,
    delete_tickets_router,
    categories_router, unk_msg_router,
    close_time_router,
    working_hours_router,
    subs_router,
]

for router in sub_routers:
    router.message.middleware(middle.InsertUserIfNotExistMiddleware())
    router.message.middleware(middle.LanguageMiddleware())
    router.callback_query.middleware(middle.InsertUserIfNotExistMiddleware())
    router.callback_query.middleware(middle.LanguageMiddleware())

admin_router.include_routers(*sub_routers)

# --- Обработчик отмены ---
@admin_router.message(filters.IsAdmin(), F.text.in_(decline_btn))
async def process_decline_message(message: Message, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    menu_kb = await get_main_menu(lang=lang, user_id=message.chat.id)
    await handle_decline_message(message, state, menu_kb)