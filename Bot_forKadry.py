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
# Проверка мы работаем на Heroku или локально, сделано собственной переменной в оболочке Heroku, можно пробовать также значением DYNO 
if 'We_are_on_Heroku' in os.environ:
    Run_On_Heroku = True
    # Переменные окружения на Heroku: CHAT --- ADMIN_CHAT --- TOKEN --- HEROKU_APP_NAME --- We_are_on_Heroku
    CHAT = os.getenv('CHAT')
    ADMIN_CHAT = os.getenv('ADMIN_CHAT')
    BOT_TOKEN = os.getenv('TOKEN')
    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
    bot = Bot(token=BOT_TOKEN)
    storage=MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # webhook settings
    WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
    WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
    # webserver settings
    WEBAPP_HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', '8443'))
    #print('...Port=' + str(PORT))
    WEBAPP_PORT = int(os.getenv('PORT'))

    #bot.remove_webhook()
    #bot.set_webhook(WEBHOOK_URL)
    
    # еще из одного места - Run after startup
    #async def on_startup():
    async def on_startup(dispatcher: Dispatcher) -> None:
        print('....0001')
        await bot.delete_webhook()
        print('....002')
        await bot.set_webhook(WEBHOOK_URL)
        print('....003')

    # async def hook_set():
    #     await bot.set_webhook(WEBHOOK_URL)
    #     print(await bot.get_webhook_info())
    # asyncio.run(hook_set())
    # bot.close()

    #bot.set_webhook('https://bot-for-kadry-main.herokuapp.com/' + TOKEN)
    #app.run()
    
    # а это версия из иного источника:
    #PORT = int(os.environ.get('PORT', '8443'))
    #updater = Updater(TOKEN)
    # add handlers
    #updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN, webhook_url="https://bot-for-kadry-main.herokuapp.com/" + TOKEN)
    #updater.idle()
else:
    print ('..Run_On_Heroku = NO')
    Run_On_Heroku = False # локально запускаем без webhook 
    from config import *
    bot = Bot(token=TOKEN)
    storage=MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

print('....вводную часть завершили')

#======================== Для работы с состояниями
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# Объявляем варианты состояния конечных автоматов (FSM — Finite State Machine)
class Status (StatesGroup):
    st_00 = State() # начальный статус, ничего не делали
    st_01 = State() # после кнопки Запуск выбрали действие, но пока не ввели подробных данных
    st_02 = State() # ввели все данные для отправки
#await Status.st_00.set()
#state = Dispatcher.get_current().current_state()
# для явного задания состояния строка типа этой:
# await OrderFood.waiting_for_food_name.set()
#мы явно говорим боту встать в состояние waiting_for_food_name из группы OrderFood

global begining_text, text_of_obiavy, full_text, codeDO, send_admin
begining_text = 'пустое начало'
text_of_obiavy = 'пустой текст объявы'
full_text = 'пустой суммарный текст'
codeDO = '0' #переменная, по которой определяем что делать дальше на основе ответа пользователя 
send_admin = 'No'

# задаем пустой массив для id сообщений, в которых у нас будут инлайн кнопки, чтобы их потом удалять
list_msg_with_inline = []

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

@dp.message_handler(lambda message: message.text == btn_help, state="*")
@dp.message_handler(commands=['help'], state="*")
async def process_help_command(message: types.Message):
    await message.reply(help_message, disable_web_page_preview = True) # убран предпросмотр ссылок
    await Status.st_00.set()



#===== блок Начала
btn_zapusk = 'Запуск'
btn_help = 'Помощь'
MAIN_KB = ReplyKeyboardMarkup(
                             resize_keyboard=True).row(
                             KeyboardButton(btn_zapusk),
                             KeyboardButton(btn_help)
                             )

@dp.message_handler(commands=['start'], state="*")
async def process_start_command(message: types.Message):
    if ((message.from_user.first_name is None) and (message.from_user.first_name is None)):
        whom_say = message.from_user.username
        await message.answer(f'Привет, @{message.from_user.username}!\n Начинаем работу 👋', reply_markup=MAIN_KB)
    else:
        whom_say = message.from_user.first_name + ' ' + message.from_user.last_name
        await message.answer(f'Привет, {whom_say} (@{message.from_user.username})!\nНачинаем работу 👋', reply_markup=MAIN_KB)
    await Status.st_00.set()


