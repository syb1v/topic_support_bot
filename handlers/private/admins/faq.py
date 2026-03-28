from . import *

# Standard
from database import db
from utils.logger import bot_logger
from database.models import PreferenceModel
from uuid import uuid4
from json import loads, dumps
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

# Project
from handlers.utils import CustomJSONEncoder, get_decline_reply_keyboard, get_main_menu

# __router__ !DO NOT DELETE!
faq_router = Router()
general_faq_router = general_router


# __states__ !DO NOT DELETE!
class UpdateStates(StatesGroup):
    get_question = State()
    get_content = State()

class FaqStates(StatesGroup):
    get_question = State()
    get_buttons = State()
    get_content = State()
    get_category = State()

# __buttons__ !DO NOT DELETE!
async def get_faq_details_inline_keyboard(lang: str, question_id: str, is_admin: bool) -> InlineKeyboardMarkup:
    button_list = []
    if is_admin:
        button_list.append(
            [InlineKeyboardButton(text=strs(lang=lang).update_btn_question, callback_data=f'update_btn question {question_id}'),
             InlineKeyboardButton(text=strs(lang=lang).update_btn_content, callback_data=f'update_btn content {question_id}')],
        )
        button_list.append(
            [InlineKeyboardButton(text=strs(lang=lang).remove_btn, callback_data=f'remove_btn {question_id} {int(is_admin)}'),
             InlineKeyboardButton(text=strs(lang=lang).update_btn, callback_data=f'question_update {question_id} {int(is_admin)}')]
        )

    faq_pref = await db.preferences.get_by_key(key='faq')
    category_id_for_back = None
    if faq_pref and isinstance(faq_pref.value, dict):
        questions = faq_pref.value.get('questions', [])
        for q in questions:
            if q.get('question_id') == question_id:
                category_id_for_back = q.get('category')
                break
    if category_id_for_back is not None:
        back_callback = f'faq_set_category {category_id_for_back}'
    else:
        back_callback = 'back_to_choose_categories'

    button_list.append(
        [InlineKeyboardButton(text=strs(lang=lang).back_btn, callback_data=back_callback)]
    )
    return InlineKeyboardMarkup(inline_keyboard=button_list)

# --- Обработчики колбэков ---
@faq_router.callback_query(F.data.startswith('question_update'))
async def handle_question_update_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling faq_details question update button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    question_id, is_admin_str = data[1], data[2]
    is_admin_cb = bool(int(is_admin_str))

    faq = await db.preferences.get_by_key(key='faq')
    question = None
    if faq and isinstance(faq.value, dict):
         questions = faq.value.get('questions', [])
         question = next((q for q in questions if q.get('question_id') == question_id), None)

    if not question:
         await callback.answer("Вопрос не найден.", show_alert=True)
         return

    content = question.get('content')
    if not content or not isinstance(content, dict):
        await callback.answer("Содержимое вопроса не найдено или повреждено.", show_alert=True)
        return

    details_kb = await get_faq_details_inline_keyboard(
            lang=(await state.get_data())['lang'], question_id=question_id, is_admin=is_admin_cb)

    content_reply_markup = content.get('reply_markup')
    final_markup = details_kb
    if content_reply_markup and isinstance(content_reply_markup, dict) and 'inline_keyboard' in content_reply_markup:
         final_markup = InlineKeyboardMarkup(inline_keyboard=content_reply_markup['inline_keyboard'] + details_kb.inline_keyboard)

    try:
        await callback.message.delete()
        message = Message(**content)
        await message.send_copy(
            chat_id=callback.message.chat.id,
            reply_markup=final_markup
        ).as_(callback.bot)
    except Exception as e:
        bot_logger.error(f"Error sending/updating FAQ message on question_update: {e}")
        await callback.answer("Ошибка отображения вопроса.", show_alert=True)

    await callback.answer()


@faq_router.callback_query(F.data.startswith('update_btn'))
async def handle_update_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling faq_details update button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    action, question_id = data[1], data[2]
    lang = (await state.get_data()).get('lang', 'ru')

    await state.update_data({'question_id': question_id})
    if action == 'question':
        await callback.message.answer(
            text=strs(lang=lang).faq_ask_question,
            reply_markup=await get_decline_reply_keyboard(lang=lang)
        )
        await state.set_state(UpdateStates.get_question.state)
    elif action == 'content':
        await callback.message.answer(
            text=strs(lang=lang).faq_ask_content,
            reply_markup=await get_decline_reply_keyboard(lang=lang)
        )
        await state.set_state(UpdateStates.get_content.state)
    await callback.answer()


