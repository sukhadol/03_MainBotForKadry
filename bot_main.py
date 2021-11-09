import asyncio

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook


from aiogram.utils import executor
from aiogram.utils.markdown import LIST_MD_SYMBOLS, text
from aiogram import Dispatcher
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import os
import facebook

#++++++++++++++++++++++++++++++++++++++++

print ('..====== начали ===== ')
# Проверка мы работаем на Heroku или локально, сделано собственной переменной в оболочке Heroku
if 'We_are_on_Heroku' in os.environ:
    Run_On_Heroku = True
    # Переменные окружения на Heroku: CHAT --- ADMIN_CHAT --- TOKEN --- HEROKU_APP_NAME --- We_are_on_Heroku --- ACCESS_TOKEN_Facebook
    CHAT = os.getenv('CHAT')
    ADMIN_CHAT = os.getenv('ADMIN_CHAT')
    BOT_TOKEN = os.getenv('TOKEN')
    HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')

    # переменные для работы с ВК
    groupId_in_VK = os.environ.get("groupId_in_VK")
    token_VK_access_token_to_walls = os.environ.get("token_VK_access_token_to_walls")  # Токен ВК с доступом только к wall, для опубликования там сообщений

    # переменные для работы с ФБ
    ACCESS_TOKEN_Facebook = os.environ.get("ACCESS_TOKEN_Facebook")
    groupid_in_FB = 1013708529168332

    # webhook settings
    WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
    WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}' 
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

    # webserver settings
    WEBAPP_HOST = '0.0.0.0'
    WEBAPP_PORT = int(os.environ.get('PORT', '8443')) # фактический результат - каждый раз берет какой-то порт из переменной окружения, все время разные

    loop = asyncio.get_event_loop()
    bot = Bot(token=BOT_TOKEN, loop=loop)
    #dp = Dispatcher(bot)
    storage=MemoryStorage()
    dp = Dispatcher(bot, storage=storage)


    async def on_startup(dp):
        await bot.delete_webhook(dp) 
        await bot.set_webhook(WEBHOOK_URL)
        # и дальше все что надо после запуска

    async def on_shutdown(dp):
        # если что-то надо для окончания
        pass

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
    st_ADM_02 = State() # особое состояние общения с Админом
# для явного задания состояния строка типа этой:
# await Status.st_00.set() # !!! особенность: в самом начале СТАТУС не встает, остается неопределенным, надо запустить ПОМОЩЬ или START
# мы явно говорим боту встать в состояние st_00 из группы Status
# state = Dispatcher.get_current().current_state()


global begining_text, text_of_obiavy, text_from_to_telegram, text_from_to_export, full_text_telegram, full_text_export, codeDO, send_admin
# еще есть переменные textOfForvardObiavyHtml, textOfForvardObiavyPlain - они только в разделе ловли форварда из иных каналов
begining_text = 'пустое начало'
text_of_obiavy = 'пустой текст объявы'
full_text_telegram = 'пустой суммарный текст'
full_text_export = 'пустой суммарный текст'
codeDO = '0' #переменная, по которой определяем что делать дальше на основе ответа пользователя 
send_admin = 'No'
textOfForvardObiavy = '' # это для форварднутых админом сообщений

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
    "\nЕсли вдруг бот не запускается, воспользуйтесь командой",
	"/start, после чего внизу возникнут кнопки ЗАПУСК (основная часть функционала) и ПОМОЩЬ",
    "\nДополнительно информация в канале автоматически наполняется из постов группы Facebook \"Карьера в закупках: Вакансии & Кандидаты\" (https://www.facebook.com/groups/1013708529168332)",
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

def def_to_whom_say(SomeOne): # подпрограмма чтобы понимать как обращаться к пользователю. Возвращает WhomToSay (как зовут или id), JustIdYNo (понимание, что содержится в WhomToSay - имя или id)
    if ((SomeOne.first_name is None) and (SomeOne.last_name is None)):
        if (SomeOne.username is None):
            #WhomToSay = str(SomeOne.id) # т.е. когда вообще все неизвестно, и значит остается только id 
            WhomToSay = 'ИмяСкрытоПользователем' # т.е. когда вообще все неизвестно, и значит остается только id 
            JustIdYNo = 'Yes'  
        else:
            WhomToSay = '@' + str(SomeOne.username)
            JustIdYNo = 'No'
    elif (SomeOne.first_name is None):
        WhomToSay = str(SomeOne.last_name)
        JustIdYNo = 'No'
    elif (SomeOne.last_name is None):
        WhomToSay = str(SomeOne.first_name)
        JustIdYNo = 'No'
    else:
        WhomToSay = str(SomeOne.first_name) + ' ' + str(SomeOne.last_name)
        JustIdYNo = 'No'
    return [WhomToSay, JustIdYNo]

