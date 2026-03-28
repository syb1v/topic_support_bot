from . import *
from database import db
from utils.logger import bot_logger
from database.models import PreferenceModel
from aiogram.fsm.state import State, StatesGroup

# Standard
import asyncio

# Project
from bot import bot
from handlers.utils import get_decline_reply_keyboard
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramAPIError

# __router__ !DO NOT DELETE!
mailing_router = Router()


# __states__ !DO NOT DELETE!
class MailingStates(StatesGroup):
    get_msg = State()
    get_link = State()


# __buttons__ !DO NOT DELETE!
async def get_mailing_msg_menu_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    button_list = [
        [InlineKeyboardButton(text=strs(lang=lang).send_mailing_message_btn, callback_data='mailing_send_btn')],
        [InlineKeyboardButton(text=strs(lang=lang).mailing_add_link_btn, callback_data='mailing_add_link_btn')],
        [InlineKeyboardButton(text=strs(lang=lang).mailing_delete_btn, callback_data='mailing_delete_btn')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=button_list)

# --- Обработчики колбэков ---
@mailing_router.callback_query(F.data.startswith('mailing_delete_btn'))
async def handle_mailing_delete_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling add_link mailing_delete button callback from user {callback.message.chat.id}')
    pref_msg = await db.preferences.get_by_key(key='preference_message')
    if pref_msg:
        if isinstance(pref_msg.value, dict) and 'preview_message_id' in pref_msg.value:
            try: await bot.delete_message(callback.from_user.id, pref_msg.value['preview_message_id'])
            except Exception as e: bot_logger.warning(f"Could not delete mailing preview msg on delete: {e}")
        await db.preferences.delete(preference=pref_msg)
    try: await callback.message.delete()
    except: pass
    from handlers.utils import get_main_menu
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(
        text=strs(lang=lang).use_help,
        reply_markup=await get_main_menu(lang=lang, user_id=callback.from_user.id)
    )
    await callback.answer()

@mailing_router.callback_query(F.data.startswith('mailing_add_link_btn'))
async def handle_link_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling add_link link button callback from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(
        text=strs(lang=lang).admin_mailing_add_link,
        reply_markup=await get_decline_reply_keyboard(lang=lang))
    await state.set_state(MailingStates.get_link.state)
    await callback.answer()

@mailing_router.callback_query(F.data.startswith('mailing_send_btn'))
async def handle_mailing_send_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling mailing_send button callback from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    pref_msg = await db.preferences.get_by_key(key='preference_message')
    if not pref_msg or not pref_msg.value or 'content' not in pref_msg.value:
         await callback.answer("Сообщение для рассылки не найдено.", show_alert=True)
         return

    msg_info_to_send = pref_msg.value['content']
    reply_markup_to_send = None

    try:
        original_markup_dict = msg_info_to_send.get('reply_markup')
        if original_markup_dict and 'inline_keyboard' in original_markup_dict:
            original_inline_keyboard = original_markup_dict['inline_keyboard']
            link_buttons_keyboard = []
            bot_logger.info("Filtering mailing keyboard by URL presence...")
            for row in original_inline_keyboard:
                link_buttons_row = []
                for btn_dict in row:
                    if 'url' in btn_dict and btn_dict['url']:
                        link_buttons_row.append(btn_dict)
                if link_buttons_row:
                    link_buttons_keyboard.append(link_buttons_row)
            bot_logger.info(f"Filtered keyboard (only links): {link_buttons_keyboard}")
            if link_buttons_keyboard:
                reply_markup_to_send = InlineKeyboardMarkup(inline_keyboard=link_buttons_keyboard)
                bot_logger.info("Created final reply_markup for sending (links only).")
            else:
                 bot_logger.info("No link buttons found, sending without keyboard.")
        else:
             bot_logger.info("Original message had no keyboard, sending without keyboard.")
    except Exception as e:
        bot_logger.error(f"Error processing keyboard for mailing: {e}")
        reply_markup_to_send = None

    users = await db.users.get_all()
    count = 0
    successful_sends = 0
    failed_sends = 0
    if users:
        # Воссоздаем объект Message, чтобы легче доставать данные
        message_obj_to_send = Message(**msg_info_to_send)
        total_users_to_send = len([u for u in users if u.id != callback.from_user.id])
        bot_logger.info(f"Starting mailing to {total_users_to_send} users...")

        for user in users:
            if user.id == callback.from_user.id:
                continue # Пропускаем админа

            try:
                content_type = message_obj_to_send.content_type
                caption = message_obj_to_send.caption

                if content_type == 'text':
                    await bot.send_message(
                        chat_id=user.id,
                        text=message_obj_to_send.text,
                        entities=message_obj_to_send.entities,
                        reply_markup=reply_markup_to_send
                    )
                elif content_type == 'photo':
                    await bot.send_photo(
                        chat_id=user.id,
                        photo=message_obj_to_send.photo[-1].file_id,
                        caption=caption,
                        caption_entities=message_obj_to_send.caption_entities,
                        reply_markup=reply_markup_to_send
                    )
                elif content_type == 'video':
                    await bot.send_video(
                        chat_id=user.id,
                        video=message_obj_to_send.video.file_id,
                        caption=caption,
                        caption_entities=message_obj_to_send.caption_entities,
                        reply_markup=reply_markup_to_send
                    )
                elif content_type == 'document':
                    await bot.send_document(
                        chat_id=user.id,
                        document=message_obj_to_send.document.file_id,
                        caption=caption,
                        caption_entities=message_obj_to_send.caption_entities,
                        reply_markup=reply_markup_to_send
                    )
                elif content_type == 'audio':
                     await bot.send_audio(
                        chat_id=user.id,
                        audio=message_obj_to_send.audio.file_id,
                        caption=caption,
                        caption_entities=message_obj_to_send.caption_entities,
                        reply_markup=reply_markup_to_send
                     )
                # Добавьте другие типы контента по аналогии (voice, video_note, animation, etc.)
                else:
                    # Если тип не поддерживается для прямой отправки, пробуем send_copy
                    # как запасной вариант, но без гарантии работы клавиатуры
                    bot_logger.warning(f"Unsupported content type '{content_type}' for direct send. Falling back to send_copy for user {user.id}.")
                    await message_obj_to_send.send_copy(
                        chat_id=user.id,
                        reply_markup=reply_markup_to_send
                    ).as_(bot)

                successful_sends += 1
                await asyncio.sleep(0.05) # Уменьшаем задержку, т.к. send_copy более ресурсоемкий

            except TelegramAPIError as e:
                failed_sends += 1
                bot_logger.error(f"Telegram API Error sending mailing to user {user.id}: {e}")
            except Exception as e:
                failed_sends += 1
                bot_logger.error(f"Unexpected error sending mailing to user {user.id}: {e}")
            finally:
                 count += 1

    bot_logger.info(f"Mailing finished. Attempted: {count}, Successful: {successful_sends}, Failed: {failed_sends}")

    from handlers.utils import get_main_menu
    admin_menu = await get_main_menu(lang=lang, user_id=callback.from_user.id)

    if successful_sends == 0 and count > 0: # Если были попытки, но все неудачные
        await callback.message.answer(
            text=f"Не удалось отправить рассылку ни одному пользователю (Ошибок: {failed_sends})",
            reply_markup=admin_menu)
    elif successful_sends == 0 and count == 0: # Если некому было отправлять
         await callback.message.answer(
             text=strs(lang=lang).admin_general_no_users,
             reply_markup=admin_menu)
    else:
        success_text = strs(lang=lang).admin_general_mailing_successful
        if failed_sends > 0:
            success_text += f" (Успешно: {successful_sends}, Ошибок: {failed_sends})"
        await callback.message.answer(
            text=success_text,
            reply_markup=admin_menu)

    if pref_msg:
        if isinstance(pref_msg.value, dict) and 'preview_message_id' in pref_msg.value:
            try: await bot.delete_message(callback.from_user.id, pref_msg.value['preview_message_id'])
            except Exception as e: bot_logger.warning(f"Could not delete mailing preview msg on send completion: {e}")
        await db.preferences.delete(preference=pref_msg)
    try: await callback.message.delete()
    except: pass
    await callback.answer()

# __chat__ !DO NOT DELETE!
@mailing_router.message(
    filters.Private(), filters.IsAdmin(),
    ((F.text == '/mailing') | (F.text.in_(send_mailing_btn)))
)
async def handle_mailing_command(message: Message, state: FSMContext):
    bot_logger.info(f'Handling command /mailing from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await message.answer(text=strs(lang=lang).admin_general_ask_mailing_msg,
                         reply_markup=await get_decline_reply_keyboard(lang=lang))

    await state.set_state(MailingStates.get_msg.state)


@mailing_router.message(MailingStates.get_link)
async def handle_get_link_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states MailingStates.get_link from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru') # Получаем язык
    text = message.text
    if text:
        info_list = text.split('-', maxsplit=1)
        if len(info_list) != 2 or not info_list[0].strip() or not info_list[1].strip(): # Проверка, что обе части не пустые
            await message.answer(text=strs(lang=lang).admin_mailing_add_link_error)
            return # Остаемся в состоянии

        info = await db.preferences.get_by_key('preference_message')
        if not info or not info.value or 'content' not in info.value:
            await message.answer("Ошибка: не найдено исходное сообщение для добавления ссылки.")
            await state.clear()
            return

        # Удаляем старую временную запись, если она есть
        # Удаляем также и старое сообщение предпросмотра
        if isinstance(info.value, dict) and 'preview_message_id' in info.value:
            try: await bot.delete_message(message.chat.id, info.value['preview_message_id'])
            except Exception as e: bot_logger.warning(f"Could not delete previous preview message: {e}")
        await db.preferences.delete(preference=info)


        saved_msg_info = info.value['content']
        # --- ИЗМЕНЕНИЕ: Создаем объект Message для удобства ---
        send_msg = Message(**saved_msg_info)
        control_markup = await get_mailing_msg_menu_inline_keyboard(lang=lang) # Клавиатура управления
        # Получаем существующую клавиатуру как словарь
        original_markup_dict = saved_msg_info.get('reply_markup')

        final_inline_keyboard = []
        # Добавляем существующие кнопки-ссылки (если есть)
        if original_markup_dict and 'inline_keyboard' in original_markup_dict:
            for row in original_markup_dict['inline_keyboard']:
                link_buttons_row = []
                for btn_dict in row:
                    if 'url' in btn_dict and btn_dict['url']:
                         link_buttons_row.append(btn_dict)
                if link_buttons_row:
                     final_inline_keyboard.append(link_buttons_row)

        # Добавляем новую кнопку
        try:
            new_button = InlineKeyboardButton(text=info_list[0].strip(), url=info_list[1].strip())
            final_inline_keyboard.append([new_button.model_dump()]) # Добавляем как словарь
        except Exception as e:
            bot_logger.warning(f"Invalid URL provided for mailing link: {info_list[1].strip()} - {e}")
            await message.answer(text=strs(lang=lang).admin_mailing_add_link_error)
            # Сохраняем исходное сообщение обратно во временное хранилище
            await db.preferences.insert(preference=info)
            return

        # Добавляем кнопки управления рассылкой в конец
        for control_row in control_markup.inline_keyboard:
             final_inline_keyboard.append([btn.model_dump() for btn in control_row])

        final_reply_markup = InlineKeyboardMarkup(inline_keyboard=final_inline_keyboard)

        # Отправляем обновленное сообщение админу для предпросмотра
        try:
             content_type = send_msg.content_type
             caption = send_msg.caption
             preview_message_to_save = None

             if content_type == 'text':
                 preview_message_to_save = await bot.send_message(
                     chat_id=message.chat.id, text=send_msg.text, entities=send_msg.entities,
                     reply_markup=final_reply_markup
                 )
             elif content_type == 'photo':
                 preview_message_to_save = await bot.send_photo(
                     chat_id=message.chat.id, photo=send_msg.photo[-1].file_id,
                     caption=caption, caption_entities=send_msg.caption_entities,
                     reply_markup=final_reply_markup
                 )
             elif content_type == 'video':
                 preview_message_to_save = await bot.send_video(
                     chat_id=message.chat.id, video=send_msg.video.file_id,
                     caption=caption, caption_entities=send_msg.caption_entities,
                     reply_markup=final_reply_markup
                 )
             elif content_type == 'document':
                 preview_message_to_save = await bot.send_document(
                     chat_id=message.chat.id, document=send_msg.document.file_id,
                     caption=caption, caption_entities=send_msg.caption_entities,
                     reply_markup=final_reply_markup
                 )
             elif content_type == 'audio':
                 preview_message_to_save = await bot.send_audio(
                     chat_id=message.chat.id, audio=send_msg.audio.file_id,
                     caption=caption, caption_entities=send_msg.caption_entities,
                     reply_markup=final_reply_markup
                 )
             # Добавьте другие типы по аналогии...
             else:
                  # Fallback на send_copy для неподдерживаемых типов предпросмотра
                  preview_message_to_save = await send_msg.send_copy(
                      chat_id=message.chat.id, reply_markup=final_reply_markup
                  ).as_(bot)


             # Сохраняем ИСХОДНОЕ сообщение (send_msg) с ОБНОВЛЕННОЙ клавиатурой
             # но с ID НОВОГО сообщения предпросмотра
             msg_info_to_db = send_msg.model_dump() # Исходное сообщение
             msg_info_to_db['reply_markup'] = final_reply_markup.model_dump() # Обновленная клава

             preference_message = PreferenceModel()
             preference_message.key = 'preference_message'
             preference_message.value = {'content': msg_info_to_db, 'preview_message_id': preview_message_to_save.message_id}
             await db.preferences.insert(preference=preference_message)
        except Exception as e:
            bot_logger.error(f"Error sending updated mailing preview: {e}")
            await message.answer("Произошла ошибка при обновлении предпросмотра.")
            # Сохраняем исходное сообщение обратно во временное хранилище
            await db.preferences.insert(preference=info)

        await state.clear()
        return

    await message.answer(text=strs(lang=lang).admin_mailing_add_link_error)


@mailing_router.message(MailingStates.get_msg)
async def handle_get_msg_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states MailingStates.get_msg from user {message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')

    from handlers.utils import get_main_menu
    admin_menu = await get_main_menu(lang=lang, user_id=message.chat.id)

    await message.delete() # Удаляем исходное сообщение админа
    await message.answer(text=strs(lang=lang).mailing_what_to_do,
                         reply_markup=admin_menu)

    try:
        # Отправляем копию сообщения для предпросмотра с кнопками управления
        msg = await message.send_copy(
            chat_id=message.chat.id,
            reply_markup=await get_mailing_msg_menu_inline_keyboard(lang=lang)
        )
        msg_info = msg.model_dump(mode='json') # Сериализуем Pydantic модель

        # Сохраняем сообщение во временную запись
        pref = await db.preferences.get_by_key(key='preference_message')
        if pref:
            if isinstance(pref.value, dict) and 'preview_message_id' in pref.value:
                try: await bot.delete_message(message.chat.id, pref.value['preview_message_id'])
                except Exception as e: bot_logger.warning(f"Could not delete previous preview message on get_msg: {e}")
            await db.preferences.delete(preference=pref)

        preference_message = PreferenceModel()
        preference_message.key = 'preference_message'
        preference_message.value = {'content': msg_info, 'preview_message_id': msg.message_id}
        await db.preferences.insert(preference=preference_message)

    except Exception as e:
         bot_logger.error(f"Error sending/saving mailing preview in get_msg: {e}")
         await message.answer("Произошла ошибка при создании предпросмотра рассылки.")

    await state.clear()