@faq_router.callback_query(F.data.startswith('remove_btn'))
async def handle_remove_button_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling faq_details remove button callback from user {callback.message.chat.id}')
    data = callback.data.split()
    question_id, is_admin_str = data[1], data[2]
    is_admin_cb = bool(int(is_admin_str))
    lang = (await state.get_data()).get('lang', 'ru')

    faq = await db.preferences.get_by_key(key='faq')
    category_id_for_back = None
    if faq and isinstance(faq.value, dict):
        questions = faq.value.get('questions', [])
        original_length = len(questions)
        question_to_remove = next((q for q in questions if q.get('question_id') == question_id), None)
        if question_to_remove: category_id_for_back = question_to_remove.get('category')
        faq.value['questions'] = [q for q in questions if q.get('question_id') != question_id]
        if len(faq.value['questions']) < original_length:
             await db.preferences.update(preference=faq)
             bot_logger.info(f"Admin {callback.from_user.id} removed FAQ question {question_id}")
             await callback.answer("Вопрос удален.", show_alert=True)
        else:
             bot_logger.warning(f"Admin {callback.from_user.id} tried to remove non-existent question {question_id}")
             await callback.answer("Вопрос не найден.", show_alert=True)
             return
    else:
        await callback.answer("Ошибка получения данных FAQ.", show_alert=True)
        return

    await callback.message.delete()
    await callback.message.answer(
        text=strs(lang=lang).faq_questions,
        reply_markup=await get_faq_menu_inline_keyboard(lang=lang, is_admin=is_admin_cb, category_id=category_id_for_back)
    )
# --- Конец колбэков ---

async def get_faq_menu_inline_keyboard(lang: str, is_admin: bool = False, category_id: int | str | None = None) -> InlineKeyboardMarkup:
    if isinstance(category_id, str):
        try:
            category_id = int(category_id)
        except ValueError:
            category_id = None # Если не число, сбрасываем

    button_list = []
    if category_id is not None: # Показываем вопросы категории
        faqs = await db.preferences.get_by_key(key='faq')
        questions = []
        if faqs and isinstance(faqs.value, dict):
            all_questions = faqs.value.get('questions', [])
            questions = [q for q in all_questions if q.get('category') == category_id]
        if questions:
            for question in questions:
                question_id = question.get('question_id')
                question_text = question.get('question', f"Вопрос ID: {question_id}")
                button_list.append(
                    [InlineKeyboardButton(text=question_text, callback_data=f'faq {question_id} {int(is_admin)}')]
                )
        else:
            button_list.append([InlineKeyboardButton(text="В этой категории пока нет вопросов.", callback_data='no_action')])

        if not is_admin:
            button_list.append(
                [InlineKeyboardButton(text=strs(lang=lang).faq_not_found_btn, callback_data='faq_create_ticket')]
            )

        if is_admin:
            button_list.extend([
                [InlineKeyboardButton(text=strs(lang=lang).add_btn, callback_data=f'add_btn {category_id}')],
                [InlineKeyboardButton(text=strs(lang=lang).admin_category_manage_btn, callback_data=f'manage_category {category_id}')]
            ])
        button_list.append([InlineKeyboardButton(text=strs(lang=lang).back_btn, callback_data='back_to_choose_categories')]) # Кнопка Назад к списку категорий

    else: # Показываем список категорий
        categories_pref = await db.preferences.get_by_key('categories')
        categories = []
        if categories_pref and isinstance(categories_pref.value, dict): categories = categories_pref.value.get('categories', [])

        if categories:
            button_list = [[InlineKeyboardButton(text=categories[i], callback_data=f'faq_set_category {i}')] for i in range(len(categories))]
        else:
            button_list.append([InlineKeyboardButton(text="Категории не найдены.", callback_data='no_action')])

        if is_admin:
            button_list.append([InlineKeyboardButton(text=strs(lang=lang).add_category_btn, callback_data='add_category')])

    return InlineKeyboardMarkup(inline_keyboard=button_list)

# --- Обработчики колбэков ---
@faq_router.callback_query(F.data.startswith('back_to_choose_categories'))
async def back_to_choose_categories_handler(callback: CallbackQuery, state: FSMContext):
    user = await db.users.get_by_id(user_id=callback.from_user.id)
    is_admin = user.status == 'admin' if user else False
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.edit_text(
        text=strs(lang=lang).faq_ask_category,
        reply_markup=await get_faq_menu_inline_keyboard(lang=lang, is_admin=is_admin)
    )
    await callback.answer()

