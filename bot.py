import asyncio
import threading

from flask import Flask, request

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions
)

from github_update import create_subscription

from database import save_subscription_link



# =====================
# CASHeRA WEBHOOK
# =====================

app = Flask(__name__)


@app.route(
    "/webhook/cashera",
    methods=["POST"]
)
def cashera():

    data = request.json


    print(
        "💳 CASHeRA PAYMENT:"
    )

    print(
        data
    )


    return "OK", 200



def run_webhook():

    app.run(
        host="0.0.0.0",
        port=8080
    )





# =====================
# HANDLERS
# =====================

from handlers.start import router as start_router

from handlers.cabinet import router as cabinet_router

from handlers.stars_payment import router as stars_router

from handlers.sbp_payment import router as sbp_router

from handlers.admin_panel import router as admin_router

from handlers.admin_payments import router as admin_payments_router

# Новые обработчики админки
from handlers.admin_users import router as admin_users_router

from handlers.admin_search import router as admin_search_router

from handlers.admin_promos import router as admin_promos_router

from handlers.admin_stats import router as admin_stats_router

from handlers.admin_broadcast import router as admin_broadcast_router

from handlers.admin_settings import router as admin_settings_router





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
    sbp_router
)

dp.include_router(
    admin_router
)

dp.include_router(
    admin_payments_router
)

dp.include_router(
    admin_users_router
)

dp.include_router(
    admin_search_router
)

dp.include_router(
    admin_promos_router
)

dp.include_router(
    admin_stats_router
)

dp.include_router(
    admin_broadcast_router
)

dp.include_router(
    admin_settings_router
)





# =====================
# START
# =====================

async def main():


    create_table()


    check_expired_subscriptions()



    print(
        "☂️ ixxy vpn бот запущен"
    )


    try:

        await dp.start_polling(
            bot
        )


    finally:

        await bot.session.close()





if __name__ == "__main__":


    threading.Thread(
        target=run_webhook,
        daemon=True
    ).start()



    asyncio.run(
        main()
    )