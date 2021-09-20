import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook



# webhook settings
WEBHOOK_HOST = 'https://your.domain'
WEBHOOK_PATH = '/path/to/api'

#вставка моих данных - начало
import os
BOT_TOKEN = os.getenv('TOKEN') 
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME') # попробовал на всякий случай задать в явном виде HEROKU_APP_NAME = 'bot-for-kadry-main'  - тоже не помогло
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}' 
#вставка моих данных - конец

API_TOKEN = BOT_TOKEN
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = 'localhost'  # - это исходный вариант
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 3001 # - это исходный вариант
WEBAPP_PORT = int(os.environ.get('PORT', '8443')) # фактический результат - каждый раз берет какой-то порт из переменной окружения, все время разные
#WEBAPP_PORT = 8443


loop = asyncio.get_event_loop()
bot = Bot(token=API_TOKEN, loop=loop)
dp = Dispatcher(bot)


#просто повтор сказанного пользователем
@dp.message_handler()
async def echo(message: types.Message):
    await bot.send_message(message.chat.id, message.text)


async def on_startup(dp):
    print('...вошли в on_startup')
    await bot.delete_webhook(dp) # строка добавлена
    print('...стартуем set_webhook')
    await bot.set_webhook(WEBHOOK_URL)
    print('...после запуска set_webhook')
    # insert code here to run it after start


async def on_shutdown(dp):
    # insert code here to run it before shutdown
    pass


if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                  skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)