import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook


import os
BOT_TOKEN = os.getenv('TOKEN') 
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME') 

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}' 
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.environ.get('PORT', '8443')) # фактический результат - каждый раз берет какой-то порт из переменной окружения, все время разные

loop = asyncio.get_event_loop()
bot = Bot(token=BOT_TOKEN, loop=loop)
dp = Dispatcher(bot)

# #просто повтор сказанного пользователем
# @dp.message_handler()
# async def echo(message: types.Message):
#     await bot.send_message(message.chat.id, message.text)


#===== блок текстов
help_message = text("здесь текстовое сообщение бла-бла-бла, пока удалено, если вдруг бот не запускается, воспользуйтесь командой /start")
@dp.message_handler(lambda message: message.text == btn_help)
@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply(help_message, disable_web_page_preview = True)

tmp_message = text("здесь потом будет основной функционал общения с пользователем")
@dp.message_handler(lambda message: message.text == btn_zapusk)
@dp.message_handler(commands=['zapusk'])
async def process_help_command(message: types.Message):
    await message.reply(tmp_message, disable_web_page_preview = True)


#===== блок Начала
btn_zapusk = 'Запуск'
btn_help = 'Помощь'
MAIN_KB = ReplyKeyboardMarkup(
                             resize_keyboard=True).row(
                             KeyboardButton(btn_zapusk),
                             KeyboardButton(btn_help)
                             )

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    if ((message.from_user.first_name is None) and (message.from_user.first_name is None)):
        whom_say = message.from_user.username
        await message.answer(f'Привет, @{message.from_user.username}!\n Начинаем работу 👋', reply_markup=MAIN_KB)
    else:
        whom_say = message.from_user.first_name + ' ' + message.from_user.last_name
        await message.answer(f'Привет, {whom_say} (@{message.from_user.username})!\nНачинаем работу 👋', reply_markup=MAIN_KB)



async def on_startup(dp):
    await bot.delete_webhook(dp) 
    await bot.set_webhook(WEBHOOK_URL)
    # и дальше все что надо после запуска


async def on_shutdown(dp):
    # если что-то надо для окончания
    pass


if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                  skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)