#======================== Главное меню
def get_inline_kb_full():
	# Генерация клавиатуры Главного меню
	inline_btn_1 = InlineKeyboardButton('Разместить вакансию', callback_data='btn1')
	inline_btn_2 = InlineKeyboardButton('Разместить резюме', callback_data='btn2')
	inline_kb_full = types.InlineKeyboardMarkup(row_width=2) # можно еще добавить параметры, но толку нет resize_keyboard=True, one_time_keyboard=True
	inline_kb_full.row(inline_btn_1, inline_btn_2)
	inline_btn_3 = InlineKeyboardButton('Предложить работы/услуги в сфере закупок', callback_data='btn3')
	inline_kb_full.add(inline_btn_3)
	inline_btn_4 = InlineKeyboardButton('Иное сообщение в канал', callback_data='btn4')
	inline_kb_full.add(inline_btn_4)
	inline_btn_5 = InlineKeyboardButton('Нужна помощь', callback_data='btn5')
	inline_btn_6 = InlineKeyboardButton('Связаться с админом', callback_data='btn6')
	inline_kb_full.add(inline_btn_5, inline_btn_6)
	# inline_kb_full.add(InlineKeyboardButton('На сайт админа', url='https://sukhadol.ru',callback_data='btn7'))
	return inline_kb_full

import requests
@dp.message_handler(lambda message: message.text == btn_zapusk, state="*")
@dp.message_handler(commands=['begin'], state="*")
async def process_command_main_menu(message: types.Message, state: FSMContext):
    await Status.st_00.set()
    await message.answer("Что Вы хотите сделать?\nВыберите вариант:",
                        reply_markup=get_inline_kb_full())
# суть очистки: после того как пользователь на Инлайн-клавиатуре выбрал вариант что он хочет, то все Инлайн-клавиатуры надо скрыть. 
# Причем их до этого могло быть несколько, надо скрыть все предыдущие. А для этого надо сначала запомнить все id таких сообщений, а потом по ним циклом пройтись и закрыть. 
    next_id = message.message_id
    list_msg_with_inline.append(next_id) # добавляем id сообщения. Но! Это id сообщения пользователя ЗАПУСК, т.е. работать потом надо будет с (id+1)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('btn'), state=Status.st_00)
async def process_callback_from_main_menu(callback_query: types.CallbackQuery):
    global begining_text, text_of_obiavy, full_text, codeDO, send_admin
    await Status.st_01.set()
    codeDO = callback_query.data[-1]  # сформировали команду что будем дальше делать
    if codeDO.isdigit():
        codeDO = int(codeDO)
    if codeDO == 1:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ ВАКАНСИЮ') 
        await bot.send_message(callback_query.from_user.id, f'Для размещения вакансии введите ниже ее описание, указав:\n- организацию,\n- город,\n- должность, требования к соискателю и его обязанности,\n- ожидаемое вознаграждение,\n-контакты для связи.\n\nВ описании можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки)', parse_mode='Markdown') 
        begining_text = '*#ВАКАНСИЯ* от @' + str(callback_query.from_user.username)
    elif codeDO == 2:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ РЕЗЮМЕ') 
        await bot.send_message(callback_query.from_user.id, f'Для размещения резюме введите ниже его текст.\n\nВ тексте можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки)', parse_mode='Markdown') 
        begining_text = '*#РЕЗЮМЕ* от @' + str(callback_query.from_user.username)
    elif codeDO == 3:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: ПРЕДЛОЖИТЬ УСЛУГИ') 
        await bot.send_message(callback_query.from_user.id, f'Введите описание предлагаемых Вами услуг.\n\nВ описании можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки)', parse_mode='Markdown')  
        begining_text = '*#УСЛУГИ_В_СФЕРЕ_ЗАКУПОК* от @' + str(callback_query.from_user.username)
    elif codeDO == 4:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ ИНОЕ СООБЩЕНИЕ') 
        await bot.send_message(callback_query.from_user.id, f'Введите свое сообщение') 
        begining_text = 'Сообщение от @' + str(callback_query.from_user.username)
    elif codeDO == 5:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, help_message, disable_web_page_preview=True) 
    elif codeDO == 6:
        send_admin = 'Yes'
        await bot.send_message(callback_query.from_user.id, f'Вы выбрали:\nНАПРАВИТЬ СООБЩЕНИЕ АДМИНИСТРАТОРАМ КАНАЛА') 
        await bot.send_message(callback_query.from_user.id, f'Введите текст сообщение') 
        begining_text = 'СООБЩЕНИЕ АДМИНИСТРАТОРАМ от @' + str(callback_query.from_user.username)
    else:
        #await bot.answer_callback_query(callback_query.id)
    	await bot.send_message(callback_query.from_user.id, f'Нажата инлайн кнопка! codeDO={codeDO}')
    # удаление клавиатуры. Причем надо не только последнюю, но и предыдущие
    while ((len(list_msg_with_inline)) > 0):
        #print('........len число элементов в массиве текущее = ' + str((len(list_msg_with_inline))))
        id_tmp = list_msg_with_inline.pop() # взяли последний элемент массива в переменную, и одновременно удалили его из массива
        #print('...id_tmp = ' + str(id_tmp))
        #print('...len текущее2 = ' + str((len(list_msg_with_inline))))
        await bot.edit_message_reply_markup(callback_query.message.chat.id, message_id = id_tmp+1)
        #print('... После удаления')
    # Не забываем отчитаться о получении колбэка
    await callback_query.answer()

