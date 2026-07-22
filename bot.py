import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from database import create_table


# =====================
# HANDLERS
# =====================

from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.payments import router as payments_router
from handlers.admin_panel import router as admin_panel_router



# =====================
# BOT
# =====================

bot = Bot(
    token=BOT_TOKEN
)


dp = Dispatcher()



# =====================
# ROUTERS
# =====================

dp.include_router(start_router)

dp.include_router(admin_router)

dp.include_router(payments_router)

dp.include_router(admin_panel_router)



# =====================
# START
# =====================

async def main():

    create_table()

    print("🦅 Орёл VPN бот запущен")


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(main())