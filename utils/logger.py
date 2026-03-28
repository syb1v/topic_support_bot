# Standard
import os
import sys
import logging

# Third-party
from loguru import logger

# Project
import config as cf

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logger.remove()

log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"

logger.add(sys.stderr, level="ERROR", format=log_format, colorize=True)

logging_folder = os.path.join(cf.BASE, 'logs')
if not os.path.exists(logging_folder):
    os.makedirs(logging_folder, exist_ok=True)

bot_log_path = os.path.join(logging_folder, 'bot_log.log')
db_log_path = os.path.join(logging_folder, 'database_log.log')
bg_log_path = os.path.join(logging_folder, 'background_log.log')

logger.add(bot_log_path, level="ERROR", format=log_format, rotation="10 MB", retention="7 days", compression="zip", filter=lambda record: record["extra"].get("name") == "bot")
logger.add(db_log_path, level="ERROR", format=log_format, rotation="10 MB", retention="7 days", compression="zip", filter=lambda record: record["extra"].get("name") == "database")
logger.add(bg_log_path, level="ERROR", format=log_format, rotation="10 MB", retention="7 days", compression="zip", filter=lambda record: record["extra"].get("name") == "background")

bot_logger = logger.bind(name="bot")
database_logger = logger.bind(name="database")
background_logger = logger.bind(name="background")

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger('apscheduler').setLevel(logging.WARNING)