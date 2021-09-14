from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook

import os

API_TOKEN = os.getenv('TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
BOT_TOKEN = os.getenv('TOKEN')

# webhook settings
#WEBHOOK_HOST = 'https://your.domain'
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
#WEBHOOK_PATH = '/path/to/api'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = 'localhost'  # or ip
#WEBAPP_PORT = 3001
PORT = int(os.environ.get('PORT', '8443'))
WEBAPP_PORT = int(os.getenv('PORT'))

#    WEBAPP_HOST = '0.0.0.0'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
#dp.middleware.setup(LoggingMiddleware())

@dp.message_handler()
async def echo(message: types.Message):
    # Regular request
    # await bot.send_message(message.chat.id, message.text)

    # or reply INTO webhook
    return SendMessage(message.chat.id, message.text)


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start


async def on_shutdown(dp):
    # insert code here to run it before shutdown

    # Remove webhook (not acceptable in some cases)
    await bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )