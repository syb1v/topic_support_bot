# Project
from .ru_strs import RuTranslation
from .en_strs import EnTranslation

# Standard
from enum import Enum


class Language(Enum):
    RU = 'ru'
    EN = 'en'


def strs(lang: str):
    match lang:
        case Language.RU.value:
            return RuTranslation
        case Language.EN.value:
            return EnTranslation
    return None


# --- Переменные для кнопок (используются в фильтрах и обработчиках) ---
decline_btn = [RuTranslation.decline_btn, EnTranslation.decline_btn]
# Админские кнопки
delete_tickets_btn = [RuTranslation.delete_tickets_btn, EnTranslation.delete_tickets_btn]
change_faq_btn = [RuTranslation.change_faq_btn, EnTranslation.change_faq_btn]
send_mailing_btn = [RuTranslation.send_mailing_btn, EnTranslation.send_mailing_btn]
start_msg_btn = [RuTranslation.start_msg_btn, EnTranslation.start_msg_btn]
change_close_time_btn = [RuTranslation.change_close_time_btn, EnTranslation.change_close_time_btn]
unk_msg_btn = [RuTranslation.change_unk_message, EnTranslation.change_unk_message]
statistic_btn = [RuTranslation.statistic_btn, EnTranslation.statistic_btn]
working_hours_btn = [RuTranslation.working_hours_btn, EnTranslation.working_hours_btn]
change_subscription_channel_btn = [RuTranslation.change_subscription_channel_btn, EnTranslation.change_subscription_channel_btn] # <--- ИЗМЕНЕНИЕ
# Кнопки менеджера/админа
find_user_btn = [RuTranslation.find_user_btn, EnTranslation.find_user_btn]
opened_tickets_btn = [RuTranslation.opened_tickets_btn, EnTranslation.opened_tickets_btn]
admin_mode_btn = [RuTranslation.admin_mode_btn, EnTranslation.admin_mode_btn]
manager_mode_btn = [RuTranslation.manager_mode_btn, EnTranslation.manager_mode_btn]
admin_take_over_btn = [RuTranslation.admin_take_over_btn, EnTranslation.admin_take_over_btn]
# Кнопки пользователя
faq_btn = [RuTranslation.faq_btn, EnTranslation.faq_btn]
my_tickets_btn = [RuTranslation.my_tickets_btn, EnTranslation.my_tickets_btn]
create_ticket_btn = [RuTranslation.create_ticket_btn, EnTranslation.create_ticket_btn]
# Общие кнопки
choose_lang_btn = [RuTranslation.choose_lang_btn, EnTranslation.choose_lang_btn]
# Новые кнопки
faq_not_found_btn = [RuTranslation.faq_not_found_btn, EnTranslation.faq_not_found_btn]
end_conversation_btn = [RuTranslation.end_conversation_btn, EnTranslation.end_conversation_btn]

# Обновляем общий список reply_buttons (для фильтров)
all_reply_buttons_list = [
    decline_btn, delete_tickets_btn, change_faq_btn, faq_btn, find_user_btn,
    my_tickets_btn, send_mailing_btn, start_msg_btn, change_close_time_btn,
    manager_mode_btn, admin_mode_btn, opened_tickets_btn, create_ticket_btn,
    choose_lang_btn, statistic_btn, unk_msg_btn, end_conversation_btn,
    working_hours_btn,
    change_subscription_channel_btn,
]
reply_buttons = list(set(item for sublist in all_reply_buttons_list for item in sublist))

# Финальный список команд
commands = [
    '/start', '/help', '/create_ticket', '/faq',
    '/opened_tickets', '/search', '/to_admin', '/change_faq',
    '/mailing', '/start_msg', '/change_close_time',
    '/delete_tickets', '/to_manager', '/lang',
    '/working_hours',
    '/change_channel',
]

search_not_found = [RuTranslation.search_not_found, EnTranslation.search_not_found]
user_not_found = [RuTranslation.user_not_found, EnTranslation.user_not_found]