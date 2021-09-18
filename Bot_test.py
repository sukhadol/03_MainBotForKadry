from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.utils.markdown import LIST_MD_SYMBOLS, text
from aiogram import Dispatcher
from aiogram.dispatcher import Dispatcher

import os

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

print ('..====== начали ===== ')
# Проверка мы работаем на Heroku или локально, сделано собственной переменной в оболочке Heroku
if 'We_are_on_Heroku' in os.environ:
    Run_On_Heroku = True
    # Переменные окружения на Heroku: CHAT --- ADMIN_CHAT --- TOKEN --- HEROKU_APP_NAME --- We_are_on_Heroku
    CHAT = os.getenv('CHAT')
    ADMIN_CHAT = os.getenv('ADMIN_CHAT')
    BOT_TOKEN = os.getenv('TOKEN')
    #HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
    # Heroku git URL =  https://git.heroku.com/bot-for-kadry-main.git
    # т.е. так понимаю HEROKU_APP_NAME = bot-for-kadry-main
    HEROKU_APP_NAME = 'bot-for-kadry-main'
    bot = Bot(token=BOT_TOKEN)
    storage=MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

     
    # webhook settings
    WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
    WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
    # webserver settings
    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = int(os.environ.get('PORT', '8443'))
    # PORT = int(os.environ.get('PORT', '8443'))
    # WEBAPP_PORT = int(os.getenv('PORT'))
    print('...WEBHOOK_HOST=' + str(WEBHOOK_HOST))
    print('...WEBHOOK_PATH=' + str(WEBHOOK_PATH))
    print('...WEBHOOK_URL=' + str(WEBHOOK_URL))
    print('...WEBAPP_PORT=' + str(WEBAPP_PORT))

    async def on_startup():
        print('....контроль прохода к строке 0001')
        await bot.delete_webhook()
        print('....контроль прохода к строке 002')
        await bot.set_webhook(WEBHOOK_URL)
        print('....контроль прохода к строке 003')
else:
    print ('..Run_On_Heroku = NO')
    Run_On_Heroku = False # локально запускаем без webhook 
    from config import *
    bot = Bot(token=TOKEN)
    storage=MemoryStorage()
    dp = Dispatcher(bot, storage=storage)


#===== блок Помощи
help_message = text(
    "Это бот раздела \"Закупочный хаб ProЗакупки\".\n",
    "Он поможет в размещении вакансии или резюме, а также через него можно связаться с администрацией канала.",
    "Ну и вообще сделать все что надо.",
	"\nНаши каналы:",
	"- Новости Интерфакса по закупкам https://t.me/InterfaxProZakupkiNews",
	"- Работа и Карьера в закупках: Вакансии & Кандидаты https://t.me/jobzakupki",
    "\nЕсли вдруг бот не запускается, воспользуйтесь командой\n",
	"/start - приветствие",
	sep="\n"
)

@dp.message_handler(lambda message: message.text == btn_help)
@dp.message_handler(commands=['help'], state="*")
async def process_help_command(message: types.Message):
    await message.reply(help_message, disable_web_page_preview = True) # убран предпросмотр ссылок



#===== блок Начала
btn_zapusk = 'Запуск - отключен'
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



#Ещё вроде надо закрывать соединение с хранилищем состояний, для этого объявляем функцию:
async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


print('....контроль прохода к строке 007')

if __name__ == '__main__':
    if Run_On_Heroku:
        print('....контроль прохода к строке 004')
        def main():
            print('....контроль прохода к строке 005')
            executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
            print('....контроль прохода к строке 006')
    else:
        executor.start_polling(dp, on_shutdown=shutdown)

