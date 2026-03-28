from . import *
from database import db
from utils.logger import bot_logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup

# __router__ !DO NOT DELETE!
categories_router = Router()

# __states__ !DO NOT DELETE!
class CategoriesStates(StatesGroup):
    manage_category = State()
    create_category_name = State()
    update_category_name = State()


# __buttons__ !DO NOT DELETE!

# __chat__ !DO NOT DELETE!
@categories_router.message(
    filters.Private(), filters.IsAdmin(),
    (F.text == '/manage_category'))
async def handle_manage_category_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /manage_category from user {message.chat.id}')
    categories = (await db.preferences.get_by_key('categories')).value['categories']
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=categories[i], callback_data=f'manage_category {i}')] for i in range(len(categories))] + 
                                                    [[InlineKeyboardButton(text=strs(lang=(await state.get_data())['lang']).add_btn, callback_data='add_category')]])

    await message.answer(strs(lang=(await state.get_data())['lang']).admin_choose_category, reply_markup=keyboard)


@categories_router.callback_query(F.data.startswith('manage_category'))
async def manage_category_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling command manage_category_callback from user {callback.message.chat.id}')
    
    categories = (await db.preferences.get_by_key('categories')).value['categories']
    category_id = int(callback.data.split(' ')[1])

    category_name = categories[category_id]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=strs(lang=(await state.get_data())['lang']).remove_btn, callback_data=f'remove_category {category_id}')],
        [InlineKeyboardButton(text=strs(lang=(await state.get_data())['lang']).rename_btn, callback_data=f'rename_category {category_id}')],
        [InlineKeyboardButton(text=strs(lang=(await state.get_data())['lang']).back_btn, callback_data=f'back_to_category_menu {category_id}')]
    ])

    await callback.message.edit_text(text=strs(lang=(await state.get_data())['lang']).admin_manage_category_composite.format(category_name),
                                     reply_markup=keyboard)
    await callback.answer()


@categories_router.callback_query(F.data.startswith('back_to_category_menu'))
async def back_to_category_menu_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling command back_to_category_menu from user {callback.message.chat.id}')
    from .faq import get_faq_menu_inline_keyboard
    category_id = int(callback.data.split(' ')[1].strip())

    await callback.message.edit_text(strs(lang=(await state.get_data())['lang']).faq_questions,
                                     reply_markup=await get_faq_menu_inline_keyboard(lang=(await state.get_data())['lang'], is_admin=True, category_id=category_id))


@categories_router.callback_query(F.data.startswith('add_category'))
async def add_category_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling command add_category from user {callback.message.chat.id}')
    from handlers.utils import get_decline_reply_keyboard

    await callback.message.delete()
    await callback.message.answer(text=strs(lang=(await state.get_data())['lang']).admin_create_category, reply_markup=await get_decline_reply_keyboard(lang=(await state.get_data())['lang']))
    await state.set_state(CategoriesStates.create_category_name)
    await callback.answer()


@categories_router.message(CategoriesStates.create_category_name)
async def add_category_message(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command add_category from user {message.chat.id}')
    from .general import get_menu_reply_keyboard

    categories = await db.preferences.get_by_key('categories')
    categories.value['categories'].append(message.text.strip())
    await db.preferences.update(categories)
    await message.answer(text=strs(lang=(await state.get_data())['lang']).admin_create_category_success.format(message.text.strip()), reply_markup=await get_menu_reply_keyboard(lang=(await state.get_data())['lang']))
    await state.clear()


@categories_router.callback_query(F.data.startswith('remove_category'))
async def remove_category_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling command remove_category_callback from user {callback.message.chat.id}')
    category_id = int(callback.data.split(' ')[1].strip())

    categories = await db.preferences.get_by_key('categories')
    categories.value['categories'].pop(category_id)
    await db.preferences.update(categories)

    faqs = await db.preferences.get_by_key(key='faq')
    if faqs.value.get('questions'):
        for question in range(len(faqs.value.get('questions'))):
            if faqs.value.get('questions')[question].get('category') == category_id:
                faqs.value.get('questions').pop(question)

    await db.preferences.update(faqs)   
    await state.clear()
    await callback.message.edit_text(text=strs(lang='ru').admin_delete_category, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=strs(lang=(await state.get_data())['lang']).back_btn, callback_data='show_faq_main')]
    ]))


@categories_router.callback_query(F.data.startswith('rename_category'))
async def rename_category_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling command rename_category_callback from user {callback.message.chat.id}')
    category_id = int(callback.data.split(' ')[1].strip())

    await callback.message.delete()
    await callback.message.answer(strs(lang=(await state.get_data())['lang']).admin_create_category)
    await state.set_state(CategoriesStates.update_category_name)
    await state.set_data({'category_id': category_id})


@categories_router.message(CategoriesStates.update_category_name)
async def rename_category_message(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command rename_category_message from user {message.chat.id}')

    categories = await db.preferences.get_by_key('categories')
    category_id = int((await state.get_data())['category_id'])

    categories.value['categories'][category_id] = message.text.strip()
    await db.preferences.update(categories)

    await message.answer(strs(lang=(await state.get_data())['lang']).admin_rename_category_success.format(message.text.strip()))
    await state.clear()