@dp.message_handler(commands=['start'], state="*")
async def process_start_command(message: types.Message):
    #def_to_whom_say(message.from_user)
    text_from_to_telegram = '[' + def_to_whom_say(message.from_user)[0] + '](tg://user?id=' + str(message.from_user.id) +')' # суть: хотим получить универсальную гиперссылку на пользователя, независимо от того, скрыто его имя или нет 
    print ('...from_user.id = ')
    print(message.from_user.id)
    print ('...text_from_to_telegram = ')
    print(text_from_to_telegram)
   # await message.answer(f'Привет, {text_from_to_telegram}!\nНачинаем работу-2 tg://user?id=' + str(message.from_user.id), parse_mode='Markdown')
    await message.answer(f'Привет, {text_from_to_telegram}!\nНачинаем работу 👋\n(Используйте внизу кнопки ЗАПУСК и ПОМОЩЬ)', reply_markup=MAIN_KB, parse_mode='Markdown')
 

    # дублирующий блок, на удаление, чуть позже
    # if (message.from_user.username is None):
    #     #fff
    # elif ((message.from_user.first_name is None) or (message.from_user.last_name is None)):
    #     if ((message.from_user.first_name is None) and (message.from_user.last_name is None)):
    #         #whom_say = message.from_user.username
    #         await message.answer(f'Привет, @{message.from_user.username}!\n Начинаем работу 👋\n(Используйте внизу кнопки ЗАПУСК и ПОМОЩЬ)', reply_markup=MAIN_KB)
    #     else:
    #         if (message.from_user.first_name is None):
    #             whom_say = message.from_user.last_name
    #             await message.answer(f'Привет, {whom_say} (@{message.from_user.username})!\n Начинаем работу 👋\n(Используйте внизу кнопки ЗАПУСК и ПОМОЩЬ)', reply_markup=MAIN_KB)
    #         else:
    #             whom_say = message.from_user.first_name
    #             await message.answer(f'Привет, {whom_say} (@{message.from_user.username})!\n Начинаем работу 👋\n(Используйте внизу кнопки ЗАПУСК и ПОМОЩЬ)', reply_markup=MAIN_KB)
    # else:
    #     whom_say = message.from_user.first_name + ' ' + message.from_user.last_name
    #     await message.answer(f'Привет, {whom_say} (@{message.from_user.username})!\nНачинаем работу 👋\n(Используйте внизу кнопки ЗАПУСК и ПОМОЩЬ)', reply_markup=MAIN_KB)
    await Status.st_00.set()


