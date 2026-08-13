import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeDefault,
)
from bot import bot, dispatcher
from handlers import all_routers
from handlers import background as back
from database import generate_start_data
from utils.logger import bot_logger
import config as cf

dispatcher.include_routers(*all_routers)

async def start_bot():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        bot_logger.error(f"Failed to delete webhook on start: {e}")

    user_commands = [
        BotCommand(command='start', description='Запустить бота'),
        BotCommand(command='menu', description='Открыть меню'),
        BotCommand(command='help', description='Помощь'),
        BotCommand(command='lang', description='Сменить язык'),
    ]
    private_commands = [
        *user_commands,
        BotCommand(command='bye', description='Предложить закрыть обращение'),
    ]
    try:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())
        await bot.set_my_commands(private_commands, scope=BotCommandScopeAllPrivateChats())
        if cf.GROUP_CHAT_ID:
            await bot.set_my_commands(
                [BotCommand(command='bye', description='Предложить закрыть обращение')],
                scope=BotCommandScopeChat(chat_id=cf.GROUP_CHAT_ID),
            )
        bot_logger.info('Bot command hints configured')
    except Exception as e:
        bot_logger.error(f'Failed to configure bot commands: {e}')
        
    bot_logger.info("Starting polling...")
    await dispatcher.start_polling(
        bot,
        allowed_updates=[
            'message', 'callback_query'
        ]
    )

async def run_app():
    await asyncio.gather(
        generate_start_data(), # Генерируем стартовые данные (настройки) 
    )

# Основная функция запуска
async def main():
    bot_logger.info("Bot starting...")
    await run_app() # Инициализация данных

    # Создаем планировщик
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow") # Устанавливаем часовой пояс

    # Добавляем задачи
    scheduler.add_job(
        back.check_mute,
        trigger='interval',
        minutes=1,
        id='check_mute_job'
    )

    scheduler.add_job(
        back.close_check,
        trigger='interval',
        minutes=30, # Можно изменить интервал проверки авто-закрытия
        id='close_check_job'
    )

    scheduler.add_job(
        back.resolution_prompt_check,
        trigger='interval',
        minutes=1,
        id='resolution_prompt_check_job'
    )

    scheduler.add_job(
        back.notify_delete,
        trigger=CronTrigger(day=1, hour=10, minute=0), # Раз в месяц, 1-го числа в 10:00
        id='notify_delete_job'
    )

    scheduler.start()
    bot_logger.info("Scheduler started.")

    await start_bot()

# Запускаем бот
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        bot_logger.info("Bot stopped.")
    except Exception as e:
        bot_logger.error(f"Unhandled error in main loop: {e}", exc_info=True)
