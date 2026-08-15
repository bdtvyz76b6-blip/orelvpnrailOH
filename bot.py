import asyncio
import threading
import os

from flask import Flask, request
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions,
    extend_subscription,
    get_payment_by_payment_id,
    update_payment_status
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

# Цикл Telegram-бота
BOT_LOOP = None


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

    if not data:

        print("⚠️ Пустой webhook")

        return "OK", 200


    # =====================
    # ПОЛУЧАЕМ TRANSACTION
    # =====================

    transaction = None


    if isinstance(data, dict):

        transaction = (
            data.get("transaction")
            or data.get("data")
            or data
        )


    elif isinstance(data, (list, tuple)):

        for item in data:

            if isinstance(item, dict):

                if (
                    "transaction" in item
                    or "status" in item
                    or "uuid" in item
                ):

                    transaction = item

                    break


    if not transaction:

        print(
            "⚠️ Transaction не найден"
        )

        return "OK", 200


    # =====================
    # ЕСЛИ TRANSACTION ВНУТРИ
    # =====================

    if isinstance(transaction, dict):

        transaction = (
            transaction.get("transaction")
            or transaction
        )


    if not isinstance(transaction, dict):

        print(
            "⚠️ Неверный формат transaction"
        )

        return "OK", 200


    # =====================
    # ДАННЫЕ ПЛАТЕЖА
    # =====================

    status = transaction.get(
        "status"
    )

    payment_uuid = transaction.get(
        "uuid"
    )

    external_id = transaction.get(
        "external_id"
    )


    print(
        f"💳 Статус: {status}"
    )

    print(
        f"🆔 UUID: {payment_uuid}"
    )

    print(
        f"🔗 External ID: {external_id}"
    )


    # =====================
    # ОБРАБАТЫВАЕМ ТОЛЬКО PAID
    # =====================

    if status != "paid":

        print(
            f"⏭ Платёж не оплачен: {status}"
        )

        return "OK", 200


    if not payment_uuid:

        print(
            "❌ В webhook отсутствует UUID"
        )

        return "OK", 200


    # =====================
    # ИЩЕМ ПЛАТЁЖ В БД
    # =====================

    try:

        payment = get_payment_by_payment_id(
            payment_uuid
        )

    except Exception as e:

        print(
            f"❌ Ошибка поиска платежа: {e}"
        )

        return "OK", 200


    if not payment:

        print(
            f"❌ Платёж {payment_uuid} "
            f"не найден в БД"
        )

        return "OK", 200


    # payment:
    #
    # 0 = id
    # 1 = user_id
    # 2 = photo
    # 3 = days
    # 4 = payment_id
    # 5 = status
    # 6 = created_at


    payment_db_id = payment[0]

    user_id = payment[1]

    days = payment[3]

    old_status = payment[5]


    # =====================
    # ЗАЩИТА ОТ ПОВТОРА
    # =====================

    if old_status == "paid":

        print(
            f"⏭ Платёж {payment_uuid} "
            f"уже был обработан"
        )

        return "OK", 200


    # =====================
    # ПРОВЕРКА ДНЕЙ
    # =====================

    if not days or days <= 0:

        print(
            f"❌ Неверное количество дней: {days}"
        )

        return "OK", 200


    # =====================
    # ВЫДАЧА ПОДПИСКИ
    # =====================

    try:

        new_date = extend_subscription(
            user_id,
            days
        )


        print(
            f"🎫 Подписка продлена:"
            f" {user_id} +{days} дней"
        )


        # =====================
        # GITHUB
        # =====================

        update_subscription_file(
            user_id,
            new_date
        )


        print(
            f"☂️ GitHub файл обновлён: "
            f"{user_id}"
        )


        # =====================
        # СТАТУС ПЛАТЕЖА
        # =====================

        update_payment_status(
            payment_db_id,
            "paid"
        )


        print(
            f"✅ Платёж {payment_uuid} "
            f"помечен как paid"
        )


        # =====================
        # TELEGRAM
        # =====================

        global BOT_LOOP


        if BOT_LOOP:

            asyncio.run_coroutine_threadsafe(

                bot.send_message(
                    user_id,

f"""
✅ Оплата успешно получена!

☂️ ixxy VPN

🎫 Подписка продлена
📅 Начислено: {days} дней

📅 Действует до:
{new_date}

🔄 Серверы обновлены автоматически.

Спасибо за покупку! ❤️
"""
                ),

                BOT_LOOP
            )


            print(
                f"📨 Уведомление отправлено "
                f"{user_id}"
            )

        else:

            print(
                "⚠️ BOT_LOOP ещё не запущен"
            )


    except Exception as e:

        print(
            f"❌ ОШИБКА ВЫДАЧИ ПОДПИСКИ "
            f"{user_id}: {e}"
        )

        return "OK", 200


    print(
        "✅ CASHeRA PAYMENT COMPLETED"
    )


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


    user_id = data.get(
        "user_id"
    )

    days = data.get(
        "days"
    )


    if not user_id or not days:

        return {
            "status": "error",
            "message": "missing data"
        }, 400


    try:

        user_id = int(
            user_id
        )

        days = int(
            days
        )


        if days <= 0:

            return {
                "status": "error",
                "message": "days must be greater than 0"
            }, 400


        new_date = extend_subscription(
            user_id,
            days
        )


        # =====================
        # GITHUB
        # =====================

        update_subscription_file(
            user_id,
            new_date
        )


        print(
            f"☂️ ixxycodes +{days} дней "
            f"пользователю {user_id}"
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

    global BOT_LOOP


    # =====================
    # EVENT LOOP
    # =====================

    BOT_LOOP = asyncio.get_running_loop()


    print(
        "☂️ Запуск ixxy VPN..."
    )


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

    try:

        asyncio.create_task(
            check_subscriptions(bot)
        )


        print(
            "🔄 Автоматическая проверка "
            "подписок запущена"
        )


    except Exception as e:

        print(
            "❌ Ошибка запуска проверки:",
            e
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

    # =====================
    # FLASK
    # =====================

    threading.Thread(
        target=run_webhook,
        daemon=True
    ).start()


    # =====================
    # TELEGRAM
    # =====================

    asyncio.run(
        main()
    )