
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.client.default import DefaultBotProperties
import asyncio
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # 👈 Новый параметр для chat_id канала

# Авторизация Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).sheet1

# Бот
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_motivation = State()

@dp.message(CommandStart(deep_link=True))
async def start_with_source(message: Message, state: FSMContext, command: CommandStart):
    source = command.args or "не указан"
    await state.update_data(source=source)
    await message.answer(
        "👋 Привет!\n\n"
        "Прежде чем мы добавим тебя в наш информационный канал Академии Бенефактор,\n\n"
        "<b>напиши, пожалуйста:</b>\n"
        "«Чтобы мы понимали, что для тебя важно — напиши,\n"
        "какую пользу ты хочешь получить от участия в нашем канале?»\n\n"
        "✍️ Пара слов — этого достаточно."
    )
    await state.set_state(Form.waiting_for_motivation)

@dp.message(Form.waiting_for_motivation)
async def handle_motivation(message: Message, state: FSMContext):
    data = await state.get_data()
    source = data.get("source", "не указан")
    motivation = message.text
    user = message.from_user

    # Запись в таблицу
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user.full_name,
        f"@{user.username}" if user.username else "—",
        source,
        motivation
    ])

    try:
        await bot.add_chat_member(chat_id=CHANNEL_ID, user_id=user.id)
        await message.answer("✅ Спасибо! Мы добавили тебя в канал 🎉", reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        await message.answer("⚠️ Не удалось добавить тебя в канал. Напиши нам напрямую.")
        logging.error(f"Ошибка при добавлении: {e}")

    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
