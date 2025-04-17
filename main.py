
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardRemove
from datetime import datetime
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Прямой ID канала

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1

# Настройка бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Состояние анкеты
class Form(StatesGroup):
    waiting_for_response = State()

# Стартовая точка с отслеживанием источника
@dp.message(CommandStart(deep_link=True))
async def start(message: types.Message, state: FSMContext, command: CommandStart):
    source = command.args or "не указан"
    await state.update_data(source=source)
    await message.answer(
        "👋 Академия <b>«Бенефактор»</b> приветствует вас!\n\n"
        "Здесь вы сможете:\n"
        "• Изучить вводные бесплатные уроки\n"
        "• Получать свежие новости и обновления Академии\n"
        "• Пройти индивидуальные сессии с экспертами (в стадии настройки)\n"
        "• Задать вопросы по обучению в специальной группе\n"
        "• Участвовать в видеовстречах с другими участниками\n"
        "• И спокойно понять, подходит ли вам наше обучение\n\n"
        "✍️ Пожалуйста, напишите, какую пользу вы хотите получить и какие боли или задачи стремитесь решить с нашей помощью."
    )
    await state.set_state(Form.waiting_for_response)

# Обработка ответа и добавление в канал
@dp.message(Form.waiting_for_response)
async def handle_response(message: types.Message, state: FSMContext):
    data = await state.get_data()
    source = data.get("source", "не указан")
    user = message.from_user
    response = message.text

    # Лог в Google Таблицу
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user.full_name,
        f"@{user.username}" if user.username else "—",
        source,
        response
    ])

    # Добавление в канал
    try:
        await bot.add_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        await message.answer("✅ Спасибо! Мы добавили вас в канал 🎉", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logging.error(f"Ошибка при добавлении в канал: {e}")
        await message.answer("⚠️ Не удалось добавить вас в канал. Пожалуйста, свяжитесь с администратором.")

    await state.clear()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
