import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

# Настройки логирования
logging.basicConfig(level=logging.INFO)

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
INVITE_LINK = os.getenv("INVITE_LINK")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния анкеты
class Form(StatesGroup):
    name = State()
    goal = State()

# Стартовая команда
@dp.message_handler(commands='start')
async def start_cmd(message: types.Message):
    await Form.name.set()
    await message.reply("👋 Привет! Как тебя зовут?")

# Получаем имя
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await Form.next()
    await message.reply("💡 Расскажи, зачем ты хочешь присоединиться к Академии?")

# Получаем цель и завершаем анкету
@dp.message_handler(state=Form.goal)
async def process_goal(message: types.Message, state: FSMContext):
    await state.update_data(goal=message.text)
    data = await state.get_data()

    # Здесь можно сохранить ответы в Google Таблицу, если настроено
    name = data['name']
    goal = data['goal']
    logging.info(f"Новая анкета: {name} — {goal}")

    await message.reply("✅ Спасибо! Вот ссылка для входа в канал:\n" + INVITE_LINK)

    await state.finish()

# Запуск
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