@faq_router.callback_query(F.data.startswith('faq_set_category'))
async def faq_set_category_callback_handler(callback: CallbackQuery, state: FSMContext):
    category_id = callback.data.split(' ')[1]
    user = await db.users.get_by_id(user_id=callback.from_user.id)
    is_admin = user.status == 'admin' if user else False
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.edit_text(
        text=strs(lang=lang).faq_questions,
        reply_markup=await get_faq_menu_inline_keyboard(lang=lang, is_admin=is_admin, category_id=category_id)
    )
    await callback.answer()

@faq_router.callback_query(F.data.startswith('faq '))
async def handle_faq_button_callback_handler(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split()
    question_id, is_admin_str = data[1], data[2]
    await state.update_data(lang=(await state.get_data()).get('lang', 'ru')) # Сохраняем язык на всякий случай
    # Создаем новый callback_data для question_update
    new_callback_data = f'question_update {question_id} {is_admin_str}'
    callback.data = new_callback_data # Модифицируем данные колбэка
    await handle_question_update_button_callback(callback, state) # Вызываем обработчик деталей

@faq_router.callback_query(F.data.startswith('add_btn'))
async def handle_add_button_callback_handler(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split(' ')[1])
    lang = (await state.get_data()).get('lang', 'ru')
    await state.update_data({'category': category_id}) # Сохраняем категорию в state
    await callback.message.answer(
        text=strs(lang=lang).faq_ask_question,
        reply_markup=await get_decline_reply_keyboard(lang=lang)
    )
    await state.set_state(FaqStates.get_question.state)
    await callback.answer()

@faq_router.callback_query(F.data == 'add_category')
async def handle_add_category_callback_handler(callback: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(
        text=strs(lang=lang).admin_create_category,
        reply_markup=await get_decline_reply_keyboard(lang=lang)
    )
    await state.set_state(FaqStates.get_category.state) # Переходим в состояние get_category
    await callback.answer()
# --- Конец обработчиков колбэков ---

# __chat__ !DO NOT DELETE!

# Обработчик для команд /faq и /change_faq
@general_faq_router.message(
    filters.Private(),
    Command('faq', 'change_faq')
)
async def handle_faq_commands(message: Message, state: FSMContext):
    await process_faq_request(message, state)

# Обработчик для кнопок faq_btn и change_faq_btn
@general_faq_router.message(
    filters.Private(),
    F.text.in_(faq_btn) | F.text.in_(change_faq_btn)
)
async def handle_faq_buttons(message: Message, state: FSMContext):
    await process_faq_request(message, state)

async def process_faq_request(message: Message, state: FSMContext):
    """Общая логика для обработки запросов FAQ (команды и кнопки)."""
    bot_logger.info(f'Handling FAQ request from user {message.chat.id}')
    user = await db.users.get_by_id(user_id=message.chat.id)
    is_admin = user.status == 'admin' if user else False
    lang = (await state.get_data()).get('lang', 'ru')
    await message.answer(
        text=strs(lang=lang).faq_ask_category,
        reply_markup=await get_faq_menu_inline_keyboard(lang=lang, is_admin=is_admin)
    )


@general_router.callback_query(F.data.startswith('show_faq_main'))
async def handle_faq_callback(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling show_faq_main callback from user {callback.message.chat.id}')
    user = await db.users.get_by_id(user_id=callback.message.chat.id)
    is_admin = user.status == 'admin' if user else False
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.edit_text(
        text=strs(lang=lang).faq_ask_category,
        reply_markup=await get_faq_menu_inline_keyboard(lang=lang, is_admin=is_admin)
    )
    await callback.answer()


@faq_router.message(FaqStates.get_question)
async def handle_get_question_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_question from user {message.chat.id}')
    question = message.text
    lang = (await state.get_data()).get('lang', 'ru')
    if question:
        await state.update_data({'question': question})
        await state.update_data({"buttons": {}})
        await message.answer(text=strs(lang=lang).faq_get_buttons,
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text=strs(lang=lang).faq_media_skip, callback_data=f'to_choose_content')]
                             ]))
        await state.set_state(FaqStates.get_buttons.state)
    else:
        await message.answer(text=strs(lang=lang).faq_ask_question_error)


