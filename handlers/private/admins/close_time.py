from . import *
from database import db
from database.models import PreferenceModel
from utils.logger import bot_logger
from handlers.utils import get_main_menu, get_decline_reply_keyboard
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup

# __router__ !DO NOT DELETE!
close_time_router = Router()

# __states__ !DO NOT DELETE!
class ChangeCloseTimeStates(StatesGroup):
    get_hours = State()

# Обработчик для кнопки
@close_time_router.message(
    filters.Private(), filters.IsAdmin(),
    F.text.in_(change_close_time_btn)
)
async def handle_change_close_time_button(message: Message, state: FSMContext):
    """Обрабатывает кнопку изменения времени авто-закрытия."""
    await handle_change_close_time_command(message, state)

# Обработчик для команды
@close_time_router.message(
    filters.Private(), filters.IsAdmin(),
    Command('change_close_time')
)
async def handle_change_close_time_command(message: Message, state: FSMContext):
    """Обрабатывает команду изменения времени авто-закрытия."""
    bot_logger.info(f'Handling /change_close_time command or button from admin {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    close_pref = await db.preferences.get_by_key('close_hours')
    current_hours = close_pref.value.get('hours', 'N/A') if close_pref and isinstance(close_pref.value, dict) else 'N/A'

    text = strs(lang=lang).close_composite.format(current_hours) # Показываем текущее значение

    await message.answer(text=text)
    await message.answer(
        text=strs(lang=lang).admin_close_ask_time,
        reply_markup=await get_decline_reply_keyboard(lang=lang)
    )
    await state.set_state(ChangeCloseTimeStates.get_hours.state)


@close_time_router.message(ChangeCloseTimeStates.get_hours)
async def handle_get_hours_state(message: Message, state: FSMContext):
    """Обрабатывает ввод нового времени авто-закрытия."""
    bot_logger.info(f'Handling ChangeCloseTimeStates.get_hours from admin {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    if message.text and message.text.isdigit() and int(message.text) > 0:
        hours = int(message.text)
        close_pref = await db.preferences.get_by_key('close_hours')

        if not close_pref: # Создаем настройку, если её нет
            close_pref = PreferenceModel(key='close_hours', value={'hours': hours})
            await db.preferences.insert(preference=close_pref)
        else:
            # Проверяем структуру перед обновлением
            if not isinstance(close_pref.value, dict): close_pref.value = {}
            close_pref.value['hours'] = hours
            await db.preferences.update(preference=close_pref)

        await message.answer(
            text=strs(lang=lang).admin_close_updated,
            reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id) # Возвращаем главное меню админа
        )
        await state.clear()
    else:
        await message.answer(text=strs(lang=lang).admin_close_ask_time_error)