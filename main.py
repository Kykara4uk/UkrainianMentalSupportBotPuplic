

from aiogram import executor

import handlers
import variables






import postgres
async def on_startup(dispatcher):


    await postgres.startup()
    await set_bot_commands()
    await handlers.kykara4a()
    settings = await postgres.get_settings()
    variables.queue_scan_job_id = variables.scheduler.add_job(handlers.scan_queue, 'interval', seconds=settings.queue_scan_timer).id
    variables.dashboard_scan_job_id = variables.scheduler.add_job(handlers.dashboard, 'interval', seconds=settings.dashboard_scan_timer).id
    #print(queue_scan_job_id)
    variables.scheduler.start()
    print("Bot started")





if __name__ == '__main__':
    from handlers import dp, set_bot_commands

    executor.start_polling(dp, on_startup=on_startup)


