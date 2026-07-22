import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import create_table

# Подключаем хендлеры
from handlers.start import router as start_router
from handlers.admin import router as admin_router
# from handlers.payments import router as payments_router


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Подключаем роутеры
dp.include_router(start_router)
dp.include_router(admin_router)
# dp.include_router(payments_router)


async def main():
    create_table()

    print("🦅 Орёл VPN бот запущен")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())