#======================== Главное меню
def get_inline_kb_full():
	# Генерация клавиатуры Главного меню
	inline_btn_1 = InlineKeyboardButton('🔎 Разместить вакансию', callback_data='btn1')
	inline_btn_2 = InlineKeyboardButton('✍ Разместить резюме', callback_data='btn2')
	inline_kb_full = types.InlineKeyboardMarkup(row_width=2) # можно еще добавить параметры, но толку нет resize_keyboard=True, one_time_keyboard=True
	inline_kb_full.row(inline_btn_1, inline_btn_2)
	inline_btn_3 = InlineKeyboardButton('⚡ Предложить работы/услуги в сфере закупок', callback_data='btn3')
	inline_kb_full.add(inline_btn_3)
	inline_btn_4 = InlineKeyboardButton('🔔 Иное сообщение в канал', callback_data='btn4')
	inline_kb_full.add(inline_btn_4)
	inline_btn_5 = InlineKeyboardButton('❓ Нужна помощь', callback_data='btn5')
	inline_btn_6 = InlineKeyboardButton('☎️ Связаться с админом', callback_data='btn6')
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
    global begining_text, text_of_obiavy, text_from_to_telegram, text_from_to_export, full_text_telegram, full_text_export, codeDO, send_admin
    await Status.st_01.set()
    codeDO = callback_query.data[-1]  # сформировали команду что будем дальше делать
    #text_from_to_telegram_part = <a href="tg://user?id={callback_query.from_user.id}">{def_to_whom_say(callback_query.from_user)[0]}</a> # это такой формат гиперссылки при маркдауне HTML далее работает 
    text_from_to_telegram = '[' + def_to_whom_say(callback_query.from_user)[0] + '](tg://user?id=' + str(callback_query.from_user.id) +')' # суть: хотим получить универсальную гиперссылку на пользователя, независимо от того, скрыто его имя или нет 
    text_from_to_export = def_to_whom_say(callback_query.from_user)[0] # суть: получаем только имя пользователя для экспорта, независимо от того, скрыто его имя или нет 

    #text_from_to_telegram = '@' + str(callback_query.from_user.username) # здесь пока поставили username, но на самом деле он не всегда есть у пользователя
    if codeDO.isdigit():
        codeDO = int(codeDO)
    if codeDO == 1:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ ВАКАНСИЮ') 
        await bot.send_message(callback_query.from_user.id, f'Для размещения вакансии введите ниже ее описание, указав:\n- организацию,\n- город,\n- должность, требования к соискателю и его обязанности,\n- ожидаемое вознаграждение,\n-контакты для связи.\n\nВ описании можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки).\n\nЕсли хотите прикрепить файл - то сможете это сделать после размещения текстового сообщения, в рамках его обсуждения.', parse_mode='Markdown') 
        begining_text = '*#вакансия* от ' 
    elif codeDO == 2:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ резюме') 
        await bot.send_message(callback_query.from_user.id, f'Для размещения резюме введите ниже его текст.\n\nВ тексте можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки)\n\nЕсли хотите прикрепить файл - то сможете это сделать после размещения текстового сообщения, в рамках его обсуждения.', parse_mode='Markdown') 
        begining_text = '*#резюме* от ' 
    elif codeDO == 3:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: ПРЕДЛОЖИТЬ УСЛУГИ') 
        await bot.send_message(callback_query.from_user.id, f'Введите описание предлагаемых Вами услуг.\n\nВ описании можно использовать символы разметки Markdown\n  \*bold text\* (*выделение жирным*)\n  \_italic text\_ (_курсив_)\n  \[text](URL) (для размещения ссылки)\n\nЕсли хотите прикрепить файл - то сможете это сделать после размещения текстового сообщения, в рамках его обсуждения.', parse_mode='Markdown')  
        begining_text = '*#Услуги_в_сфере_закупок* от '
    elif codeDO == 4:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, 'Вы выбрали: РАЗМЕСТИТЬ ИНОЕ СООБЩЕНИЕ') 
        await bot.send_message(callback_query.from_user.id, f'Введите свое сообщение.\n\nЕсли хотите прикрепить файл - то сможете это сделать после размещения текстового сообщения, в рамках его обсуждения.') 
        begining_text = 'Сообщение от '
    elif codeDO == 5:
        send_admin = 'No'
        await bot.send_message(callback_query.from_user.id, help_message, disable_web_page_preview=True) 
    elif codeDO == 6:
        send_admin = 'Yes'
        await bot.send_message(callback_query.from_user.id, f'Вы выбрали:\nНАПРАВИТЬ СООБЩЕНИЕ АДМИНИСТРАТОРАМ КАНАЛА') 
        await bot.send_message(callback_query.from_user.id, f'Введите текст сообщение') 
        begining_text = 'СООБЩЕНИЕ АДМИНИСТРАТОРАМ от ' 
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
    global begining_text, text_of_obiavy, full_text_telegram
    text_of_obiavy = message.text
    full_text_telegram= begining_text + text_from_to_telegram + '\n\n' + text_of_obiavy
   # full_text_telegram = full_text_telegram + types.chat.chat_title(chat_id=CHAT)
    await message.answer(text=f'Итого получаем следующий текст:\n\n{full_text_telegram}', parse_mode='Markdown')
    await Status.st_02.set()
    await message.answer("Подтверждаете отправку?",
                        reply_markup=get_inline_kb_Yes_No())


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('YNbtn'), state=Status.st_02)
async def process_callback_from_menuYN(callback_query: types.CallbackQuery):
    global begining_text, text_of_obiavy, text_from_to_telegram, text_from_to_export, full_text_telegram, full_text_export, codeDO, send_admin
    codeYN = callback_query.data[-1]
    if codeYN.isdigit():
        codeYN = int(codeYN)
    await Status.st_00.set()
    if codeYN == 1:
        if send_admin == 'Yes':
            await bot.send_message(callback_query.from_user.id, f'Спасибо, сообщение направлено администраторам.') 
            await bot.send_message(chat_id = ADMIN_CHAT, text=full_text_telegram, parse_mode='Markdown') 
        else:
            await bot.send_message(chat_id = CHAT, text=full_text_telegram, parse_mode='Markdown') 
            if codeDO < 3:   
                # ниже 5 строчек - для отправки сообщения в ВК
                message_to_VK = ('Форвард нового сообщения из Телеграм:\n\n' + begining_text + text_from_to_export + '\n\n' + text_of_obiavy + '\n\nИсточник:\nhttps://t.me/jobzakupki')
                message_to_VK = message_to_VK.replace("*#вакансия*", "#вакансия")
                message_to_VK = message_to_VK.replace("*#резюме*", "#резюме")
                params = {'owner_id':int(groupId_in_VK), 'from_group': 1, 'message': message_to_VK, 'access_token': token_VK_access_token_to_walls, 'v':5.103} # это отправка дубля на ВК
                requests.get('https://api.vk.com/method/wall.post', params=params)
                # ниже 3 строчки - для отправки сообщения в ФБ
                graph = facebook.GraphAPI(ACCESS_TOKEN_Facebook)
                message_to_FB = message_to_VK
                graph.put_object(groupid_in_FB, "feed", message=message_to_FB)
            await bot.send_message(callback_query.from_user.id, f'Спасибо, сообщение размещено в канале') 
        await bot.send_message(callback_query.from_user.id, f'Чем-то еще могу помочь? Например, если хотите, можно начать еще раз. Для этого нажмите внизу кнопку "Запуск" или введите команду /begin \nИли можете перейти в один из каналов:\n https://t.me/InterfaxProZakupkiNews \n https://t.me/jobzakupki\n\nP.S.Если внизу пропали кнопки ЗАПУСК и ПОМОЩЬ - введите /start и нажмите Enter') 
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
    await message.reply("Не понимаю Вас. Нажмите выше кнопки Да или Нет, для подтверждения отправки ранее сформированного текста, или отказа от него")


