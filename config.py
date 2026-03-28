import os
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))

project = {
    'base': BASE,
    'storage': BASE + '/storage'
}

BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPERGROUP_ID = os.getenv('SUPERGROUP_ID')


bot = {
    'token': BOT_TOKEN,
}

# Преобразуем SUPERGROUP_ID в число, если он задан
try:
    SUPERGROUP_ID = int(SUPERGROUP_ID)
except (ValueError, TypeError):
    print("Warning: SUPERGROUP_ID не является числом или не задан. Используется значение по умолчанию.")
    SUPERGROUP_ID = -100


# Список администраторов
admin_ids = [6499614618] # можно перечислить ids через запятую

try:
    GROUP_CHAT_ID = int(SUPERGROUP_ID)
except ValueError:
    print("Ошибка: SUPERGROUP_ID должен быть числовым значением.")
    GROUP_CHAT_ID = None

# Убедитесь, что storage директория существует
storage_path = project['storage']
if not os.path.exists(storage_path):
    os.makedirs(storage_path)
    print(f"Создана директория: {storage_path}")
