from . import *
from database import db, PreferenceModel
from utils.logger import bot_logger
from handlers.utils import get_decline_reply_keyboard, get_main_menu
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# __router__ !DO NOT DELETE!
subs_router = Router()


# __states__ !DO NOT DELETE!
class ChangeChannelInfoStates(StatesGroup):
    get_url = State()
    get_id = State()


class ChangeButtonNameStates(StatesGroup):
    get_button_name = State()


# --- Functions for Keyboard Generation ---
async def get_sub_menu_inline_keyboard(lang: str, is_on: bool) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для управления подпиской."""
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).change_channel_info_btn, callback_data='channel_change_btn')],
        [InlineKeyboardButton(text=strs(lang=lang).change_channel_button_name_btn,
                              callback_data='chnl_cng_btn_name_btn')]
    ]
    if not is_on:
        button_list.append([InlineKeyboardButton(text=strs(lang=lang).make_subscription_necessary_btn,
                                                 callback_data='channel_turn_btn on')])
    else:
        button_list.append([InlineKeyboardButton(text=strs(lang=lang).make_subscription_unnecessary_btn,
                                                 callback_data='channel_turn_btn off')])

    button_list.append([InlineKeyboardButton(text=strs(lang=lang).remove_menu_btn, callback_data='delete_btn')])
    return InlineKeyboardMarkup(inline_keyboard=button_list)


# --- Callback Handlers ---
@subs_router.callback_query(F.data == 'delete_btn')
async def handle_delete_menu_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        bot_logger.warning(f"Could not delete message on admin menu close: {e}")
    await callback.answer()


@subs_router.callback_query(F.data == 'channel_change_btn')
async def handle_change_button_callback(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(text=strs(lang=lang).admin_channel_ask_channel_url,
                                  reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(ChangeChannelInfoStates.get_url)
    await callback.answer()


@subs_router.callback_query(F.data == 'chnl_cng_btn_name_btn')
async def handle_change_channel_button_name_button_callback(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(
        text=strs(lang=lang).admin_channel_ask_button_name,
        reply_markup=await get_decline_reply_keyboard(lang=lang)
    )
    await state.set_state(ChangeButtonNameStates.get_button_name)
    await callback.answer()


@subs_router.callback_query(F.data.startswith('channel_turn_btn'))
async def handle_turn_button_callback(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    action = callback.data.split()[-1]
    is_on = True if action == 'on' else False

    channel_info = await db.preferences.get_by_key(key='channel_info')
    if not channel_info:
        channel_info = PreferenceModel(key='channel_info', value={})
        await db.preferences.insert(channel_info)
        channel_info = await db.preferences.get_by_key('channel_info')

    if not isinstance(channel_info.value, dict): channel_info.value = {}
    channel_info.value['is_on'] = is_on
    await db.preferences.update(preference=channel_info)

    id_ = channel_info.value.get('id', 'N/A')
    url = channel_info.value.get('url', 'N/A')
    button_name = channel_info.value.get('button_name', 'N/A')

    await callback.message.edit_text(
        text=strs(lang=lang).admin_channel_info(id_=id_, url=url, button_name=button_name),
        reply_markup=await get_sub_menu_inline_keyboard(lang=lang, is_on=is_on)
    )
    text = strs(lang=lang).admin_channel_on if is_on else strs(lang=lang).admin_channel_off
    await callback.answer(text=text, show_alert=True)


# --- Command and State Handlers ---
@subs_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/change_channel') | F.text.in_(change_subscription_channel_btn))
)
async def handle_change_channel_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /change_channel from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    channel_info_pref = await db.preferences.get_by_key('channel_info')

    channel_info = channel_info_pref.value if channel_info_pref and isinstance(channel_info_pref.value, dict) else {}
    id_ = channel_info.get('id', 'N/A')
    url = channel_info.get('url', 'N/A')
    is_on = channel_info.get('is_on', False)
    button_name = channel_info.get('button_name', 'Подписаться')

    await message.answer(
        text=strs(lang=lang).admin_channel_info(id_=id_, url=url, button_name=button_name),
        reply_markup=await get_sub_menu_inline_keyboard(lang=lang, is_on=is_on)
    )


@subs_router.message(ChangeChannelInfoStates.get_url)
async def handle_get_channel_url_state(message: Message, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    url = message.text
    if message.entities and any(e.type in ['url', 'text_link'] for e in message.entities):
        await message.answer(text=strs(lang=lang).admin_channel_ask_channel_id)
        await state.update_data({'url': url})
        await state.set_state(ChangeChannelInfoStates.get_id)
    else:
        await message.answer(text=strs(lang=lang).admin_channel_ask_channel_url_error)


@subs_router.message(ChangeChannelInfoStates.get_id)
async def handle_get_channel_id_state(message: Message, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        data = await state.get_data()
        url = data['url']

        channel_info = await db.preferences.get_by_key('channel_info')
        if not channel_info:
            channel_info = PreferenceModel(key='channel_info', value={})
            await db.preferences.insert(channel_info)
            channel_info = await db.preferences.get_by_key('channel_info')

        if not isinstance(channel_info.value, dict): channel_info.value = {}

        channel_info.value['id'] = channel_id
        channel_info.value['url'] = url
        await db.preferences.update(preference=channel_info)

        await message.answer(
            text=strs(lang=lang).admin_channel_updated,
            reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id)
        )
        await state.clear()
    else:
        await message.answer(text=strs(lang=lang).admin_channel_ask_channel_id_error)


@subs_router.message(ChangeButtonNameStates.get_button_name)
async def handle_get_button_name_state(message: Message, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    button_name = message.text
    if button_name and 0 < len(button_name) < 30:
        channel_info = await db.preferences.get_by_key('channel_info')
        if not channel_info:
            channel_info = PreferenceModel(key='channel_info', value={})
            await db.preferences.insert(channel_info)
            channel_info = await db.preferences.get_by_key('channel_info')

        if not isinstance(channel_info.value, dict): channel_info.value = {}

        channel_info.value['button_name'] = button_name
        await db.preferences.update(channel_info)

        await message.answer(
            text=strs(lang=lang).admin_channel_button_name_updated,
            reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id)
        )
        await state.clear()
    else:
        await message.answer(text=strs(lang=lang).admin_channel_ask_button_name_error)