#======================== Меню размещения ФОРВАРДНЫХ постов админом
# алгоритм: если взять любой пост из Телеграма и форварднуть его на бота @CareerZakupkiBot, то этот пост будет переразмещен у нас в канале

def ADMIN_get_inline_kb_Yes_No():
	# Генерация клавиатуры АДМИНСКОГО меню Yes-No
	inline_admin_YNbtn_1 = InlineKeyboardButton('Да, ВАКАНСИЯ', callback_data='AdminYNbtn1')
	inline_admin_YNbtn_2 = InlineKeyboardButton('Нет, НЕ РАЗМЕЩАТЬ', callback_data='AdminYNbtn2')
	Admin_inline_kb_Yes_No = types.InlineKeyboardMarkup(row_width=2)
	Admin_inline_kb_Yes_No.row(inline_admin_YNbtn_1, inline_admin_YNbtn_2)
	inline_admin_YNbtn_3 = InlineKeyboardButton('Нет, разместить как РЕЗЮМЕ', callback_data='AdminYNbtn3')
	Admin_inline_kb_Yes_No.add(inline_admin_YNbtn_3)
	return Admin_inline_kb_Yes_No


# Ловим все иные непонятные тексты - все оставшиеся, кроме если в состоянии st_ADM_02
@dp.message_handler(content_types=types.ContentTypes.TEXT, state=Status.st_00 or Status.st_01 or Status.st_02) # почему-то вариант с перечислением выдал ошибку state=Status.st_00 | Status.st_01 | Status.st_02
async def strange_txt(message: types.Message):
    global begining_text, text_of_obiavy, text_from_to_telegram, text_from_to_export, full_text_telegram, full_text_export, codeDO, send_admin, textOfForvardObiavyHtml, textOfForvardObiavyPlain
    if message.from_user.username == "sukhadol":
        if message.forward_from is None:                  # т.е. если это не форварднутое сообщение, а прямо в чат
            await message.answer("о мой администратор! Что-то написано и не распознано!! (возможно у пользователя скрыта инфа о себе)") 
        else:
            await message.answer(text=f'о мой администратор! Это форварднутая вакансия от <strong><a href="tg://user?id={message.forward_from.id}">{def_to_whom_say(message.forward_from)[0]}</a></strong> и надо разместить ее в основном канале?', parse_mode = 'html') 

            textOfForvardObiavyHtml = '<strong>#вакансия</strong> от <strong><a href=\"tg://user?id=' + str(message.forward_from.id) + '\">' + def_to_whom_say(message.forward_from)[0] + '</a></strong>\n\n' + message.text
            if def_to_whom_say(message.forward_from)[1] == 'Yes': # т.е. в случае если у пользователя не открыты не имя ни фамилия (JustIdYNo = 'Yes'), а знаем только его id - то вовне Телеграма убираем его ФИО (точнее, убираем отображение id)
                textOfForvardObiavyPlain = '#вакансия\n\n' + message.text                
            else:
                textOfForvardObiavyPlain = '#вакансия от ' + def_to_whom_say(message.forward_from)[0] + '\n\n' + message.text

            await message.answer(text=f'Итого получаем следующий текст:\n\n{textOfForvardObiavyHtml}', parse_mode=types.ParseMode.HTML)
            await Status.st_ADM_02.set()
            await message.answer("Подтверждаете отправку?", reply_markup=ADMIN_get_inline_kb_Yes_No()) 
    else:
        await message.reply("Не понимаю Вас. Нажмите /begin для открытия основного меню")

