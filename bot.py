import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import create_table

from subscription_checker import check_subscriptions



# =====================
# HANDLERS
# =====================

from handlers.start import router as start_router

from handlers.cabinet import router as cabinet_router

from handlers.admin_panel import router as admin_router

from handlers.admin_manage import router as admin_manage_router

from handlers.admin_broadcast import router as admin_broadcast_router

from handlers.admin_promos import router as admin_promos_router

from handlers.payments import router as payments_router



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
    payments_router
)


dp.include_router(
    admin_router
)


dp.include_router(
    admin_manage_router
)


dp.include_router(
    admin_broadcast_router
)


dp.include_router(
    admin_promos_router
)



# =====================
# START
# =====================

async def main():

    create_table()


    asyncio.create_task(
        check_subscriptions(bot)
    )


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