import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions
)



# =====================
# HANDLERS
# =====================

from handlers.start import router as start_router

from handlers.cabinet import router as cabinet_router

from handlers.stars_payment import router as stars_router

from handlers.transfer_payment import router as transfer_router

from handlers.payment_check import router as payment_check_router

from handlers.admin_panel import router as admin_router

from handlers.admin_payments import router as admin_payments_router



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

dp.include_router(
    start_router
)

dp.include_router(
    cabinet_router
)

dp.include_router(
    stars_router
)

dp.include_router(
    transfer_router
)

dp.include_router(
    payment_check_router
)

dp.include_router(
    admin_router
)

dp.include_router(
    admin_payments_router
)



# =====================
# START
# =====================

async def main():

    # создаём БД
    create_table()


    # отключаем просроченные подписки
    check_expired_subscriptions()


    print(
        "🦅 Орёл VPN бот запущен"
    )


    try:

        await dp.start_polling(
            bot
        )


    finally:

        await bot.session.close()



if __name__ == "__main__":

    asyncio.run(main())