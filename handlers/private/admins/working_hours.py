from database import db
from utils.logger import bot_logger
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import re
from datetime import datetime, time, timezone, timedelta

# Проектные импорты
from . import *
from handlers.utils import get_decline_reply_keyboard, get_main_menu
from database import PreferenceModel
from translations import working_hours_btn, decline_btn

# --- Роутер ---
working_hours_router = Router()

# --- Состояния FSM ---
class WorkingHoursStates(StatesGroup):
    get_hours = State()
    get_days = State()
    get_exceptions = State()

# --- Клавиатуры ---
# Дни недели для клавиатуры и отображения
DAYS_OF_WEEK = {
    0: {"ru": strs("ru").monday, "en": strs("en").monday},
    1: {"ru": strs("ru").tuesday, "en": strs("en").tuesday},
    2: {"ru": strs("ru").wednesday, "en": strs("en").wednesday},
    3: {"ru": strs("ru").thursday, "en": strs("en").thursday},
    4: {"ru": strs("ru").friday, "en": strs("en").friday},
    5: {"ru": strs("ru").saturday, "en": strs("en").saturday},
    6: {"ru": strs("ru").sunday, "en": strs("en").sunday},
}

async def get_working_days_keyboard(lang: str, selected_days: list[int] | None = None) -> InlineKeyboardMarkup:
    """Генерирует Inline клавиатуру для выбора рабочих дней."""
    if selected_days is None:
        selected_days = []
    buttons = []
    row = []
    for i in range(7):
        day_name = DAYS_OF_WEEK[i].get(lang, DAYS_OF_WEEK[i]['ru']) # Получаем название дня
        text = f"✅ {day_name}" if i in selected_days else day_name
        row.append(InlineKeyboardButton(text=text, callback_data=f"wh_day_{i}"))
        if len(row) == 3: # По 3 кнопки в ряд
            buttons.append(row)
            row = []
    if row: # Добавляем оставшиеся кнопки
        buttons.append(row)

    # Кнопка "Далее"
    buttons.append([InlineKeyboardButton(text=strs(lang).next_btn, callback_data="wh_days_next")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def get_skip_exceptions_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """ Клавиатура с кнопками 'Пропустить' и 'Отмена' для ввода исключений """
    button_list = [
        [KeyboardButton(text=strs(lang).skip_btn)],
        [KeyboardButton(text=strs(lang).decline_btn)],
    ]
    return ReplyKeyboardMarkup(keyboard=button_list, resize_keyboard=True, one_time_keyboard=True)


# --- Вспомогательные функции ---
def format_current_settings(lang: str, settings: dict | None) -> str:
    """Форматирует текущие настройки графика для вывода."""
    if not settings or not isinstance(settings, dict):
        return strs(lang).no_settings_found

    text_parts = [strs(lang).current_working_hours_info]
    start_time = settings.get("start_time")
    end_time = settings.get("end_time")
    working_days_indices = settings.get("working_days", [])
    exceptions = settings.get("exceptions", [])

    if start_time and end_time:
        text_parts.append(strs(lang).working_hours_set.format(
            start_time=start_time, end_time=end_time
        ))

    if working_days_indices:
        # Используем полный цикл для получения локализованных имен
        days_str_list = []
        for d in sorted(working_days_indices):
             day_info = DAYS_OF_WEEK.get(d)
             if day_info:
                 days_str_list.append(day_info.get(lang, day_info.get('ru', '?'))) # Fallback на '?'
             else:
                 days_str_list.append('?') # Fallback, если индекс некорректен
        days_str = ", ".join(days_str_list)
        text_parts.append(strs(lang).working_days_set.format(days=days_str))
    else:
         text_parts.append(strs(lang).working_days_set.format(days=strs(lang).not_set)) # Используем перевод

    if exceptions:
        exceptions_str = ", ".join(exceptions)
        text_parts.append(strs(lang).exceptions_set.format(dates=exceptions_str))
    else:
        text_parts.append(strs(lang).exceptions_set.format(dates=strs(lang).none)) # Используем перевод

    return "\n".join(text_parts) if len(text_parts) > 1 else strs(lang).no_settings_found


# --- ИСПРАВЛЕНИЕ: Добавлен параметр lang ---
def is_working_time(settings: dict | None, lang: str = 'ru') -> tuple[bool, str]:
    """
    Проверяет, является ли текущее время рабочим согласно настройкам.
    Возвращает кортеж: (True/False - рабочее ли время, Строка с графиком для отображения).
    """
    # lang = 'ru' # Убрана жесткая привязка к русскому языку
    default_schedule_text = strs(lang).schedule_not_set # Используем переданный lang

    if not settings or not isinstance(settings, dict):
        return True, default_schedule_text # Возвращаем текст по умолчанию на нужном языке

    try:
        start_time_str = settings.get("start_time")
        end_time_str = settings.get("end_time")
        working_days_indices = settings.get("working_days", [])
        exceptions = settings.get("exceptions", [])

        # Формируем строку с графиком для отображения (даже если настройки неполные)
        schedule_display_text = default_schedule_text
        if start_time_str and end_time_str and working_days_indices:
             days_str_list = []
             for d in sorted(working_days_indices):
                  day_info = DAYS_OF_WEEK.get(d)
                  if day_info:
                      # Используем переданный lang
                      days_str_list.append(day_info.get(lang, day_info.get('ru', '?')))
                  else:
                      days_str_list.append('?')
             days_str = ", ".join(days_str_list)
             # Используем переданный lang
             schedule_display_text = strs(lang).working_hours_display.format(
                 days_str=days_str, start_time=start_time_str, end_time=end_time_str
             )
        elif start_time_str and end_time_str: # Если есть только время
             # Используем переданный lang
             schedule_display_text = strs(lang).working_hours_set.format(start_time=start_time_str, end_time=end_time_str)


        # Если не все настройки заданы, считаем время рабочим
        if not start_time_str or not end_time_str or not working_days_indices:
             return True, schedule_display_text

        # Получаем текущее время в МСК (логика остается прежней)
        msk_tz = timezone(timedelta(hours=3))
        now_msk = datetime.now(msk_tz)
        current_date_str = now_msk.strftime('%d.%m.%Y')
        current_weekday = now_msk.weekday() # 0 = Пн, 6 = Вс
        current_time_obj = now_msk.time()

        # 1. Проверка на дату-исключение
        if current_date_str in exceptions:
            return False, schedule_display_text

        # 2. Проверка на рабочий день недели
        if current_weekday not in working_days_indices:
            return False, schedule_display_text

        # 3. Проверка времени
        start_time_obj = time.fromisoformat(start_time_str)
        end_time_obj = time.fromisoformat(end_time_str)

        is_working = start_time_obj <= current_time_obj < end_time_obj

        return is_working, schedule_display_text

    except Exception as e:
        bot_logger.error(f"Error checking working time: {e}. Settings: {settings}", exc_info=True)
        return True, default_schedule_text


# --- Основная логика входа в настройку графика ---
async def _start_working_hours_setup_logic(message: Message, state: FSMContext):
    user_id = message.from_user.id
    bot_logger.info(f"Admin {user_id} started working hours setup (via button or command).")
    lang = (await state.get_data()).get('lang', 'ru')

    pref = await db.preferences.get_by_key("working_hours")
    current_settings_text = format_current_settings(lang, pref.value if pref else None)
    await message.answer(current_settings_text)

    await message.answer(
        strs(lang).ask_working_hours,
        reply_markup=await get_decline_reply_keyboard(lang)
    )
    await state.set_state(WorkingHoursStates.get_hours)

# --- ОБНОВЛЕННЫЕ ОБРАБОТЧИКИ ---

# Обработчик для КНОПКИ
@working_hours_router.message(
    filters.Private(),
    filters.IsAdmin(),
    F.text.in_(working_hours_btn) # Фильтр по тексту кнопки
)
async def start_working_hours_setup_button(message: Message, state: FSMContext):
    await _start_working_hours_setup_logic(message, state)

# Обработчик для КОМАНДЫ
@working_hours_router.message(
    filters.Private(),
    filters.IsAdmin(),
    Command("working_hours") # Фильтр по команде
)
async def start_working_hours_setup_command(message: Message, state: FSMContext):
    await _start_working_hours_setup_logic(message, state)


# Получение времени работы
@working_hours_router.message(WorkingHoursStates.get_hours)
async def get_working_hours(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = (await state.get_data()).get('lang', 'ru')
    time_pattern = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)\s*-\s*([01]\d|2[0-3]):([0-5]\d)$")
    match = time_pattern.match(message.text)

    if match:
        start_time_str = f"{match.group(1)}:{match.group(2)}"
        end_time_str = f"{match.group(3)}:{match.group(4)}"
        # Дополнительная проверка: время начала не должно быть позже времени конца
        try:
            start_t = time.fromisoformat(start_time_str)
            end_t = time.fromisoformat(end_time_str)
            if start_t >= end_t:
                 raise ValueError("Start time >= end time")
        except ValueError:
             bot_logger.warning(f"Admin {user_id} invalid time range: {start_time_str} - {end_time_str}")
             await message.answer(
                 "<b>Ошибка:</b> Время начала должно быть раньше времени окончания.",
                 reply_markup=await get_decline_reply_keyboard(lang)
             )
             return

        bot_logger.info(f"Admin {user_id} provided working hours: {start_time_str} - {end_time_str}")
        await state.update_data(start_time=start_time_str, end_time=end_time_str, selected_days=[])

        keyboard = await get_working_days_keyboard(lang, [])
        await message.answer(
            strs(lang).ask_working_days,
            reply_markup=keyboard
        )
        await state.set_state(WorkingHoursStates.get_days)
    else:
        bot_logger.warning(f"Admin {user_id} invalid time format: {message.text}")
        await message.answer(
            strs(lang).ask_working_hours_error,
            reply_markup=await get_decline_reply_keyboard(lang)
        )

# Обработка нажатия на день недели
@working_hours_router.callback_query(WorkingHoursStates.get_days, F.data.startswith("wh_day_"))
async def toggle_working_day(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = (await state.get_data()).get('lang', 'ru')
    try:
        day_index = int(callback.data.split("_")[-1])
        if not (0 <= day_index <= 6): raise ValueError("Invalid day index")
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid callback data for day toggle: {callback.data}")
        await callback.answer("Ошибка выбора дня", show_alert=True)
        return

    data = await state.get_data()
    selected_days = data.get("selected_days", [])

    if day_index in selected_days:
        selected_days.remove(day_index)
        bot_logger.info(f"Admin {user_id} deselected day {day_index}")
    else:
        selected_days.append(day_index)
        bot_logger.info(f"Admin {user_id} selected day {day_index}")

    selected_days.sort()
    await state.update_data(selected_days=selected_days)

    new_keyboard = await get_working_days_keyboard(lang, selected_days)
    try:
        if selected_days:
             days_str_list = []
             for d in sorted(selected_days):
                  day_info = DAYS_OF_WEEK.get(d)
                  if day_info: days_str_list.append(day_info.get(lang, day_info.get('ru', '?')))
                  else: days_str_list.append('?')
             days_str = ", ".join(days_str_list)
             days_display_text = strs(lang).working_days_display.format(days_str=days_str)
        else:
             days_display_text = strs(lang).no_working_days_selected

        await callback.message.edit_text(
            f"{strs(lang).ask_working_days}\n\n{days_display_text}",
            reply_markup=new_keyboard
        )
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            bot_logger.error(f"Error editing working days msg for admin {user_id}: {e}")

    await callback.answer()

# Обработка кнопки "Далее" после выбора дней
@working_hours_router.callback_query(WorkingHoursStates.get_days, F.data == "wh_days_next")
async def ask_exception_dates(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    lang = (await state.get_data()).get('lang', 'ru')
    data = await state.get_data()
    selected_days = data.get("selected_days", [])

    if not selected_days:
        await callback.answer("Пожалуйста, выберите хотя бы один рабочий день.", show_alert=True)
        return

    bot_logger.info(f"Admin {user_id} finished selecting days: {selected_days}")

    try:
         await callback.message.edit_reply_markup(reply_markup=None)
    except Exception: pass

    await callback.message.answer(
        strs(lang).ask_exception_dates,
        reply_markup=await get_skip_exceptions_keyboard(lang)
    )
    await state.set_state(WorkingHoursStates.get_exceptions)
    await callback.answer()


# Получение дат-исключений
@working_hours_router.message(WorkingHoursStates.get_exceptions)
async def get_exception_dates(message: Message, state: FSMContext):
    user_id = message.from_user.id
    lang = (await state.get_data()).get('lang', 'ru')
    text = message.text
    exception_dates = []
    error = False

    if text == strs(lang).skip_btn:
        bot_logger.info(f"Admin {user_id} skipped exception dates.")
        exception_dates = []
    else:
        try:
            raw_dates = [d.strip() for d in text.split(',') if d.strip()]
            if not raw_dates:
                 raise ValueError("Empty input is not allowed unless 'Skip' is pressed")
            parsed_dates = set()
            for date_str in raw_dates:
                # Проверяем формат ДД.ММ.ГГГГ и валидность даты
                parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                parsed_dates.add(date_str) # Сохраняем в исходном формате
            exception_dates = sorted(list(parsed_dates), key=lambda d: datetime.strptime(d, '%d.%m.%Y')) # Сортируем даты
            bot_logger.info(f"Admin {user_id} provided exception dates: {exception_dates}")
        except ValueError:
            error = True
            bot_logger.warning(f"Admin {user_id} provided invalid date format: {text}")
            await message.answer(
                strs(lang).ask_exception_dates_error,
                reply_markup=await get_skip_exceptions_keyboard(lang)
            )

    if not error:
        data = await state.get_data()
        final_settings = {
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "working_days": sorted(data.get("selected_days", [])), # Сохраняем отсортированными
            "exceptions": exception_dates
        }

        pref = await db.preferences.get_by_key("working_hours")
        if pref:
            pref.value = final_settings
            await db.preferences.update(pref)
        else:
            new_pref = PreferenceModel(key="working_hours", value=final_settings)
            await db.preferences.insert(new_pref)

        bot_logger.info(f"Admin {user_id} saved working hours settings: {final_settings}")
        await message.answer(
            strs(lang).working_hours_saved,
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
             strs(lang).use_help,
             reply_markup=await get_main_menu(lang=lang, user_id=user_id)
        )
        await state.clear()


# Обработка отмены на любом шаге настройки графика
@working_hours_router.message(
    F.text.in_(decline_btn),
    StateFilter( # Используем StateFilter(...) для перечисления состояний
        WorkingHoursStates.get_hours,
        WorkingHoursStates.get_days,
        WorkingHoursStates.get_exceptions
    )
)
async def cancel_working_hours_setup(message: Message, state: FSMContext):
    bot_logger.info(f"Admin {message.from_user.id} cancelled working hours setup.")
    lang = (await state.get_data()).get('lang', 'ru')
    await message.answer(
        strs(lang).working_hours_cancelled,
        reply_markup=await get_main_menu(lang=lang, user_id=message.from_user.id)
    )
    await state.clear()