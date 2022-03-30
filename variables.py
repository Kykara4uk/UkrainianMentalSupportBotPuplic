from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import data
from IsAnswerFilter import IsAnswerFilter
from lang_middleware import setup_middleware

tg_token = data.token

storage = MemoryStorage()
bot = Bot(token=tg_token, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
dp.filters_factory.bind(IsAnswerFilter, event_handlers=[dp.message_handlers])

i18n = setup_middleware(dp)
_ = i18n.gettext
scheduler = AsyncIOScheduler(timezone="Europe/Kiev")
dashboard_scan_job_id = None
queue_scan_job_id = None