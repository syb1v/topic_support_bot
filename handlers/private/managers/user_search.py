import database
from utils.logger import bot_logger
from . import *

from datetime import datetime, timedelta, timezone
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
# Project
import config as cf
from database import db
from translations import strs
from handlers.utils import get_decline_reply_keyboard, make_up_user_info
import traceback


# __router__ !DO NOT DELETE!
search_router = Router()


# __states__ !DO NOT DELETE!
class UserInfoStates(StatesGroup):
    get_user_info = State()


# __buttons__ !DO NOT DELETE!
async def get_user_actions_inline_keyboard(
        lang: str, user_id: int, ticket_id: str | None, user_is_manager: bool, is_user_admin: bool = False
) -> InlineKeyboardMarkup | None:
    """ Генерирует клавиатуру действий для найденного пользователя (для менеджера/админа) """
    # Кнопки доступны только админам или для обычных пользователей (которых может мутить/банить менеджер)
    if user_is_manager and not is_user_admin:
        return None # Менеджер не может управлять другим менеджером

    button_list = []
    user_for_buttons = await db.users.get_by_id(user_id=user_id) # Получаем актуальные данные пользователя
    if not user_for_buttons:
         bot_logger.error(f"Пользователь {user_id} не найден при генерации кнопок действий.")
         return None

    # Кнопка Mute (менеджер может мутить юзера, админ может всех)
    # Не показываем кнопку мута для забаненных или уже замученных
    if (not user_is_manager or is_user_admin) and not user_for_buttons.is_banned:
        if user_for_buttons.mute_time and user_for_buttons.mute_time > datetime.now(timezone(timedelta(hours=3))):
             # TODO: Добавить кнопку Unmute, если нужно (например, `unmute_btn {user_id}`)
             pass # Пока не добавляем кнопку размута
        else: # Если не замучен или время мута прошло
             button_list.append(
                 [InlineKeyboardButton(text=strs(lang=lang).mute_btn, callback_data=f'ticket_mute {ticket_id or "None"} {user_id}')]
             )

    # Кнопка "Тикеты пользователя"
    button_list.append(
        [InlineKeyboardButton(text=strs(lang=lang).user_tickets_btn,
                              callback_data=f'ticket_user_tickets {user_id} {int(user_is_manager)}')])

    # Только админские кнопки
    if is_user_admin:
        # Ban/Unban
        if not user_for_buttons.is_banned:
            button_list.append(
                [InlineKeyboardButton(text=strs(lang=lang).ban_btn, callback_data=f'ban_btn {user_id} {ticket_id or "None"}')]
            )
        else:
            button_list.append(
                [InlineKeyboardButton(text=strs(lang=lang).unban_btn, callback_data=f'unban_btn {user_id}')]
            )
        # Смена статуса
        if user_is_manager: # Если текущий статус - менеджер (или админ)
            # Не позволяем админу разжаловать самого себя через этот интерфейс
            if user_id != cf.admin_ids[0]: # Простая проверка, возможно, нужна более надежная
                 button_list.append(
                      [InlineKeyboardButton(text=strs(lang=lang).make_ordinary_btn,
                                            callback_data=f'make_user user {user_id}')]
                 )
        else: # Если текущий статус - обычный пользователь
            button_list.append(
                [InlineKeyboardButton(text=strs(lang=lang).make_manager_btn,
                                      callback_data=f'make_user manager {user_id}')]
            )
        # Кнопка Обновить
        button_list.append(
            [InlineKeyboardButton(text=strs(lang=lang).update_btn,
                                  callback_data=f'search_update_btn {user_id} {ticket_id or "None"} {int(user_is_manager)} {int(is_user_admin)}')],
        )
    # Кнопка Закрыть есть всегда, если есть другие кнопки
    if button_list:
         button_list.append(
            [InlineKeyboardButton(text=strs(lang=lang).delete_btn, callback_data='delete_btn')]
         )

    if not button_list:
        return None

    return InlineKeyboardMarkup(inline_keyboard=button_list)


# --- Обработчики колбэков ---

@search_router.callback_query(filters.IsAdmin(), F.data.startswith('make_user'))
async def handle_change_user_status_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling make_user button callback from admin {callback.message.chat.id}')
    data = callback.data.split()
    try:
        new_status = data[1] # 'user' or 'manager'
        target_user_id = int(data[2])
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid callback data for make_user: {callback.data}")
        await callback.answer("Error changing user status.", show_alert=True)
        return

    target_user = await db.users.get_by_id(user_id=target_user_id)
    if not target_user:
        await callback.answer("Target user not found.", show_alert=True)
        return

    # Запрещаем админу менять свой статус через этот интерфейс
    if target_user_id == callback.from_user.id and target_user.status == 'admin':
         await callback.answer("Администратор не может изменить свой статус.", show_alert=True)
         return

    current_lang = (await state.get_data()).get('lang', 'ru')
    alert_text = ""
    status_changed = False

    if new_status == 'manager' and target_user.status != 'manager':
        target_user.status = 'manager'
        await db.users.update(user=target_user)
        alert_text = strs(lang=current_lang).search_manager_now + strs(lang=current_lang).press_update_btn
        status_changed = True
        try:
            await callback.bot.send_message(target_user_id, text=strs(lang=target_user.lang).search_manager_now)
        except Exception as e:
            bot_logger.error(f"Failed to notify user {target_user_id} about becoming manager: {e}")
    elif new_status == 'user' and target_user.status != 'user':
        target_user.status = 'user'
        await db.users.update(user=target_user)
        alert_text = strs(lang=current_lang).search_user_now + strs(lang=current_lang).press_update_btn
        status_changed = True
        try:
            await callback.bot.send_message(target_user_id, text=strs(lang=target_user.lang).search_user_now)
        except Exception as e:
            bot_logger.error(f"Failed to notify user {target_user_id} about becoming user: {e}")
    else:
        await callback.answer("User already has this status.", show_alert=True) # Уведомляем, если статус не меняется
        return # Выход, если статус не изменился

    if status_changed:
         await callback.answer(alert_text, show_alert=True)
         # Вызываем обновление информации о пользователе после изменения статуса
         await handle_search_update_button_callback(callback, state) # Передаем callback и state


