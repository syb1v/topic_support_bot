# coding: utf-8
class RuTranslation:
    # Buttons
    yes = 'Да ✅'
    no = 'Нет ❌'
    decline_btn = 'Отмена ❌'
    month_btn_1 = 'От 1️⃣ месяца'
    month_btn_3 = 'От 3️⃣ месяцев'
    month_btn_6 = 'От 6️⃣ месяцев'
    month_btn_12 = 'От года 🗓️'
    update_btn_question = 'Обновить вопрос ❓'
    update_btn_content = 'Обновить контент 📝'
    remove_btn = 'Удалить 🗑️'
    update_btn = 'Обновить 🔄'
    back_btn = 'Назад 🔙'
    rename_btn = 'Переименовать ✏️'
    delete_btn = 'Закрыть 🚫'
    delete_tickets_btn = 'Удалить обращения 🗑️'
    add_btn = 'Добавить ➕'
    add_category_btn = 'Добавить категорию ➕'
    change_faq_btn = 'Изменить FAQ ❓'
    faq_media_skip = 'Далее'
    unk_message = 'Ошибка. Воспользуйтесь командой /help или кнопками в меню.'
    change_unk_message = 'Неизвестная команда 🛑'
    faq_get_buttons = 'Пришлите ссылки и тексты в формате текст-ссылка\ngoogle - google.com\n\nПри нажатии на одну из кнопок ниже, вы удаляете её'
    faq_btn = 'FAQ ❓'
    find_user_btn = 'Найти пользователя 🔎'
    my_tickets_btn = 'Мои обращения 📂'
    user_tickets_btn = 'Обращения пользователя 📂'
    add_faq_media = 'Добавить / Удалить медиа 📷'
    send_mailing_btn = 'Отправить рассылку 📬'
    send_mailing_message_btn = 'Отправить 📨'
    mailing_add_link_btn = 'Добавить ссылку 🌐'
    mailing_delete_btn = 'Убрать меню ❌'
    start_msg_btn = 'Стартовое сообщение 💬'
    change_close_time_btn = 'Изменить время авто закрытия 🕒'
    manager_mode_btn = 'Режим менеджера 💼'
    admin_mode_btn = 'Режим администратора 😎'
    opened_tickets_btn = 'Активные обращения 💬'
    create_ticket_btn = 'Написать менеджеру 💬'
    press_update_btn = ' Нажмите на кнопку "Обновить 🔄"'
    mute_btn = 'Ограничить 🤐'
    history_btn = 'История 💬'
    media_btn = 'Показать медиа 📷'
    ticket_data_btn = 'Данные обращения 🔄'
    archive_btn = 'Архив 🗄️'
    user_info_btn = 'Информация о пользователе ℹ️'
    link_to_topic_btn = 'Перейти к обращению ↗️'
    hide_btn = 'Спрятать 🗂️'
    ban_btn = 'Забанить ⛔'
    unban_btn = 'Разбанить 🟢'
    make_ordinary_btn = 'Сделать обычным пользователем 👤'
    make_manager_btn = 'Сделать менеджером 👨🏻‍💻'
    statistic_btn = 'Статистика 📑'
    choose_lang_btn = 'Eng 🇺🇸'
    faq_not_found_btn = 'Не нашли нужный ответ?'
    admin_take_over_btn = 'Перехватить диалог 👑'

    # Кнопки меню топика
    topic_user_info_button = 'ℹ️ Инфо о пользователе'
    topic_reopen_button = '🔄 Открыть обращение заново'
    topic_close_button = '❌ Закрыть обращение'

    # Список кнопок reply keyboard для разных ролей (устарело)
    reply_buttons_full = [
        decline_btn, delete_tickets_btn, change_faq_btn, faq_btn,
        find_user_btn, my_tickets_btn, send_mailing_btn, start_msg_btn, change_close_time_btn,
        manager_mode_btn, admin_mode_btn, opened_tickets_btn, create_ticket_btn, choose_lang_btn,
        statistic_btn, change_unk_message
    ]

    # Composite
    close_composite = '<b>Обращение закрывается</b>, если последние действие было более {} ч. назад\n\n'
    statistic_composition = '<b>👥 Статистика по активным пользователям:\nЗа 7 дней</b>: {}\n<b>За 30 дней:</b> {}\n<b>За все время:</b> {}\n\n<b>📋 Статистика по активным обращениям:\nЗа 7 дней:</b> {}\n<b>За 30 дней:</b> {}\n<b>За все время:</b> {}\n\n<b>🔒 Среднее время закрытия:\nЗа 30 дней:</b> {} ч {} мин\n<b>За все время:</b> {} ч {} мин'
    ticket_data_composition_new = '<b>Обращение </b>#{}\n\n<b>Создано:</b> {} по МСК\n\n<b>Закрыто:</b> {} по МСК\n\n<b>Имя пользователя:</b> {}\n<b>Email:</b> {}\n<b>Комментарий менеджера:</b> {}'
    manager_accept_ticket_composition = '<b>Менеджер @{} создал обращение #{}!</b>\n\n'
    user_found = '<b>Пользователь найден!</b>'
    current_ticket_info_template = '<b>Обращение</b> #{}\n<b>Пользователь:</b> {}\n<b>Email:</b> {}\n<b>Статус:</b> {}'
    current_ticket_composition = f'<b>Текущее обращение</b>\n\n{{}}'

    # Формат для архива
    tickets_info = lambda is_manager_view: ''.join((
        '<b>Обращение:</b> #{}\n',
        '<b>Создано:</b> {} по МСК\n',
        '<b>Закрыто:</b> {} по МСК\n',
        '<b>Имя пользователя:</b> {}\n',
        '<b>Ссылка:</b> @{}\n',
        '<b>Отвечал менеджер:</b> {}\n' if is_manager_view else '',
        '<b>Время от открытия до закрытия:</b> {} ч, {} мин\n',
        '____________________________________\n\n'))

    user_info = ''.join(('<b>ТГ имя:</b> {}\n\n',
                         '<b>ТГ ID:</b> {}\n\n',
                         '<b>Ссылка:</b> @{}\n\n',
                         '<b>Статус:</b> {}\n\n',
                         '<b>Кол-во обращений (как пользователь):</b> {}\n\n',
                         ))
    user_is_banned = lambda is_banned: f'<b>Забанен ли:</b> {"✔️" if is_banned else "✖️"}\n\n'
    user_restricted = '<b>Запрет на создание обращений до:</b> {}\n\n'
    conversations = lambda upper, len_tickets: f'<b>Архив обращений |{upper}/{len_tickets}|</b>\n\n'
    history_ticket = lambda upper, len_content: f'<i>История обращения</i> <b>|{upper}/{len_content}|</b>\n\n'
    manager_extended = lambda manager_name, message_id, media_group_text: f'<b>🗣️ Менеджер ({manager_name}):</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
    user_extended = lambda user_id, message_id, media_group_text: f'<b>👤 Пользователь ({user_id}):</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
    manager_usual = lambda message_id, media_group_text: f'<b>🗣️ Менеджер:</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
    user_usual = lambda message_id, media_group_text: f'<b>👤 Пользователь:</b>\nID сообщения: {message_id}\nМедиа-группа {media_group_text}\n\n'
    media_files_in_msg = '<i>В данном сообщении присутствует медиафайл!</i>\n\n'
    msg_caption = lambda message_id, media_group_text: f'<b>ID сообщения:</b> {message_id}\n<b>Медиа-группа:</b> {media_group_text}\n\n'
    status_usual = 'обычный пользователь'
    status_manager = 'менеджер'
    status_admin = 'администратор'
    ticket = 'Обращение'
    topic_closed_msg = '❗️ Тема закрыта.'
    topic_reopened_msg = '❗️ Тема вновь открыта.'
    ticket_closed_in_db_msg = '✅ Обращение #{}.{} закрыто в системе.'
    ticket_reopened_in_db_msg = '✅ Обращение #{}.{} открыто в системе.'
    ticket_not_found_for_topic = '❌ Не удалось найти обращение, связанное с этим топиком.'
    topic_invalid_command = '❌ Неверная команда. Доступные команды в топике:\n/close - закрыть обращение и тему\n/menu - управление обращением'
    ticket_active = 'Активно'
    active_tickets_title = lambda upper, len_tickets: f'<b>Активные обращения |{upper}/{len_tickets}|</b>\n\n'

    # Button Messages
    decline_msg = '<b>Действие отменено!</b>'
    use_help = 'Воспользуйтесь кнопками в меню или командой <i>/help</i>, чтобы увидеть доступные команды'

    # Users General
    general_start = '<b>Добро пожаловать! 👋</b>\n\nЭтот бот поможет вам связаться с поддержкой.\n\nВыберите одну из опций ниже или используйте /help для просмотра команд.'
    general_help = ('<b>Список команд:</b> 📃\n\n'
                    '<b>/create_ticket</b> - <i>написать менеджеру</i>\n'
                    '<b>/faq</b> - <i>посмотреть часто задаваемые вопросы</i>\n'
                    '<b>/lang</b> - <i>изменить язык</i>')
    general_lang = '<b>Choose a language!</b>'
    language_updated = 'Язык обновлен!'

    # Users Tickets
    ticket_opened_already = '<b>У Вас уже есть активное обращение!</b>\n\nВы можете писать сообщения прямо здесь.'
    ticket_ask_message = 'Напишите ваше <b>обращение</b>. Вы можете прикрепить фото или документы.'
    ticket_ask_message_error = 'Пожалуйста, отправьте текстовое сообщение или медиафайл.'

    @staticmethod
    def ticket_created_topic_info(ticket_id, user_name, user_id, user_url):
        return (f"🆕 <b>Обращение #{ticket_id} - {user_name}</b>\n\n"
                f"👤 <b>Пользователь:</b> {user_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"🔗 <b>Ссылка:</b> @{user_url}\n"

                f"👇 Первое сообщение ниже:")

    ticket_no_opened = '<b>У Вас нет активных обращений.</b>\n\nНажмите "{}", чтобы создать обращение.'.format(
        'Написать менеджеру 💬')
    ticket_no_opened_manager = '<b>У Вас нет активных обращений для ответа.</b>'
    ticket_opened = '<b>Ваше обращение создано!</b> ✅\n\nМенеджер скоро ответит вам прямо здесь. Вы можете продолжать писать сообщения или отправлять файлы.'

    ticket_closed_by_user = '✅ Ваше обращение закрыто.\n\nВы можете создать новое, нажав "{}"'.format(
        'Написать менеджеру 💬')
    ticket_closed_by_manager = '✅ Ваше обращение закрыто менеджером.\n\nВы можете создать новое, нажав "{}"'.format(
        'Написать менеджеру 💬')
    ticket_reopened_by_manager = '🔄 Ваше обращение вновь открыто менеджером.'
    ticket_no_history = '<b>У обращения нет истории!</b>'
    ticket_no_media_on_page = 'У данных сообщений нет медиафайлов!'

    ticket_empty = 'Нет закрытых обращений!'
    ticket_already_closed = '<b>Обращение уже закрыто!</b>'
    ticket_not_found = 'Обращение не найдено.'

    # Managers Tickets
    ticket_no_opened_tickets = '<b>Нет открытых обращений!</b>'
    ticket_get_mute = 'Пожалуйста, введите сколько <b>минут</b> пользователь не сможет создавать обращения!\n\n<i>Например:</i> 5, 15, 90 и т.д. Либо введите 0, чтобы снять ограничения'
    ticket_get_mute_error = '<b>Некорректный ввод!</b>\n\nВведите целое число минут (от 0 до 1440).'
    ticket_delete_btn = 'Удалить из БД 🗑'

    # Managers Restrictions
    restriction_before = lambda date: f'Вам временно ограничен доступ к созданию обращений до {date} по МСК.'
    restriction_unmuted = '<b>Ограничения сняты!</b>\n\nВы снова можете создавать обращения.'
    restriction_get_muted = lambda mins: f'Вам временно ограничен доступ к созданию обращений на {mins} мин.'
    restriction_successfully = lambda mins: f'<b>Пользователю запрещено создавать обращения на {mins} мин.</b>'
    restriction_unmuted_successfully = '<b>Вы сняли ограничения с пользователя!</b>'
    restriction_banned_forever = '<b>Вы навсегда забанены в этом боте!</b>'
    restriction_unbanned = '<b>Вы разбанены!</b>'
    restriction_banned_successfully = 'Пользователь забанен!'
    restriction_unbanned_successfully = 'Пользователь разбанен!'

    # Manager General
    manager_general_status_updated = '<b>Вы переключились в режим администратора!</b>'
    manager_general_status_updated_error = '<b>Вы не записаны как администратор!</b>'
    manager_general_help = ('<b>Список команд:</b> 📃\n\n'
                            '<b>/opened_tickets</b> - <i>посмотреть активные обращения</i>\n'
                            '<b>/search</b> - <i>найти пользователя по имени/ID</i>\n'
                            '<b>/to_admin</b> - <i>перейти в режим администратора</i>\n'
                            '<b>/faq</b> - <i>посмотреть часто задаваемые вопросы</i>\n'
                            '<b>/lang</b> - <i>изменить язык</i>')

    # Managers User Search
    search_ask_info = 'Пожалуйста, введите <b>телеграмм имя/ID/ссылку</b> пользователя\n\nНапример: <i>765432125</i> или <i>Иван Иванович</i> или <i>@url_user_name</i>'
    search_ask_info_error = '<b>Некорректный ввод!</b>\n\nУбедитесь, правильно ли вы ввели данные? Внимательно посмотрите на пример и попробуйте отправить данные еще раз!'
    search_manager_now = '<b>Пользователь назначен менеджером!</b>\n\nВоспользуйтесь командой <i>/help</i>.'
    search_user_now = '<b>Пользователь сделан обычным пользователем!</b>\n\nВоспользуйтесь командой <i>/help</i>.'
    search_not_found = f'Пользователь не найден!'
    user_not_found = 'Пользователь не найден в базе данных!'

    # Admin General
    admin_general_now_manager = '<b>Вы теперь менеджер!</b>\n\nЧтобы вернуть статус админа воспользуйтесь командой <i>/to_admin</i>'
    admin_general_ask_faq = 'Пожалуйста, введите сообщение <b>FAQ</b>'
    admin_general_ask_faq_error = '<b>Некорректный ввод!</b>\n\nПопробуйте отправить сообщение FAQ еще раз'
    admin_what_to_do_with_message = '<b>Что сделать с этим сообщением?</b>'
    mailing_what_to_do = 'Что сделать с этим сообщением для рассылки?'

    # Admin categories
    admin_category_manage_btn = 'Управлять 📌'
    admin_choose_category = 'Выберите категорию для управления'
    admin_manage_category_composite = 'Выберите действия для редактирования категории <b>«{}»</b>:'
    admin_create_category = 'Введите название для категории'
    admin_create_category_success = 'Категория <b>«{}»</b> успешно создана!'
    admin_delete_category = 'Категория успешно удалена!'
    admin_rename_category_success = 'Теперь категория называется <b>«{}»</b>!'

    # Admin Mailing
    admin_general_ask_mailing_msg = 'Пожалуйста, отправьте <b>сообщение</b>, которое хотите отправить всем пользователям!'
    admin_general_mailing_successful = '<b>Рассылка отправлена пользователям!</b>'
    admin_general_no_users = '<b>Некому отправлять сообщение!</b>'
    admin_mailing_add_link = 'Отправьте <b>название кнопки и ссылку</b> в формате:\n\n<code>Название - https://example.com</code>'
    admin_mailing_add_link_error = '<b>Некорректный ввод!</b>\n\nПопробуйте отправить ссылку еще раз'

    # NEW/UPDATED
    admin_save_btn = 'Сохранить ✅'
    admin_add_link_btn = 'Добавить кнопку-ссылку 🌐'
    admin_remove_keyboard_btn = 'Удалить кнопки ❌'
    admin_keyboard_removed = '<b>Клавиатура удалена.</b> Вы можете добавить новые кнопки или сохранить сообщение.'
    admin_link_added = '✅ <b>Кнопка добавлена.</b> Вы можете добавить еще или сохранить сообщение.'
    admin_ask_link_text = 'Отправьте <b>название кнопки и ссылку</b> в формате:\n\n<code>Название - https://example.com</code>'
    admin_invalid_link_format = '<b>❌ Неверный формат.</b>\n\nПожалуйста, отправьте данные в формате:\n<code>Название - https://example.com</code>'

    # Admin Help
    admin_general_help = ('<b>Список команд:</b> 📃\n\n'
                          '<b>/change_faq</b> - <i>изменить часто задаваемые вопросы</i>\n'
                          '<b>/search</b> - <i>найти пользователя по имени/ID</i>\n'
                          '<b>/opened_tickets</b> - <i>посмотреть активные обращения</i>\n'
                          '<b>/mailing</b> - <i>отправить рассылку всем пользователям</i>\n'
                          '<b>/start_msg</b> - <i>изменить стартовое сообщение</i>\n'
                          '<b>/change_close_time</b> - <i>изменить время авто закрытия обращений</i>\n'
                          '<b>/delete_tickets</b> - <i>удалить обращения по промежутку времени (месяцы)</i>\n'
                          '<b>/to_manager</b> - <i>перейти в режим менеджера</i>\n'
                          '<b>/lang</b> - <i>изменить язык</i>')

    # Admin FAQ
    faq_ask_question = 'Пожалуйста, введите <b>вопрос</b> для отображения в inline режиме. Желательно коротко\n\nНапример: Какая стоимость доставки?'
    faq_ask_question_error = '<b>Некорректный ввод!</b>\n\nПопробуйте отправить вопрос еще раз'
    faq_ask_category = '<b>Выберите категорию из списка ниже</b>'
    faq_ask_content = '<b>Отправьте сообщение</b>, которое будет отображаться при выборе данного вопроса. Вы также можете использовать медиа-материалы'
    faq_ask_content_error = '<b>Некорректный ввод!</b>\n\nПопробуйте отправить текст еще раз'
    faq_added = '<b>Вопрос добавлен!</b>\n\nВоспользуйтесь <i>/faq</i>, чтобы увидеть изменения'
    faq_questions = '<b>Доступные вопросы</b>'

    # Admin Unknown Cmd
    admin_unk_current = '<b>Текущее сообщение при неизвестной команде:</b>'
    admin_unk_ask_msg = 'Пожалуйста, отправьте <b>новое сообщение</b>, которое будут видеть пользователи при вводе неизвестной команды.'
    admin_unk_message_saved = '✅ <b>Сообщение для неизвестной команды успешно сохранено!</b>'

    # Admin Start Msg
    admin_start_current = '<b>Текущее стартовое сообщение:</b>'
    admin_start_ask_msg = 'Пожалуйста, отправьте <b>новое стартовое сообщение</b>, которое будут видеть пользователи.'
    admin_start_message_saved = '✅ <b>Стартовое сообщение успешно сохранено!</b>'

    # Admin Close Time
    admin_close_ask_time = 'Пожалуйста, отправьте <b>кол-во часов</b>, через которое обращение будет автоматически закрыто при неактивности:'
    admin_close_ask_time_error = '<b>Некорректный ввод!</b>\n\nВведите целое число часов.'
    admin_close_updated = '<b>Вы обновили время автозакрытия обращения!</b>'

    # Admin Delete Tickets
    admin_delete = '<b>Выберите соответствующее время для удаления устаревших обращений</b>\n\nТакже Вы можете отключить/включить уведомления, которые приходят каждый месяц, как напоминание об очистке'
    admin_delete_sure = '<b>Вы уверены, что хотите удалить обращения?</b> Найдено: {}'
    admin_delete_tickets = lambda count: f'Кол-во удаленных обращений: {count}'

    # Background
    last_modified_outdated = lambda \
            time: f'<b>Обращение закрылось автоматически, так как прошло более {time} ч. с последнего сообщения!</b>\n\nИсторию можно посмотреть в архиве (если доступно).'

    # Ticket status translations
    ticket_created_date = 'Дата создания обращения'
    ticket_status = 'Статус обращения'
    ticket_occupied_by_manager = 'Отвечает менеджер {}'
    ticket_free = 'Ожидает ответа'
    ticket_closed = 'Закрыто'
    moscow_time = 'по МСК'

    faq_button_text = "ЧАВО ❓"
    end_conversation_btn = "Завершить обращение 🏁"

    # --- ГРАФИК РАБОТЫ ---
    working_hours_btn = "График работы 🕒"
    working_hours_menu_title = "Настройка графика работы поддержки"
    current_working_hours_info = "<b>Текущие настройки:</b>"
    working_hours_set = "Время: <code>{start_time} - {end_time}</code> (МСК)"
    working_days_set = "Рабочие дни: {days}"
    exceptions_set = "Даты-исключения: {dates}"
    no_settings_found = "<i>Настройки графика еще не заданы.</i>"
    ask_working_hours = (
        'Пожалуйста, пришлите <b>время начала и конца</b> рабочего дня по Москве в формате <b>ЧЧ:ММ - ЧЧ:ММ</b>.\n\n'
        '<i>Пример: 09:00 - 18:30</i>')
    ask_working_hours_error = "<b>Неверный формат времени!</b>\n\nПожалуйста, введите время в формате <b>ЧЧ:ММ - ЧЧ:ММ</b> (например, 09:00 - 18:00)."
    ask_working_days = "Выберите <b>рабочие дни недели</b>. Нажмите 'Далее', когда закончите."
    # Дни недели
    monday = "Пн"
    tuesday = "Вт"
    wednesday = "Ср"
    thursday = "Чт"
    friday = "Пт"
    saturday = "Сб"
    sunday = "Вс"
    working_days_display = "Выбранные рабочие дни: <b>{days_str}</b>"
    no_working_days_selected = "<i>Рабочие дни не выбраны.</i>"
    next_btn = "Далее ➡️"
    ask_exception_dates = ('Теперь пришлите <b>нерабочие даты</b> (праздники, выходные) в формате <b>ДД.ММ.ГГГГ</b>.\n'
                           'Если дат несколько, перечислите их через запятую.\n'
                           'Если исключений нет, просто нажмите "Пропустить".\n\n'
                           '<i>Пример: 01.01.2024, 08.03.2024, 01.05.2024</i>')
    skip_btn = "Пропустить ⏩"
    ask_exception_dates_error = "<b>Неверный формат даты!</b>\n\nПожалуйста, введите дату(ы) в формате <b>ДД.ММ.ГГГГ</b>, разделяя их запятыми, или нажмите 'Пропустить'."
    working_hours_saved = "✅ График работы успешно сохранен!"
    working_hours_cancelled = "❌ Настройка графика работы отменена."

    support_schedule_info = "\n\n🕒 <b>График работы поддержки:</b> {schedule_text}"
    working_hours_display = "{days_str} с {start_time} до {end_time} (МСК)"
    non_working_hours_notice = "\n\n⚠️ Обратите внимание: сейчас нерабочее время. Менеджер ответит вам в ближайший рабочий день."
    schedule_not_set = "График работы не задан."
    not_set = "Не задано"
    none = "Нет"

    # Middleware
    middle_check_channel = 'Для продолжения, пожалуйста, подпишитесь на наш канал. После подписки нажмите кнопку "Проверить подписку".'
    # Users channel
    channel_subscribed = '✅ Спасибо за подписку! Теперь вы можете пользоваться всеми функциями бота.'
    channel_unsubscribed = 'Вы все еще не подписаны. Пожалуйста, подпишитесь на канал.'
    check_subscription_btn = 'Проверить подписку 🔔'
    # Admin channel
    change_subscription_channel_btn = 'Канал подписки 🌐'
    admin_channel_ask_channel_url = 'Пожалуйста, введите <b>новую ссылку</b> на канал.\n\n<b>Важно:</b> бот должен быть администратором в этом канале с правом на добавление участников.'
    admin_channel_ask_channel_url_error = '<b>Ошибка!</b> Пожалуйста, отправьте корректную ссылку на канал (например, https://t.me/durov).'
    admin_channel_ask_channel_id = 'Отлично! Теперь, пожалуйста, <b>перешлите любое сообщение</b> из этого канала, чтобы я мог получить его ID.'
    admin_channel_ask_channel_id_error = '<b>Ошибка!</b> Пожалуйста, именно перешлите сообщение из нужного канала.'
    admin_channel_ask_button_name = 'Введите новое название для кнопки подписки (например, "Вступить в сообщество").'
    admin_channel_ask_button_name_error = '<b>Ошибка!</b> Название кнопки не может быть пустым или слишком длинным.'
    admin_channel_button_name_updated = '✅ Название кнопки обновлено!'
    admin_channel_updated_info = lambda \
            url: f'<b>Внимание!</b> Канал для обязательной подписки был изменен. Пожалуйста, подпишитесь на новый канал, чтобы продолжить: {url}'
    admin_channel_on = '✅ Проверка подписки включена'
    admin_channel_off = '❌ Проверка подписки выключена'
    change_channel_info_btn = 'Изменить канал 🔄'
    admin_channel_updated = '✅ <b>Канал обязательной подписки успешно изменён!</b>'
    change_channel_button_name_btn = 'Изменить название кнопки ✏️'
    make_subscription_necessary_btn = 'Включить проверку подписки 🔔'
    make_subscription_unnecessary_btn = 'Выключить проверку подписки 🔕'
    remove_menu_btn = 'Закрыть меню 🚫'

    @staticmethod
    def admin_channel_info(id_, url, button_name):
        return f'<b>Настройки обязательной подписки:</b>\n\n<b>Канал:</b> {url}\n<b>ID канала:</b> <code>{id_}</code>\n<b>Текст кнопки:</b> "{button_name}"'