@faq_router.message(FaqStates.get_buttons)
async def handle_get_buttons_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_buttons from user {message.chat.id}')
    buttons = (await state.get_data()).get('buttons', {})
    lang = (await state.get_data()).get('lang', 'ru')
    button_text = message.text
    if '-' not in button_text:
        current_buttons_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f'delete_faq_but {i}')] for i in buttons] + [[InlineKeyboardButton(text=strs(lang).faq_media_skip, callback_data=f'to_choose_content')]])
        await message.answer(strs(lang).faq_get_buttons, reply_markup=current_buttons_markup)
        return
    button = button_text.split('-', maxsplit=1)
    if len(button) != 2:
        current_buttons_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f'delete_faq_but {i}')] for i in buttons] + [[InlineKeyboardButton(text=strs(lang).faq_media_skip, callback_data=f'to_choose_content')]])
        await message.answer(strs(lang).faq_get_buttons, reply_markup=current_buttons_markup)
        return
    buttons[button[0].strip()] = button[1].strip()
    await state.update_data({'buttons': buttons})
    new_buttons_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f'delete_faq_but {i}')] for i in buttons] + [[InlineKeyboardButton(text=strs(lang).faq_media_skip, callback_data=f'to_choose_content')]])
    await message.answer(strs(lang).faq_get_buttons, reply_markup=new_buttons_markup)


@faq_router.callback_query(F.data.startswith('to_choose_content'))
async def handle_get_buttons_state_to_content(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling to_choose_content from user {callback.message.chat.id}')
    lang = (await state.get_data()).get('lang', 'ru')
    await callback.message.answer(text=strs(lang=lang).faq_ask_content, reply_markup=ReplyKeyboardRemove())
    await state.set_state(FaqStates.get_content.state)
    await callback.answer()
    try: await callback.message.delete()
    except: pass


@faq_router.callback_query(F.data.startswith('delete_faq_but'))
async def handle_get_buttons_state_delete_button(callback: CallbackQuery, state: FSMContext):
    bot_logger.info(f'Handling delete_faq_but from user {callback.message.chat.id}')
    buttons = (await state.get_data()).get('buttons', {})
    button_to_delete = callback.data.split(' ', maxsplit=1)[1]
    lang = (await state.get_data()).get('lang', 'ru')
    if button_to_delete in buttons:
        del buttons[button_to_delete]
        await state.update_data({'buttons': buttons})
        new_buttons_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=f'delete_faq_but {i}')] for i in buttons] + [[InlineKeyboardButton(text=strs(lang).faq_media_skip, callback_data=f'to_choose_content')]])
        try: await callback.message.edit_reply_markup(reply_markup=new_buttons_markup)
        except Exception as e:
            bot_logger.error(f"Error editing buttons markup: {e}")
            # Если редактирование не удалось, отправляем новое сообщение
            await callback.message.answer(strs(lang).faq_get_buttons, reply_markup=new_buttons_markup)
    await callback.answer(f"Кнопка '{button_to_delete}' удалена")


@faq_router.message(FaqStates.get_content)
async def handle_get_content_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_content from user {message.chat.id}')
    question_id = str(uuid4())[:10]
    data = await state.get_data()
    buttons = data.get('buttons', {})
    question = data.get('question')
    category = data.get('category')
    lang = data.get('lang', 'ru')

    if question is None or category is None:
        bot_logger.error(f"Missing question or category in state for user {message.chat.id}")
        await message.answer("Произошла ошибка сохранения.")
        await state.clear()
        return

    inline_keyboard = [[InlineKeyboardButton(text=i, url=buttons[i])] for i in buttons]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_keyboard) if buttons else None

    try:
        message_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
        if reply_markup:
            message_info['reply_markup'] = loads(dumps(reply_markup.model_dump(), cls=CustomJSONEncoder))
        else:
            message_info['reply_markup'] = None # Убеждаемся, что None если кнопок нет

        faq = await db.preferences.get_by_key('faq')
        if not faq:
            faq = PreferenceModel(key='faq', value={'questions': [], 'footer_button': {'text': "Не нашли нужный ответ?", 'action': 'create_ticket'}})
            await db.preferences.insert(faq)
            faq = await db.preferences.get_by_key('faq') # Перечитываем после вставки

        # Гарантируем правильную структуру faq.value
        if not isinstance(faq.value, dict): faq.value = {}
        if 'questions' not in faq.value or not isinstance(faq.value['questions'], list): faq.value['questions'] = []

        faq.value['questions'].append({
            'question_id': question_id,
            'question': question,
            'content': message_info,
            'category': category
        })

        await db.preferences.update(preference=faq)

        user = await db.users.get_by_id(user_id=message.chat.id)
        reply_menu = await get_main_menu(lang=lang, user_id=message.chat.id) # Используем get_main_menu
        await message.answer(text=strs(lang=lang).faq_added, reply_markup=reply_menu)
        await state.clear()
    except Exception as e:
        bot_logger.error(f"Error processing content state for user {message.chat.id}: {e}")
        await message.answer("Произошла ошибка при сохранении вопроса.")
        await state.clear()