# Ловим ответ от АДМИНА
@dp.callback_query_handler(lambda c: c.data and c.data.startswith('AdminYNbtn'), state=Status.st_ADM_02)
async def process_callback_from_menuYN(callback_query: types.CallbackQuery):
    global begining_text, text_of_obiavy, full_text_telegram, codeDO, send_admin, textOfForvardObiavyHtml, textOfForvardObiavyPlain
    codeYN = callback_query.data[-1]
    if codeYN.isdigit():
        codeYN = int(codeYN)
    await Status.st_00.set()
    if codeYN == 1:
        await bot.send_message(chat_id = CHAT, text=textOfForvardObiavyHtml, parse_mode=types.ParseMode.HTML)
        # ниже 5 строчек - для отправки сообщения в ВК
        message_to_VK = ('Форвард нового сообщения из Телеграм:\n\n' + textOfForvardObiavyPlain + '\n\nИсточник:\nhttps://t.me/jobzakupki')
        params = {'owner_id':int(groupId_in_VK), 'from_group': 1, 'message': message_to_VK, 'access_token': token_VK_access_token_to_walls, 'v':5.103} # это отправка дубля на ВК
        requests.get('https://api.vk.com/method/wall.post', params=params)
        # ниже 3 строчки - для отправки сообщения в ФБ
        graph = facebook.GraphAPI(ACCESS_TOKEN_Facebook)
        message_to_FB = message_to_VK
        graph.put_object(groupid_in_FB, "feed", message=message_to_FB)
        await bot.send_message(callback_query.from_user.id, f'АДМИН, спасибо, сообщение с ВАКАНСИЕЙ размещено в канале. Чем-то еще могу помочь? Например, если хотите, можно начать еще раз. Для этого нажмите внизу кнопку "Запуск" или введите команду /begin \nИли можете перейти в один из каналов:\n https://t.me/InterfaxProZakupkiNews \n https://t.me/jobzakupki\n\nP.S.Если внизу пропали кнопки ЗАПУСК и ПОМОЩЬ - введите /start и нажмите Enter') 
    elif codeYN == 2:
        await bot.send_message(callback_query.from_user.id, f'АДМИН, отправка отменена. Но если хотите, можно начать еще раз. Для этого нажмите внизу кнопку \"Запуск\" или введите команду /begin') 
    elif codeYN == 3:
        textOfForvardObiavyHtml = textOfForvardObiavyHtml.replace("#вакансия", "#резюме")
        await bot.send_message(chat_id = CHAT, text=textOfForvardObiavyHtml, parse_mode=types.ParseMode.HTML)
        # ниже 5 строчек - для отправки сообщения в ВК
        textOfForvardObiavyPlain = textOfForvardObiavyPlain.replace("#вакансия", "#резюме")
        message_to_VK = ('Форвард нового сообщения из Телеграм:\n\n' + textOfForvardObiavyPlain + '\n\nИсточник:\nhttps://t.me/jobzakupki')
        params = {'owner_id':int(groupId_in_VK), 'from_group': 1, 'message': message_to_VK, 'access_token': token_VK_access_token_to_walls, 'v':5.103} # это отправка дубля на ВК
        requests.get('https://api.vk.com/method/wall.post', params=params)
        # ниже 3 строчки - для отправки сообщения в ФБ
        graph = facebook.GraphAPI(ACCESS_TOKEN_Facebook)
        message_to_FB = message_to_VK
        graph.put_object(groupid_in_FB, "feed", message=message_to_FB)

        await bot.send_message(callback_query.from_user.id, f'АДМИН, спасибо, сообщение с РЕЗЮМЕ размещено в канале. Чем-то еще могу помочь? Например, если хотите, можно начать еще раз. Для этого нажмите внизу кнопку "Запуск" или введите команду /begin \nИли можете перейти в один из каналов:\n https://t.me/InterfaxProZakupkiNews \n https://t.me/jobzakupki\n\nP.S.Если внизу пропали кнопки ЗАПУСК и ПОМОЩЬ - введите /start и нажмите Enter') 
    else:
    	await bot.send_message(callback_query.from_user.id, f'Нажата инлайн кнопка! codeYN={codeYN}')
    # удаление клавиатуры
    await callback_query.message.delete_reply_markup() 
    # Не забываем отчитаться о получении колбэка
    await callback_query.answer()


