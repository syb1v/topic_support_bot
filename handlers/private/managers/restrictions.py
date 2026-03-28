from . import *
from utils.logger import bot_logger
from aiogram.fsm.state import State, StatesGroup

# Standard
from datetime import datetime, timezone, timedelta
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database import db
from translations import strs
from handlers.utils import get_decline_reply_keyboard

# __router__ !DO NOT DELETE!
mute_router = Router()


# __states__ !DO NOT DELETE!
class MuteStates(StatesGroup):
    get_mute_time = State()


# __buttons__ !DO NOT DELETE!
async def _close_ticket(ticket_id: str | None):
    if not ticket_id or ticket_id == 'None':
        bot_logger.warning(f"Попытка закрыть тикет с неверным/None ID: {ticket_id}")
        return
    try:
        ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
        if ticket:
            current_date = datetime.now(timezone(timedelta(hours=3)))
            close_date = ticket.close_date
            manager_id = ticket.manager_id
            if not close_date:
                ticket.close_date = current_date
                ticket.last_modified = current_date
                await db.tickets.update(ticket=ticket)

                # Освобождаем менеджера, если он был назначен и это был его текущий тикет
                if manager_id:
                    manager = await db.users.get_by_id(user_id=manager_id)
                    if manager and manager.current_ticket_id == str(ticket.id):
                        manager.current_ticket_id = None
                        await db.users.update(user=manager)

                # Освобождаем пользователя
                user = await db.users.get_by_id(user_id=ticket.user_id)
                if user:
                    user.current_ticket_id = None
                    user.current_topic_id = None # Убираем topic_id при закрытии
                    await db.users.update(user=user)
        else:
            bot_logger.warning(f"Тикет {ticket_id} не найден в базе данных при закрытии (в _close_ticket)")
    except Exception as e:
        bot_logger.error(f"Ошибка при закрытии тикета {ticket_id} (в _close_ticket): {e}")

@mute_router.callback_query(F.data.startswith('ban_btn'))
async def handle_ban_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_actions ban button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id, ticket_id = int(data[1]), data[2]

    if ticket_id and ticket_id != 'None':
        await _close_ticket(ticket_id=ticket_id)

    user = await db.users.get_by_id(user_id=user_id)
    if not user: # Проверка на случай, если пользователя удалили
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user.is_banned = True
    await db.users.update(user=user)

    # Пытаемся уведомить пользователя
    try:
         await callback.bot.send_message(
             chat_id=user_id,
             text=strs(lang=user.lang).restriction_banned_forever
         )
    except Exception as e:
         bot_logger.error(f"Не удалось уведомить пользователя {user_id} о бане: {e}")

    await callback.answer(
        text=strs(lang=(await state.get_data())['lang']).restriction_banned_successfully + strs(
            lang=(await state.get_data())['lang']).press_update_btn,
        show_alert=True)
    # await callback.answer() # лишний


@mute_router.callback_query(F.data.startswith('unban_btn'))
async def handle_unban_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling user_actions unban button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id = int(data[1])

    user = await db.users.get_by_id(user_id=user_id)
    if not user: # Проверка
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    user.is_banned = False
    await db.users.update(user=user)

    # Пытаемся уведомить
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=strs(lang=user.lang).restriction_unbanned
        )
    except Exception as e:
        bot_logger.error(f"Не удалось уведомить пользователя {user_id} о разбане: {e}")

    await callback.answer(text=strs(
        lang=(await state.get_data())['lang']).restriction_unbanned_successfully + strs(
        lang=(await state.get_data())['lang']).press_update_btn,
                          show_alert=True)
    # await callback.answer() # лишний


@mute_router.callback_query(F.data.startswith('ticket_mute'), filters.IsManagerOrAdmin())
async def handle_mute_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling ticket_menu mute button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    user_id = None
    ticket_id = 'None' # По умолчанию ID тикета нет

    try:
        if len(data) >= 3: # Ожидаем 'ticket_mute {ticket_id} {user_id}'
            ticket_id = data[1] # Может быть 'None'
            user_id = int(data[2])
        elif len(data) == 2: # Возможно, старый формат 'ticket_mute {user_id}'? (на всякий случай)
            user_id = int(data[1])
            bot_logger.warning(f"Обработка старого формата callback для mute: {callback.data}")
        else:
            raise ValueError("Недостаточно данных в callback")

    except (IndexError, ValueError) as e:
        bot_logger.error(f"Ошибка разбора callback_data для ticket_mute: {callback.data}, {e}")
        await callback.answer("Ошибка данных.", show_alert=True)
        return

    # Проверяем, что user_id получен
    if user_id is None:
        await callback.answer(text=strs(lang=(await state.get_data())['lang']).user_not_found, show_alert=True)
        return

    # Проверяем, что пользователь существует
    user = await db.users.get_by_id(user_id=user_id)
    if not user:
        await callback.answer(text=strs(lang=(await state.get_data())['lang']).user_not_found, show_alert=True)
        return

    # Проверяем, не забанен ли уже пользователь
    if user.is_banned:
         await callback.answer("Пользователь забанен, нельзя ограничить.", show_alert=True)
         return
    # Проверяем, не ограничен ли уже пользователь
    if user.mute_time and user.mute_time > datetime.now(timezone(timedelta(hours=3))):
         await callback.answer("Пользователь уже ограничен.", show_alert=True)
         return

    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(text=strs(lang=lang).ticket_get_mute,
                                  reply_markup=await get_decline_reply_keyboard(lang=lang))

    await state.update_data({'ticket_id': ticket_id, 'user_id': user_id})
    await state.set_state(MuteStates.get_mute_time.state)

    await callback.answer()