@faq_router.message(FaqStates.get_category)
async def handle_get_category_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states FaqStates.get_category from user {message.chat.id}')
    category_name = message.text.strip()
    lang = (await state.get_data()).get('lang', 'ru')
    if category_name:
        categories_pref = await db.preferences.get_by_key('categories')
        if not categories_pref:
            categories_pref = PreferenceModel(key='categories', value={'categories': []})
            await db.preferences.insert(categories_pref)
            categories_pref = await db.preferences.get_by_key('categories') # Перечитываем

        if not isinstance(categories_pref.value, dict): categories_pref.value = {}
        if 'categories' not in categories_pref.value or not isinstance(categories_pref.value['categories'], list): categories_pref.value['categories'] = []

        categories_pref.value['categories'].append(category_name)
        await db.preferences.update(categories_pref)

        user = await db.users.get_by_id(user_id=message.chat.id)
        reply_menu = await get_main_menu(lang=lang, user_id=message.chat.id) # Используем get_main_menu
        await message.answer(text=strs(lang=lang).admin_create_category_success.format(category_name), reply_markup=reply_menu)
        await state.clear()
    else:
        await message.answer("Название категории не может быть пустым.")


@faq_router.message(UpdateStates.get_question)
async def handle_get_update_question_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states UpdateStates.get_question from user {message.chat.id}')
    data = await state.get_data()
    question_id = data.get('question_id')
    lang = data.get('lang', 'ru')
    if not question_id:
        bot_logger.error(f"question_id not found in state for user {message.chat.id} during question update")
        await message.answer("Произошла ошибка обновления.", reply_markup=await get_main_menu(lang, message.chat.id))
        await state.clear()
        return

    question_text = message.text
    if question_text:
        faq = await db.preferences.get_by_key('faq')
        updated = False
        if faq and isinstance(faq.value, dict) and 'questions' in faq.value:
             for idx, question in enumerate(faq.value['questions']):
                 if question.get('question_id') == question_id:
                     faq.value['questions'][idx]['question'] = question_text
                     await db.preferences.update(preference=faq)
                     updated = True
                     break
        if updated:
             user = await db.users.get_by_id(user_id=message.chat.id)
             reply_menu = await get_main_menu(lang=lang, user_id=message.chat.id) # Используем get_main_menu
             await message.answer(text=strs(lang=lang).data_update, reply_markup=reply_menu)
        else:
             await message.answer("Не удалось найти и обновить вопрос.")
        await state.clear()
    else:
        await message.answer(text=strs(lang=lang).faq_ask_question_error)


@faq_router.message(UpdateStates.get_content)
async def handle_get_update_content_state(message: Message, state: FSMContext):
    bot_logger.info(f'Handling states UpdateStates.get_content from user {message.chat.id}')
    data = await state.get_data()
    question_id = data.get('question_id')
    lang = data.get('lang', 'ru')
    if not question_id:
        bot_logger.error(f"question_id not found in state for user {message.chat.id} during content update")
        await message.answer("Произошла ошибка обновления.", reply_markup=await get_main_menu(lang, message.chat.id))
        await state.clear()
        return

    try:
        message_info = loads(dumps(message.model_dump(), cls=CustomJSONEncoder))
        message_info['reply_markup'] = None # Удаляем клавиатуру при обновлении контента
        faq: PreferenceModel | None = await db.preferences.get_by_key('faq')
        updated = False
        if faq and isinstance(faq.value, dict) and 'questions' in faq.value:
             for idx, question in enumerate(faq.value['questions']):
                 if question.get('question_id') == question_id:
                     faq.value['questions'][idx]['content'] = message_info
                     await db.preferences.update(preference=faq)
                     updated = True
                     break
        if updated:
             user = await db.users.get_by_id(user_id=message.chat.id)
             reply_menu = await get_main_menu(lang=lang, user_id=message.chat.id) # Используем get_main_menu
             await message.answer(text=strs(lang=lang).data_update, reply_markup=reply_menu)
        else:
             await message.answer("Не удалось найти и обновить контент вопроса.")
        await state.clear()
    except Exception as e:
        bot_logger.error(f"Error processing content update state for user {message.chat.id}: {e}")
        await message.answer("Произошла ошибка при обновлении контента.")
        await state.clear()