# Ловим все иные непонятные тексты - все оставшиеся
@dp.message_handler(content_types=types.ContentTypes.TEXT, state="*") 
async def strange_txt(message: types.Message):
    if message.from_user.username == "sukhadol":
        await message.reply("о мой администратор! Просто отлов постов!!")        
    else:
        await message.reply("Не понимаю Вас. Нажмите /begin для открытия основного меню")

# Ловим вообще все иное - смайлы, файлы и др.
@dp.message_handler(content_types=types.ContentType.ANY, state="*") 
async def strange_txt(message: types.Message):
    await message.reply("Не понимаю Вас. Нажмите /begin для открытия основного меню")

#=================================================
#======= а теперь обработка иных сообщений В КАНАЛЕ - по факту только от админа

test_chanel = -516530210 # тестовый канал "02_ЧАТ админский тест"
@dp.channel_post_handler(chat_id=CHAT)
async def process_post(post: types.Message):
    print('...в сообщении  вот такое содержание')
    print(post.text) # это собственно содержание сообщения
    #тут надо добавить фильтры - в каких случаях надо или НЕ надо форвардить размещаемое сообщение
    if(post.text.startswith('Форвард нового сообщения из Фейсбука')):
        await bot.send_message(chat_id = test_chanel, text="... ... есть форварднутое сообщение из Фейсбука", parse_mode='Markdown')          
    elif(post.text.startswith('Форвард нового сообщения из ВКонтакте')):
        await bot.send_message(chat_id = test_chanel, text="... ... есть форварднутое сообщение из ВКонтакте", parse_mode='Markdown')   
    elif(post.text.startswith('Форвард нового сообщения из Телеграм')):
        await bot.send_message(chat_id = test_chanel, text="... ... есть форварднутое сообщение из Телеграм", parse_mode='Markdown')          
    else:
        await bot.send_message(chat_id = test_chanel, text="... ... есть НОВОЕ сообщение изнутри Телеграм", parse_mode='Markdown')  
        await bot.send_message(chat_id = test_chanel, text=post.text, parse_mode='Markdown')     # кидаем вообще в тестовый канал "02_ЧАТ админский тест" 


#@bot.on(events.NewMessage(CHAT)) # это функция от еще одного аддона, попробуем без нее
# async def my_event_handler(event):
#     print(event.stringify())  # это полный json сообщения
#     print(event.message.message) # это только текст сообщения




if __name__ == '__main__':
    if Run_On_Heroku:
        start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                    skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
    else:
        executor.start_polling(dp, on_shutdown=on_shutdown)