#====  примеры удаления клавиатуры:

# для telebot
#hideBoard = types.ReplyKeyboardRemove()  # if sent as reply_markup, will hide the keyboard
#bot.send_photo(cid, open('kitten.jpg', 'rb'), reply_markup=hideBoard)

# Edit only the reply markup of messages sent by the bot.
# bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)



#======================== Меню размещения детального описания вакансии или сообщения 

def get_inline_kb_Yes_No():
	# Генерация клавиатуры меню Yes-No
	inline_YNbtn_1 = InlineKeyboardButton('Да', callback_data='YNbtn1')
	inline_YNbtn_2 = InlineKeyboardButton('Нет', callback_data='YNbtn2')
	inline_kb_Yes_No = types.InlineKeyboardMarkup(row_width=2)
	inline_kb_Yes_No.row(inline_YNbtn_1, inline_YNbtn_2)
	#inline_YNbtn_3 = InlineKeyboardButton('Ввести новый текст для отправки', callback_data='YNbtn3')
	#inline_kb_Yes_No.add(inline_YNbtn_3)
	return inline_kb_Yes_No

# Сюда приходит ответ с текстом объявления
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=Status.st_01) 
async def vvod_txt(message: types.Message):
    global begining_text, text_of_obiavy, full_text
    text_of_obiavy = message.text
    full_text= begining_text+'\n\n'+text_of_obiavy
   # full_text = full_text + types.chat.chat_title(chat_id=CHAT)
    await message.answer(text=f'Итого получаем следующий текст:\n\n{full_text}', parse_mode='Markdown')
    await Status.st_02.set()
    await message.answer("Подтверждаете отправку?",
                        reply_markup=get_inline_kb_Yes_No())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('YNbtn'), state=Status.st_02)
async def process_callback_from_menuYN(callback_query: types.CallbackQuery):
    global begining_text, text_of_obiavy, full_text, codeDO, send_admin
    codeYN = callback_query.data[-1]
    if codeYN.isdigit():
        codeYN = int(codeYN)
    await Status.st_00.set()
    if codeYN == 1:
        if send_admin == 'Yes':
            await bot.send_message(callback_query.from_user.id, f'Спасибо, сообщение направлено администраторам.') 
            await bot.send_message(chat_id = ADMIN_CHAT, text=full_text, parse_mode='Markdown') 
        else:
            await bot.send_message(chat_id = CHAT, text=full_text, parse_mode='Markdown') 
            await bot.send_message(callback_query.from_user.id, f'Спасибо, сообщение размещено в канале') 
        await bot.send_message(callback_query.from_user.id, f'Чем-то еще могу помочь? Например, если хотите, можно начать еще раз. Для этого нажмите внизу кнопку "Запуск" или введите команду /begin \nИли можете перейти в один из каналов:\n https://t.me/InterfaxProZakupkiNews \n https://t.me/jobzakupki') 
    elif codeYN == 2:
        await bot.send_message(callback_query.from_user.id, f'Отправка отменена. Но если хотите, можно начать еще раз. Для этого нажмите внизу кнопку \"Запуск\" или введите команду /begin') 
        #await process_start_command()
        #await Status.st_00.set()
    else:
    	await bot.send_message(callback_query.from_user.id, f'Нажата инлайн кнопка! codeYN={codeYN}')
    # удаление клавиатуры
    await callback_query.message.delete_reply_markup() 
    # Не забываем отчитаться о получении колбэка
    await callback_query.answer()



# Ловим все иные непонятные тексты - в рамках state=Status.st_02, т.е. когда ввели все данные для отправки
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=Status.st_02) 
async def strange_txt(message: types.Message):
    await message.reply("Не понимаю Вас. Нажмите выше кнопки Да или Нет, для подтверждения отправки ранее сформированного тектса, или отказа от него")

# Ловим все иные непонятные тексты - все оставшиеся
@dp.message_handler(content_types=types.ContentTypes.TEXT, state="*") 
async def strange_txt(message: types.Message):
    await message.reply("Не понимаю Вас. Нажмите /begin для открытия основного меню")

#=================================================


#Для красоты ещё стоит закрывать соединение с хранилищем состояний, для этого объявляем функцию:
async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

print('....007')

if __name__ == '__main__':
    #print('... что-то есть')
    if Run_On_Heroku:
        print('....004')
        def main():
            print('....005')
            #start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
            executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
            print('....006')

    else:
        print('.... 9999')
        executor.start_polling(dp, on_shutdown=shutdown)
#else:
    #print('... пусто и ничего не делаем')
