import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.filters import CommandStart

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# Получаем переменные из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_SHEET_NAME = os.getenv("SPREADSHEET_NAME", "AcademyBotLeads")
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Пример: -1001234567890

# Telegram bot
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gc = gspread.authorize(credentials)
sheet = gc.open(GOOGLE_SHEET_NAME).sheet1

# Приветственное сообщение
WELCOME_TEXT = (
    "👋 Добро пожаловать в закрытый канал Академии «Бенефактор» Игоря Стрельникова и Максима Кучерова!\n\n"
    "Здесь вы сможете:\n"
    "• Изучить вводные бесплатные уроки\n"
    "• Получать свежие новости и обновления Академии\n"
    "• Пройти индивидуальные сессии с экспертами Академии (в стадии технической настройки)\n"
    "• Задать вопросы по обучению в специальной группе\n"
    "• Участвовать в видеовстречах и общаться с другими участниками\n"
    "• Спокойно понять, подходит ли вам наше обучение\n\n"
    "✍️ Пожалуйста, напишите в ответ несколько слов:\n"
    "какую пользу вы хотели бы получить и какие боли или задачи стремитесь решить с нашей помощью."
)

@dp.message(CommandStart())
async def handle_start(message: Message):
    await message.answer(WELCOME_TEXT)

@dp.message(F.text)
async def handle_response(message: Message):
    user = message.from_user
    user_data = [
        user.full_name,
        user.username or "",
        str(user.id),
        message.text
    ]
    sheet.append_row(user_data)
    await message.answer("✅ Спасибо! Мы добавляем вас в канал...")

    if CHANNEL_ID:
        try:
            await bot.send_message(CHANNEL_ID, f"➕ Новый участник: {hbold(user.full_name)} (@{user.username or 'без username'})")
            await bot.send_message(message.chat.id, "🎉 Готово! Проверьте, пожалуйста, доступ к закрытому каналу.")
        except Exception as e:
            logging.error(f"Ошибка при добавлении в канал: {e}")
            await message.answer("Произошла ошибка при добавлении в канал.")
    else:
        await message.answer("⚠️ Канал пока не подключён. Свяжитесь с администрацией.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))
