# coding: utf-8
class EnTranslation:
    # Buttons
    yes = 'Yes ✅'
    no = 'No ❌'
    decline_btn = 'Cancel ❌'
    month_btn_1 = 'From 1️⃣ month'
    month_btn_3 = 'From 3️⃣ months'
    month_btn_6 = 'From 6️⃣ months'
    month_btn_12 = 'From year 🗓️'
    update_btn_question = 'Update question ❓'
    update_btn_content = 'Update content 📝'
    remove_btn = 'Delete 🗑️'
    update_btn = 'Update 🔄'
    back_btn = 'Back 🔙'
    rename_btn = 'Rename ✏️'
    delete_btn = 'Close 🚫'
    delete_tickets_btn = 'Delete requests 🗑️'
    add_btn = 'Add ➕'
    add_category_btn = 'Add category ➕'
    change_faq_btn = 'Change FAQ ❓'
    faq_media_skip = 'Continue'
    unk_message = 'Error. Use the /help command or buttons in the menu.'
    change_unk_message = 'Unknown command 🛑'
    faq_get_buttons = 'Send URL and description in format text-url\ngoogle - google.com\n\nIf you click on one button below, you delete it'
    faq_btn = 'FAQ ❓'
    find_user_btn = 'Find user 🔎'
    my_tickets_btn = 'My requests 📂'
    user_tickets_btn = 'User requests 📂'
    add_faq_media = 'Add / Remove media 📷'
    send_mailing_btn = 'Send mailing 📬'
    send_mailing_message_btn = 'Send 📨'
    mailing_add_link_btn = 'Add link 🌐'
    mailing_delete_btn = 'Remove menu ❌'
    start_msg_btn = 'Start message 💬'
    change_close_time_btn = 'Change auto-closing time 🕒'
    manager_mode_btn = 'Manager mode 💼'
    admin_mode_btn = 'Admin mode 😎'
    opened_tickets_btn = 'Active requests 💬'
    create_ticket_btn = 'Write to manager 💬'
    press_update_btn = ' Click on the "Update 🔄" button'
    mute_btn = 'Restrict 🤐'
    history_btn = 'History 💬'
    media_btn = 'Show media 📷'
    ticket_data_btn = 'Request data 🔄'
    archive_btn = 'Archive 🗄️'
    user_info_btn = 'User information ℹ️'
    link_to_topic_btn = 'Go to request ↗️'
    hide_btn = 'Hide 🗂️'
    ban_btn = 'Ban ⛔'
    unban_btn = 'Unban 🟢'
    make_ordinary_btn = 'Make regular user 👤'
    make_manager_btn = 'Make manager 👨🏻‍💻'
    statistic_btn = 'Statistics 📑'
    choose_lang_btn = 'Рус 🇷🇺'
    faq_not_found_btn = 'Did not find the answer?'
    admin_take_over_btn = 'Take over dialog 👑'

    # Topic menu buttons
    topic_user_info_button = 'ℹ️ User Info'
    topic_reopen_button = '🔄 Reopen Request'
    topic_close_button = '❌ Close Request'

    # Reply buttons list (obsolete, but keep for now)
    reply_buttons_full = [
        decline_btn, delete_tickets_btn, change_faq_btn, faq_btn,
        find_user_btn, my_tickets_btn, send_mailing_btn, start_msg_btn, change_close_time_btn,
        manager_mode_btn, admin_mode_btn, opened_tickets_btn, create_ticket_btn, choose_lang_btn,
        statistic_btn, change_unk_message
    ]

    # Composite
    close_composite = '<b>The request closes</b> if the last action was more than {} hours ago\n\n'
    ticket_data_composition_new = '<b>Request </b>#{}\n\n<b>Created:</b> {} Moscow time\n\n<b>Closed:</b> {} Moscow time\n\n<b>User name:</b> {}\n<b>Email:</b> {}\n<b>Manager comment:</b> {}'
    statistic_composition = '<b>👥 Statistics for active users:\nFor 7 days</b>: {}\n<b>For 30 days:</b> {}\n<b>For all time:</b> {}\n\n<b>📋 Statistics for active requests:\nFor 7 days:</b> {}\n<b>For 30 days:</b> {}\n<b>For all time:</b> {}\n\n<b>🔒 Average closure time:\nFor 30 days:</b> {} hours {} minutes\n<b>For all time:</b> {} hours {} minutes'
    manager_accept_ticket_composition = '<b>Manager @{} created request #{}!</b>\n\n'
    user_found = '<b>User found!</b>'
    current_ticket_info_template = '<b>Request</b> #{}\n<b>User:</b> {}\n<b>Email:</b> {}\n<b>Status:</b> {}'
    current_ticket_composition = f'<b>Current request</b>\n\n{{}}'

    # Archive format
    tickets_info = lambda is_manager_view: ''.join((
        '<b>Request:</b> #{}\n',
        '<b>Created:</b> {} Moscow time\n',
        '<b>Closed:</b> {} Moscow time\n',
        '<b>User name:</b> {}\n',
        '<b>Link:</b> @{}\n',
        '<b>Manager replied:</b> {}\n' if is_manager_view else '',
        '<b>Duration:</b> {} h, {} min\n',
        '____________________________________\n\n'))

    user_info = ''.join(('<b>TG name:</b> {}\n\n',
                         '<b>TG ID:</b> {}\n\n',
                         '<b>Link:</b> @{}\n\n',
                         '<b>Status:</b> {}\n\n',
                         '<b>Requests (as user):</b> {}\n\n',
                         ))
    user_is_banned = lambda is_banned: f'<b>Is user banned:</b> {" ✔️ " if is_banned else " ✖️ "}\n\n'
    user_restricted = '<b>Request creation restricted until:</b> {}\n\n'
    conversations = lambda upper, len_tickets: f'<b>Requests Archive |{upper}/{len_tickets}|</b>\n\n'
    history_ticket = lambda upper, len_content: f'<i>Request History</i> <b>|{upper}/{len_content}|</b>\n\n'
    manager_extended = lambda manager_name, message_id, media_group_text: f'<b> 🗣️ Manager ({manager_name}):</b>\nMessage ID: {message_id}\nMedia group: {media_group_text}\n\n'
    user_extended = lambda user_id, message_id, media_group_text: f'<b> 👤 User ({user_id}):</b>\nMessage ID: {message_id}\nMedia group: {media_group_text}\n\n'
    manager_usual = lambda message_id, media_group_text: f'<b> 🗣️ Manager:</b>\nMessage ID: {message_id}\nMedia group {media_group_text}\n\n'
    user_usual = lambda message_id, media_group_text: f'<b> 👤 User:</b>\nMessage ID: {message_id}\nMedia group {media_group_text}\n\n'
    media_files_in_msg = '<i>This message contains media!</i>\n\n'
    msg_caption = lambda message_id, media_group_text: f'<b>Message ID:</b> {message_id}\n<b>Media Group:</b> {media_group_text}\n\n'
    status_usual = 'regular user'
    status_manager = 'manager'
    status_admin = 'administrator'
    ticket = 'Request'
    topic_closed_msg = '❗️ Topic closed.'
    topic_reopened_msg = '❗️ Topic reopened.'
    ticket_closed_in_db_msg = '✅ Request #{}.{} closed in system.'
    ticket_reopened_in_db_msg = '✅ Request #{}.{} reopened in system.'
    ticket_not_found_for_topic = '❌ Could not find the request associated with this topic.'
    topic_invalid_command = '❌ Invalid command. Available commands in topic:\n/close - close request and topic\n/menu - manage request'
    ticket_active = 'Active'
    active_tickets_title = lambda upper, len_tickets: f'<b>Active Requests |{upper}/{len_tickets}|</b>\n\n'

    # Button Messages
    decline_msg = '<b>Action cancelled!</b>'
    use_help = 'Use the menu buttons or <i>/help</i> command to see the available commands.'

    # Users General
    general_start = '<b>Welcome! 👋</b>\n\nThis bot helps you contact support.\n\nChoose an option below or use /help to see commands.'
    general_help = ('<b>List of commands:</b> 📃\n\n'
                    '<b>/create_ticket</b> - <i>write to manager</i>\n'
                    '<b>/faq</b> - <i>view frequently asked questions</i>\n'
                    '<b>/lang</b> - <i>change language</i>')
    general_lang = '<b>Выберите язык!</b>'
    language_updated = 'Language updated!'

    # Users Tickets
    ticket_opened_already = '<b>You already have an active request!</b>\n\nYou can write messages right here.'

    ticket_ask_message = 'Write your <b>request message</b>. You can attach photos or documents.'
    ticket_ask_message_error = 'Please send a text message or a media file.'

    @staticmethod
    def ticket_created_topic_info(ticket_id, user_name, user_id, user_url):
        return (f"🆕 <b>Request #{ticket_id} - {user_name}</b>\n\n"
                f"👤 <b>User:</b> {user_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"🔗 <b>Link:</b> @{user_url}\n"

                f"👇 First message below:")

    ticket_no_opened = '<b>You do not have an active request.</b>\n\nPress "{}" to create one.'.format(
        'Write to manager 💬')
    ticket_no_opened_manager = '<b>You do not have any active requests to answer.</b>'
    ticket_opened = '<b>Your request has been created!</b> ✅\n\nA manager will reply to you right here soon. You can continue sending messages or files.'

    ticket_closed_by_user = '✅ Your request has been closed.\n\nYou can create a new one by pressing "{}"'.format(
        'Write to manager 💬')
    ticket_closed_by_manager = '✅ Your request has been closed by the manager.\n\nYou can create a new one by pressing "{}"'.format(
        'Write to manager 💬')
    ticket_reopened_by_manager = '🔄 Your request has been reopened by the manager.'
    ticket_no_history = '<b>The request has no history!</b>'
    ticket_no_media_on_page = 'These messages do not have media files!'

    ticket_empty = 'There are no closed requests!'
    ticket_already_closed = 'The request is already closed!'
    ticket_not_found = 'Request not found.'

    # Managers Tickets
    ticket_no_opened_tickets = '<b>There are no open requests!</b>'
    ticket_get_mute = 'Please enter how many <b>minutes</b> the user will not be able to create requests!\n\n<i>Example:</i> 5, 15, 90, etc. Or enter 0 to remove restrictions.'
    ticket_get_mute_error = '<b>Incorrect input!</b>\n\nEnter an integer number of minutes (0 to 1440).'
    ticket_delete_btn = 'Delete from DB 🗑'

    # Managers Restrictions
    restriction_before = lambda \
        date: f' You are temporarily restricted from creating requests until {date} Moscow time.'
    restriction_unmuted = '<b>Restrictions lifted!</b>\n\nYou can create requests again.'
    restriction_get_muted = lambda mins: f' You are temporarily restricted from creating requests for {mins} min.'
    restriction_successfully = lambda mins: f'<b>User restricted from creating requests for {mins} min.</b>'
    restriction_unmuted_successfully = '<b>You have removed restrictions from the user!</b>'
    restriction_banned_forever = '<b>You are permanently banned from this bot!</b>'
    restriction_unbanned = '<b>You have been unbanned!</b>'
    restriction_banned_successfully = 'User banned!'
    restriction_unbanned_successfully = 'User unbanned!'

    # Manager General
    manager_general_status_updated = '<b>You have switched to admin mode!</b>'
    manager_general_status_updated_error = '<b>You are not registered as an administrator!</b>'
    manager_general_help = ('<b>List of commands:</b> 📃\n\n'
                            '<b>/opened_tickets</b> - <i>view active requests</i>\n'
                            '<b>/search</b> - <i>find a user by name/ID</i>\n'
                            '<b>/to_admin</b> - <i>switch to administrator mode</i>\n'
                            '<b>/faq</b> - <i>view frequently asked questions</i>\n'
                            '<b>/lang</b> - <i>change language</i>')

    # Managers User Search
    search_ask_info = 'Please enter user\'s <b>telegram name/ID/link</b>\n\nExample: <i>765432125</i> or <i>John Doe</i> or <i>@username</i>'
    search_ask_info_error = '<b>Incorrect input!</b>\n\nCheck the example and try sending the data again!'
    search_manager_now = '<b>User set as manager!</b>\n\n Use the <i>/help</i> command.'
    search_user_now = '<b>User set as regular user!</b>\n\n Use the <i>/help</i> command.'
    search_not_found = f'User not found!'
    user_not_found = 'User not found in the database!'

    # Admin General
    admin_general_now_manager = '<b>You are now a manager!</b>\n\n To return to admin status, use the command <i>/to_admin</i>'
    admin_general_ask_faq = 'Please enter the <b>FAQ</b> message'
    admin_general_ask_faq_error = '<b>Incorrect input!</b>\n\nTry sending the FAQ message again'
    admin_what_to_do_with_message = '<b>What should be done with this message?</b>'
    mailing_what_to_do = 'What should be done with this message for mailing?'

    # Admin categories
    admin_category_manage_btn = 'Manage 📌'
    admin_choose_category = 'Choose a category to manage'
    admin_manage_category_composite = 'Select actions to edit category <b>«{}»</b>:'
    admin_create_category = 'Enter a name for the new category'
    admin_create_category_success = 'Category <b>«{}»</b> successfully created!'
    admin_delete_category = 'Category successfully deleted!'
    admin_rename_category_success = 'The category is now called <b>«{}»</b>!'

    # Admin Mailing
    admin_general_ask_mailing_msg = 'Please send the <b>message</b> you want to send to all users!'
    admin_general_mailing_successful = '<b>Mailing sent to users!</b>'
    admin_general_no_users = '<b>No one to send the message to!</b>'
    admin_mailing_add_link = 'Send <b>the name of the button and the link</b> in the format:\n\n<code>Name - https://example.com </code>'
    admin_mailing_add_link_error = '<b>Incorrect input!</b>\n\nTry sending the link again'

    # NEW/UPDATED
    admin_save_btn = 'Save ✅'
    admin_add_link_btn = 'Add URL Button 🌐'
    admin_remove_keyboard_btn = 'Remove Buttons ❌'
    admin_keyboard_removed = '<b>Keyboard has been removed.</b> You can add new buttons or save the message.'
    admin_link_added = '✅ <b>Button added.</b> You can add more buttons or save the message.'
    admin_ask_link_text = 'Send the <b>button name and link</b> in the format:\n\n<code>Name - https://example.com</code>'
    admin_invalid_link_format = '<b>❌ Invalid format.</b>\n\nPlease send the data in the format:\n<code>Name - https://example.com</code>'

    # Admin Help
    admin_general_help = ('<b>List of commands:</b> 📃 \n\n'
                          '<b>/change_faq</b> - <i>change frequently asked questions</i>\n'
                          '<b>/search</b> - <i>find a user by name/ID</i>\n'
                          '<b>/opened_tickets</b> - <i>view open requests</i>\n'
                          '<b>/mailing</b> - <i>send a mailing to all users</i>\n'
                          '<b>/start_msg</b> - <i>change the start message</i>\n'
                          '<b>/change_close_time</b> - <i>change the time of auto closing requests</i>\n'
                          '<b>/delete_tickets</b> - <i>delete requests by time interval (months)</i>\n'
                          '<b>/to_manager</b> - <i>switch to manager mode</i>\n'
                          '<b>/lang</b> - <i>change language</i>')

    # Admin FAQ
    faq_ask_question = 'Please enter the <b>question</b> for inline display. Preferably short\n\nExample: What is the shipping cost?'
    faq_ask_question_error = '<b>Incorrect input!</b>\n\nTry submitting the question again'
    faq_ask_category = '<b>Choose category from the list below</b>'
    faq_ask_content = '<b>Send the message</b> to be displayed for this question. You can also use media.'
    faq_ask_content_error = '<b>Incorrect input!</b>\n\nTry sending the text again'
    faq_added = '<b>Question added!</b>\n\n Use <i>/faq</i> to see the changes'
    faq_questions = '<b>Available questions</b>'

    # Admin Unknown Cmd
    admin_unk_current = '<b>Current message for unknown command:</b>'
    admin_unk_ask_msg = 'Please send the <b>new message</b> that users will see for an unknown command.'
    admin_unk_message_saved = '✅ <b>Message for unknown command has been saved successfully!</b>'

    # Admin Start Msg
    admin_start_current = '<b>Current start message:</b>'
    admin_start_ask_msg = 'Please send the <b>new start message</b> that users will see.'
    admin_start_message_saved = '✅ <b>Start message has been saved successfully!</b>'

    # Admin Close Time
    admin_close_ask_time = 'Please send the <b>number of hours</b> after which an inactive request will be automatically closed:'
    admin_close_ask_time_error = '<b>Incorrect input!</b>\n\nEnter an integer number of hours.'
    admin_close_updated = '<b>Auto-closing time updated!</b>'

    # Admin Delete Tickets
    admin_delete = '<b>Select the appropriate time to delete outdated requests</b>\n\nYou can also disable/enable notifications that come every month as a reminder to clean up'
    admin_delete_sure = '<b>Are you sure you want to delete requests?</b> Found: {}'
    admin_delete_tickets = lambda count: f' Number of deleted records: {count}'

    # Background
    last_modified_outdated = lambda \
            time: f'<b>The request was closed automatically because more than {time} hours have passed since the last message!</b>\n\nHistory can be viewed in the archive (if available).'

    # Ticket status translations
    ticket_created_date = 'Creation date'
    ticket_status = 'Status'
    ticket_occupied_by_manager = 'Manager {} is replying'
    ticket_free = 'Waiting for reply'
    ticket_closed = 'Closed'
    moscow_time = 'Moscow time'

    faq_button_text = "FAQ ❓"
    end_conversation_btn = "End request 🏁"

    # --- WORKING HOURS ---
    working_hours_btn = "Working Hours 🕒"
    working_hours_menu_title = "Support Working Hours Setup"
    current_working_hours_info = "<b>Current Settings:</b>"
    working_hours_set = "Time: <code>{start_time} - {end_time}</code> (Moscow Time)"
    working_days_set = "Working days: {days}"
    exceptions_set = "Exception dates: {dates}"
    no_settings_found = "<i>Schedule settings not configured yet.</i>"
    ask_working_hours = (
        'Please send the <b>start and end time</b> of the working day (Moscow Time) in <b>HH:MM - HH:MM</b> format.\n\n'
        '<i>Example: 09:00 - 18:30</i>')
    ask_working_hours_error = "<b>Invalid time format!</b>\n\nPlease enter the time in <b>HH:MM - HH:MM</b> format (e.g., 09:00 - 18:00)."
    ask_working_days = "Select the <b>working days of the week</b>. Press 'Next' when done."
    # Days of the week
    monday = "Mon"
    tuesday = "Tue"
    wednesday = "Wed"
    thursday = "Thu"
    friday = "Fri"
    saturday = "Sat"
    sunday = "Sun"
    working_days_display = "Selected working days: <b>{days_str}</b>"
    no_working_days_selected = "<i>No working days selected.</i>"
    next_btn = "Next ➡️"
    ask_exception_dates = ('Now send the <b>non-working dates</b> (holidays, days off) in <b>DD.MM.YYYY</b> format.\n'
                           'If there are multiple dates, list them separated by commas.\n'
                           'If there are no exceptions, just press "Skip".\n\n'
                           '<i>Example: 01.01.2024, 08.03.2024, 01.05.2024</i>')
    skip_btn = "Skip ⏩"
    ask_exception_dates_error = "<b>Invalid date format!</b>\n\nPlease enter date(s) in <b>DD.MM.YYYY</b> format, separated by commas, or press 'Skip'."
    working_hours_saved = "✅ Working hours saved successfully!"
    working_hours_cancelled = "❌ Working hours setup cancelled."

    support_schedule_info = "\n\n🕒 <b>Support Working Hours:</b> {schedule_text}"
    working_hours_display = "{days_str} from {start_time} to {end_time} (Moscow Time)"
    non_working_hours_notice = "\n\n⚠️ Please note: It is currently outside of working hours. A manager will respond to you on the next working day."
    schedule_not_set = "Working hours are not set."
    not_set = "Not set"
    none = "None"

    # Middleware
    middle_check_channel = 'To continue, please subscribe to our channel. After subscribing, press the "Check Subscription" button.'
    # Users channel
    channel_subscribed = '✅ Thank you for subscribing! You can now use all the features of the bot.'
    channel_unsubscribed = 'You are still not subscribed. Please subscribe to the channel.'
    check_subscription_btn = 'Check Subscription 🔔'
    # Admin channel
    change_subscription_channel_btn = 'Subscription Channel 🌐'
    admin_channel_ask_channel_url = 'Please enter the <b>new link</b> to the channel.\n\n<b>Important:</b> The bot must be an administrator in this channel with the right to add members.'
    admin_channel_ask_channel_url_error = '<b>Error!</b> Please send a valid channel link (e.g., https://t.me/durov).'
    admin_channel_ask_channel_id = 'Great! Now, please <b>forward any message</b> from that channel so I can get its ID.'
    admin_channel_ask_channel_id_error = '<b>Error!</b> Please forward a message from the correct channel.'
    admin_channel_ask_button_name = 'Enter the new name for the subscription button (e.g., "Join Community").'
    admin_channel_ask_button_name_error = '<b>Error!</b> The button name cannot be empty or too long.'
    admin_channel_button_name_updated = '✅ Button name updated!'
    admin_channel_updated = '✅ <b>Канал обязательной подписки успешно изменён!</b>'
    admin_channel_on = '✅ Subscription check is now ON'
    admin_channel_off = '❌ Subscription check is now OFF'
    change_channel_info_btn = 'Change Channel 🔄'
    change_channel_button_name_btn = 'Change Button Name ✏️'
    make_subscription_necessary_btn = 'Enable Subscription Check 🔔'
    make_subscription_unnecessary_btn = 'Disable Subscription Check 🔕'
    remove_menu_btn = 'Close Menu 🚫'

    @staticmethod
    def admin_channel_updated_info(url):
        return f'<b>Attention!</b> The required subscription channel has been changed. Please subscribe to the new channel to continue: {url}'

    @staticmethod
    def admin_channel_info(id_, url, button_name):
        return f'<b>Subscription Settings:</b>\n\n<b>Channel:</b> {url}\n<b>Channel ID:</b> <code>{id_}</code>\n<b>Button Text:</b> "{button_name}"'