@search_router.callback_query(filters.IsManagerOrAdmin(), F.data.startswith('search_update_btn'))
async def handle_search_update_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling search_update_btn button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    try:
        target_user_id = int(data[1])
        database.db.ticket_id = data[2] if data[2] != 'None' else None
    except (IndexError, ValueError):
        bot_logger.error(f"Invalid callback data for search_update_btn: {callback.data}")
        await callback.answer("Error updating user info.", show_alert=True)
        return

    target_user = await db.users.get_by_id(user_id=target_user_id)
    if not target_user:
        await callback.answer("User not found.", show_alert=True)
        try: await callback.message.delete()
        except: pass
        return

    current_user = await db.users.get_by_id(user_id=callback.message.chat.id)
    if not current_user: return # Если текущий юзер не найден, выходим

    is_current_user_admin = current_user.status == 'admin'
    current_lang = (await state.get_data()).get('lang', 'ru')

    is_target_manager, info_text = await make_up_user_info(user=target_user, lang=current_lang)
    actions_keyboard = await get_user_actions_inline_keyboard(
        lang=current_lang,
        user_id=target_user_id,
        ticket_id=target_user.current_ticket_id, # Берем актуальный ID тикета
        user_is_manager=is_target_manager,
        is_user_admin=is_current_user_admin
    )

    try:
        await callback.message.edit_text(text=info_text, reply_markup=actions_keyboard)
        await callback.answer("Информация обновлена.")
    except Exception as e:
        # Проверяем ошибку "message is not modified" и игнорируем ее
        if "message is not modified" in str(e).lower():
            await callback.answer("Информация уже актуальна.")
        else:
            bot_logger.error(f"Error editing message on user info update: {e}")
            await callback.answer("Error updating message.", show_alert=True)

# __chat__ !DO NOT DELETE!
@search_router.message(
    filters.Private(), filters.IsManagerOrAdmin(),
    ((F.text == '/search') | (F.text.in_(find_user_btn)))
)
async def handle_search_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /search from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await message.answer(text=strs(lang=lang).search_ask_info,
                         reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(UserInfoStates.get_user_info.state)


@search_router.message(UserInfoStates.get_user_info)
async def handle_get_user_info_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states UserInfoStates.get_user_info from user {message.chat.id}')
    manager_user = await db.users.get_by_id(user_id=message.chat.id)
    if not manager_user:
        bot_logger.error(f"Current user {message.chat.id} not found in handle_get_user_info_state")
        await state.clear()
        return
    is_user_admin = manager_user.status == 'admin'
    lang = (await state.get_data()).get('lang', 'ru')

    # --- Используем get_main_menu для определения правильной клавиатуры ---
    from handlers.utils import get_main_menu
    markup = await get_main_menu(lang=lang, user_id=message.chat.id)

    info = message.text
    if info:
        found_user = None
        try:
            if info.isdigit(): found_user = await db.users.get_by_id(user_id=int(info))
            if not found_user and info.startswith('@') and len(info) > 1: found_user = await db.users.get_by_url_name(url_name=info[1:].lower())
            if not found_user: found_user = await db.users.get_by_tg_name(tg_name=info)

            if found_user:
                await message.answer(text=strs(lang=lang).user_found, reply_markup=markup)
                is_target_manager, info_text = await make_up_user_info(user=found_user, lang=lang)
                actions_keyboard = await get_user_actions_inline_keyboard(
                    user_id=int(found_user.id),
                    ticket_id=found_user.current_ticket_id, # Используем актуальный ID тикета
                    user_is_manager=is_target_manager,
                    is_user_admin=is_user_admin,
                    lang=lang
                )
                await message.answer(text=info_text, reply_markup=actions_keyboard)
            else:
                bot_logger.info(f'User not found: {info}')
                await message.answer(text=strs(lang=lang).search_not_found, reply_markup=markup)
        except Exception as e:
            bot_logger.error(f"Error searching user '{info}': {e}\n{traceback.format_exc()}")
            await message.answer(text=strs(lang=lang).search_not_found, reply_markup=markup)
        finally:
             await state.clear()
        return

    await message.answer(text=strs(lang=lang).search_ask_info_error)