# --- Обработчик отмены из состояния Mute ---
@mute_router.message(MuteStates.get_mute_time, F.text.in_(decline_btn))
async def handle_decline_mute_time(message: Message, state: FSMContext):
    bot_logger.info(f'Handling decline mute time from user {message.from_user.id}')
    from handlers.utils import get_main_menu
    lang = (await state.get_data()).get('lang', 'ru')
    await message.answer(
        text=strs(lang=lang).decline_msg,
        reply_markup=await get_main_menu(lang=lang, user_id=message.chat.id)
    )
    await state.clear()


@mute_router.message(MuteStates.get_mute_time)
async def handle_get_mute_time_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states MuteStates.get_mute_time from user {message.chat.id}')
    mute_mins = message.text
    lang = (await state.get_data()).get('lang', 'ru')
    from handlers.utils import get_main_menu
    reply_menu = await get_main_menu(lang=lang, user_id=message.chat.id)

    if mute_mins and mute_mins.isdigit() and 0 <= int(mute_mins) <= 1440: # Максимум 24 часа
        data = await state.get_data()
        ticket_id = data.get('ticket_id')
        user_id = data.get('user_id')

        # Проверяем, что user_id не None
        if user_id is None:
            await message.answer(text=strs(lang=lang).user_not_found, reply_markup=reply_menu)
            await state.clear()
            return

        user = await db.users.get_by_id(user_id=user_id)
        if not user:
            await message.answer(text=strs(lang=lang).user_not_found, reply_markup=reply_menu)
            await state.clear()
            return

        if int(mute_mins) == 0: # Снятие ограничений
            user.mute_time = None
            await db.users.update(user=user)
            # Пытаемся уведомить
            try:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=strs(lang=user.lang).restriction_unmuted
                )
            except Exception as e:
                 bot_logger.error(f"Не удалось уведомить пользователя {user_id} о снятии ограничений: {e}")

            await message.answer(text=strs(lang=lang).restriction_unmuted_successfully, reply_markup=reply_menu)
            await state.clear()
            return

        # Установка ограничений
        if ticket_id and ticket_id != 'None':
            try:
                ticket = await db.tickets.get_by_id(ticket_id=ticket_id)
                if ticket:
                    await _close_ticket(ticket_id=ticket_id)
                    # Убедимся, что user_id совпадает с user_id из тикета, на всякий случай
                    if ticket.user_id != user_id:
                         bot_logger.warning(f"user_id в state ({user_id}) не совпадает с user_id тикета ({ticket.user_id}) при муте.")
                         # Можно прервать или продолжить с user_id из state
                else:
                    bot_logger.warning(f"Тикет {ticket_id} не найден в базе данных при установке ограничения")
            except Exception as e:
                bot_logger.error(f"Ошибка при получении/закрытии тикета {ticket_id} при муте: {e}")

        # Используем UTC для расчетов
        current_time_utc = datetime.now(timezone.utc)
        mute_until_utc = current_time_utc + timedelta(minutes=int(mute_mins))
        user.mute_time = mute_until_utc # Сохраняем в UTC
        await db.users.update(user=user)

        # Отображаем время в МСК для уведомления пользователя
        try:
             msk_tz = timezone(timedelta(hours=3))
             mute_until_msk_str = mute_until_utc.astimezone(msk_tz).strftime('%Y-%m-%d %H:%M:%S')
             notification_text = strs(lang=user.lang).restriction_before(mute_until_msk_str) # Используем restriction_before
        except Exception as e:
             bot_logger.error(f"Ошибка форматирования времени для уведомления пользователя {user_id}: {e}")
             notification_text = strs(lang=user.lang).restriction_get_muted(mute_mins) # Fallback

        # Пытаемся уведомить
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=notification_text
            )
        except Exception as e:
            bot_logger.error(f"Не удалось уведомить пользователя {user_id} об ограничении: {e}")

        await message.answer(text=strs(lang=lang).restriction_successfully(mute_mins), reply_markup=reply_menu)
        await state.clear()
    else:
        await message.answer(text=strs(lang=lang).ticket_get_mute_error) # Оставляем пользователя в состоянии для повторного ввода