from . import *
import config as cf
from database import db
from utils.logger import bot_logger
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# __router__ !DO NOT DELETE!
general_router = Router()

# __buttons__ !DO NOT DELETE!
async def get_menu_reply_keyboard(user_id: int, lang: str) -> ReplyKeyboardMarkup:
    button_list = [
        [KeyboardButton(text=strs(lang=lang).opened_tickets_btn),
         KeyboardButton(text=strs(lang=lang).my_tickets_btn)],
        [KeyboardButton(text=strs(lang=lang).find_user_btn),
         KeyboardButton(text=strs(lang=lang).faq_btn)],
        [KeyboardButton(text=strs(lang=lang).choose_lang_btn)]
    ]

    if user_id in cf.admin_ids:
        button_list.append([KeyboardButton(text=strs(lang=lang).admin_mode_btn)], )

    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True)


# __chat__ !DO NOT DELETE!

@general_router.message(
    filters.Private(),
    ((F.text == '/to_admin') | (F.text.in_(admin_mode_btn)))
)
async def handle_to_admin_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /to_admin from user {message.chat.id}')
    if message.chat.id in cf.admin_ids:
        user = await db.users.get_by_id(user_id=message.chat.id)
        user.status = 'admin'
        await db.users.update(user=user)
        from ..admins.general import get_menu_reply_keyboard as admin_get_menu
        await message.answer(text=strs(lang=(await state.get_data())['lang']).manager_general_status_updated,
                             reply_markup=await admin_get_menu(lang=(await state.get_data())['lang']))
    else:
        await message.answer(text=strs(lang=(await state.get_data())['lang']).manager_general_status_updated_error)
