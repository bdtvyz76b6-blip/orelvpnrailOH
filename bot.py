import asyncio
import threading
import os

from flask import Flask, request
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions,
    extend_subscription
)

from github_update import (
    update_subscription_file,
    sync_all_active_users
)

from subscription_checker import (
    check_subscriptions
)


# =====================
# WEBHOOK / API
# =====================

app = Flask(__name__)


# =====================
# CASHeRA WEBHOOK
# =====================

@app.route(
    "/webhook/cashera",
    methods=["POST"]
)
def cashera():

    data = request.json

    print("💳 CASHeRA PAYMENT:")
    print(data)

    return "OK", 200


# =====================
# IXXY CODES API
# =====================

@app.route(
    "/add-days",
    methods=["POST"]
)
def add_days_api():

    data = request.json

    if not data:
        return {
            "status": "error",
            "message": "no json"
        }, 400

    user_id = data.get("user_id")
    days = data.get("days")

    if not user_id or not days:
        return {
            "status": "error",
            "message": "missing data"
        }, 400

    try:

        user_id = int(user_id)
        days = int(days)

        new_date = extend_subscription(
            user_id,
            days
        )

        # Обновляем персональный файл
        update_subscription_file(
            user_id,
            new_date
        )

        print(
            f"☂️ ixxycodes +{days} дней пользователю {user_id}"
        )

        return {
            "status": "ok",
            "date": new_date
        }

    except Exception as e:

        print(
            "❌ ADD DAYS ERROR:",
            e
        )

        return {
            "status": "error",
            "message": str(e)
        }, 500


# =====================
# FLASK
# =====================

def run_webhook():

    port = int(
        os.getenv(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# =====================
# HANDLERS
# =====================

from handlers.start import router as start_router
from handlers.cabinet import router as cabinet_router
from handlers.stars_payment import router as stars_router
from handlers.sbp_payment import router as sbp_router


# =====================
# ADMIN
# =====================

from handlers.admin_panel import router as admin_router
from handlers.admin_payments import router as admin_payments_router
from handlers.admin_users import router as admin_users_router
from handlers.admin_search import router as admin_search_router
from handlers.admin_promos import router as admin_promos_router
from handlers.admin_stats import router as admin_stats_router
from handlers.admin_broadcast import router as admin_broadcast_router
from handlers.admin_settings import router as admin_settings_router
from handlers.admin_extend import router as admin_extend_router


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


# =====================
# ADMIN ROUTERS
# =====================

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

dp.include_router(
    admin_extend_router
)


# =====================
# START
# =====================

async def main():

    print("☂️ Запуск ixxy VPN...")


    # =====================
    # DATABASE
    # =====================

    create_table()

    print(
        "💾 База данных инициализирована"
    )


    # =====================
    # ПРОВЕРКА ПРОСРОЧЕННЫХ
    # =====================

    try:

        check_expired_subscriptions()

        print(
            "✅ Просроченные подписки проверены"
        )

    except Exception as e:

        print(
            "❌ Ошибка проверки подписок:",
            e
        )


    # =====================
    # СИНХРОНИЗАЦИЯ СЕРВЕРОВ
    # =====================

    try:

        sync_all_active_users()

        print(
            "✅ Серверы синхронизированы"
        )

    except Exception as e:

        print(
            "❌ Ошибка синхронизации серверов:",
            e
        )


    # =====================
    # АВТОПРОВЕРКА
    # =====================

    asyncio.create_task(
        check_subscriptions(bot)
    )

    print(
        "🔄 Автоматическая проверка подписок запущена"
    )


    # =====================
    # BOT
    # =====================

    print(
        "☂️ ixxy vpn бот запущен"
    )


    try:

        await dp.start_polling(
            bot
        )

    finally:

        await bot.session.close()


# =====================
# RUN
# =====================

if __name__ == "__main__":

    # Flask запускаем отдельно
    threading.Thread(
        target=run_webhook,
        daemon=True
    ).start()


    # Telegram bot
    asyncio.run(
        main()
    )