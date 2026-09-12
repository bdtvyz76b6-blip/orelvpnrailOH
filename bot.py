import asyncio
import threading
import os
import hmac

from flask import Flask, request

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions,
    extend_subscription,
    get_payment_by_payment_id,
    update_payment_status,
)

from github_update import (
    update_subscription_file,
    sync_all_active_users,
    get_subscription_link as make_subscription_link,
)

from subscription_checker import check_subscriptions


# =========================================================
# WEBHOOK / API
# =========================================================

app = Flask(__name__)

BOT_LOOP = None


# =========================================================
# CASHERA
# =========================================================

CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY",
    "",
).strip()

CASHERA_API_SECRET = os.getenv(
    "CASHERA_API_SECRET",
    "",
).strip()


# =========================================================
# CASHERA WEBHOOK
# =========================================================

@app.route(
    "/webhook/cashera",
    methods=["POST"],
)
def cashera():

    print("")
    print("========================================")
    print("💳 CASHERA WEBHOOK RECEIVED")
    print("========================================")

    received_api_key = request.headers.get(
        "X-Api-Key",
        "",
    ).strip()

    received_secret = request.headers.get(
        "X-Secret",
        "",
    ).strip()

    # =====================================================
    # API KEY
    # =====================================================

    if CASHERA_API_KEY:

        if not hmac.compare_digest(
            received_api_key,
            CASHERA_API_KEY,
        ):

            print(
                "❌ Неверный X-Api-Key"
            )

            return (
                "Unauthorized",
                401,
            )

    # =====================================================
    # SECRET
    # =====================================================

    if CASHERA_API_SECRET:

        if not hmac.compare_digest(
            received_secret,
            CASHERA_API_SECRET,
        ):

            print(
                "❌ Неверный X-Secret"
            )

            return (
                "Unauthorized",
                401,
            )

    # =====================================================
    # JSON
    # =====================================================

    data = request.get_json(
        silent=True,
    )

    print("💳 CASHERA DATA:")
    print(data)

    if not data:

        print(
            "⚠️ Пустой webhook"
        )

        return "OK", 200

    # =====================================================
    # ПОИСК TRANSACTION
    # =====================================================

    transaction = None

    if isinstance(
        data,
        dict,
    ):

        transaction = (
            data.get("transaction")
            or data.get("data")
            or data.get("result")
            or data
        )

    elif isinstance(
        data,
        (list, tuple),
    ):

        for item in data:

            if not isinstance(
                item,
                dict,
            ):
                continue

            if (
                "transaction" in item
                or "status" in item
                or "uuid" in item
            ):

                transaction = item

                break

    # =====================================================
    # NESTED TRANSACTION
    # =====================================================

    if isinstance(
        transaction,
        dict,
    ):

        nested_transaction = transaction.get(
            "transaction"
        )

        if isinstance(
            nested_transaction,
            dict,
        ):

            transaction = nested_transaction

    if not isinstance(
        transaction,
        dict,
    ):

        print(
            "⚠️ Неверный формат transaction"
        )

        return "OK", 200

    print("💳 TRANSACTION:")
    print(transaction)

    # =====================================================
    # ДАННЫЕ
    # =====================================================

    status = transaction.get(
        "status"
    )

    payment_uuid = (
        transaction.get("uuid")
        or transaction.get("id")
    )

    external_id = transaction.get(
        "external_id"
    )

    amount = transaction.get(
        "amount"
    )

    currency = transaction.get(
        "currency"
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

    print(
        f"💰 Amount: {amount}"
    )

    print(
        f"💱 Currency: {currency}"
    )

    # =====================================================
    # ТОЛЬКО PAID
    # =====================================================

    if status != "paid":

        print(
            f"⏭ Платёж ещё не оплачен: "
            f"{status}"
        )

        return "OK", 200

    if not payment_uuid:

        print(
            "❌ В webhook отсутствует UUID"
        )

        return "OK", 200

    payment_uuid = str(
        payment_uuid
    )

    # =====================================================
    # ПОИСК ПЛАТЕЖА
    # =====================================================

    try:

        payment = get_payment_by_payment_id(
            payment_uuid
        )

    except Exception as e:

        print(
            "❌ Ошибка поиска платежа:"
        )

        print(
            type(e).__name__,
            str(e),
        )

        return "OK", 200

    if not payment:

        print(
            "❌ Платёж не найден в БД"
        )

        print(
            f"UUID: {payment_uuid}"
        )

        return "OK", 200

    # =====================================================
    # ДАННЫЕ ПЛАТЕЖА
    # =====================================================

    payment_db_id = payment[0]
    user_id = payment[1]
    days = payment[3]
    old_status = payment[5]

    print(
        f"🆔 DB PAYMENT ID: "
        f"{payment_db_id}"
    )

    print(
        f"👤 USER ID: "
        f"{user_id}"
    )

    print(
        f"📅 DAYS: "
        f"{days}"
    )

    print(
        f"📊 STATUS: "
        f"{old_status}"
    )

    # =====================================================
    # ЗАЩИТА ОТ ПОВТОРНОЙ ВЫДАЧИ
    # =====================================================

    if old_status == "paid":

        print(
            f"⏭ Платёж {payment_uuid} "
            f"уже обработан"
        )

        return "OK", 200

    # =====================================================
    # DAYS
    # =====================================================

    if not days:

        print(
            "❌ У платежа отсутствует days"
        )

        return "OK", 200

    try:

        days = int(days)

    except Exception:

        print(
            f"❌ Некорректный days: {days}"
        )

        return "OK", 200

    if days <= 0:

        print(
            f"❌ Некорректный срок: {days}"
        )

        return "OK", 200

    # =====================================================
    # ВАЛЮТА
    # =====================================================

    if currency:

        if str(
            currency
        ).upper() != "RUB":

            print(
                f"❌ Неверная валюта: "
                f"{currency}"
            )

            return "OK", 200

    # =====================================================
    # ПРОВЕРКА СУММЫ
    #
    # Cashera передаёт amount в копейках.
    #
    # 129 ₽  = 12900
    # 379 ₽  = 37900
    # 659 ₽  = 65900
    # 1089 ₽ = 108900
    # =====================================================

    expected_amounts = {

        30: 12900,

        90: 37900,

        180: 65900,

        365: 108900,

    }

    expected_amount = expected_amounts.get(
        days
    )

    if expected_amount is not None:

        try:

            received_amount = int(
                float(amount)
            )

        except Exception:

            received_amount = None

        if received_amount is None:

            print(
                "❌ Не удалось определить "
                "сумму платежа"
            )

            return "OK", 200

        print(
            f"💰 Ожидалось: "
            f"{expected_amount}"
        )

        print(
            f"💰 Получено: "
            f"{received_amount}"
        )

        if received_amount != expected_amount:

            print(
                "❌ НЕСОВПАДЕНИЕ СУММЫ!"
            )

            return "OK", 200

        print(
            "✅ Сумма платежа совпадает"
        )

    # =====================================================
    # ВЫДАЧА ПОДПИСКИ
    # =====================================================

    try:

        print(
            "🎫 Начинаем выдачу подписки..."
        )

        # -------------------------------------------------
        # ПРОДЛЕВАЕМ ПОДПИСКУ
        # -------------------------------------------------

        new_date = extend_subscription(
            user_id,
            days,
        )

        print(
            f"🎫 Подписка продлена: "
            f"{user_id} "
            f"+{days} дней"
        )

        print(
            f"📅 Новая дата: "
            f"{new_date}"
        )

        # -------------------------------------------------
        # ОБНОВЛЯЕМ GITHUB
        # -------------------------------------------------

        update_subscription_file(
            user_id,
            new_date,
        )

        print(
            f"☂️ GitHub subscription "
            f"обновлён: {user_id}"
        )

        # -------------------------------------------------
        # ПОМЕЧАЕМ ПЛАТЁЖ PAID
        # -------------------------------------------------

        update_payment_status(
            payment_db_id,
            "paid",
        )

        print(
            f"✅ Платёж "
            f"{payment_uuid} "
            f"помечен как paid"
        )

        # -------------------------------------------------
        # УВЕДОМЛЕНИЕ
        # -------------------------------------------------

        if BOT_LOOP:

            subscription_link = (
                make_subscription_link(
                    user_id
                )
            )

            message = f"""
✅ Оплата успешно получена!

☂️ ixxy VPN

🎫 Подписка продлена

📅 Начислено:
{days} дней

📅 Действует до:
{new_date}

🔄 Подписка обновлена автоматически.

🔗 Ваша подписка:
{subscription_link}

Откройте эту ссылку в Happ.

Спасибо за покупку! ❤️
"""

            asyncio.run_coroutine_threadsafe(

                bot.send_message(
                    user_id,
                    message,
                ),

                BOT_LOOP,
            )

            print(
                f"📨 Уведомление отправлено: "
                f"{user_id}"
            )

        else:

            print(
                "⚠️ BOT_LOOP ещё не запущен"
            )

    except Exception as e:

        print(
            "❌ ОШИБКА ВЫДАЧИ ПОДПИСКИ:"
        )

        print(
            f"{type(e).__name__}: {e}"
        )

        return "OK", 200

    print(
        "========================================"
    )

    print(
        "✅ CASHERA PAYMENT COMPLETED"
    )

    print(
        "========================================"
    )

    return "OK", 200


# =========================================================
# IXXY CODES API
# =========================================================

@app.route(
    "/add-days",
    methods=["POST"],
)
def add_days_api():

    data = request.get_json(
        silent=True
    )

    if not data:

        return {
            "status": "error",
            "message": "no json",
        }, 400

    user_id = data.get(
        "user_id"
    )

    days = data.get(
        "days"
    )

    if (
        user_id is None
        or days is None
    ):

        return {
            "status": "error",
            "message": "missing data",
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
                "message":
                    "days must be greater than 0",
            }, 400

        new_date = extend_subscription(
            user_id,
            days,
        )

        update_subscription_file(
            user_id,
            new_date,
        )

        subscription_link = (
            make_subscription_link(
                user_id
            )
        )

        print(
            f"☂️ ixxycodes +{days} дней "
            f"пользователю {user_id}"
        )

        return {

            "status": "ok",

            "date": new_date,

            "subscription":
                subscription_link,

        }

    except Exception as e:

        print(
            "❌ ADD DAYS ERROR:",
            e,
        )

        return {

            "status": "error",

            "message": str(e),

        }, 500


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/",
    methods=["GET"],
)
def home():

    return {
        "service": "ixxy VPN",
        "status": "ok",
    }


@app.route(
    "/health",
    methods=["GET"],
)
def health():

    return {
        "status": "ok",
    }


# =========================================================
# FLASK / WEBHOOK
# =========================================================

def run_webhook():

    port = int(
        os.getenv(
            "PORT",
            "8080",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )


# =========================================================
# USER HANDLERS
# =========================================================

from handlers.start import (
    router as start_router
)

from handlers.cabinet import (
    router as cabinet_router
)

from handlers.stars_payment import (
    router as stars_router
)

from handlers.sbp_payment import (
    router as sbp_router
)


# =========================================================
# ADMIN HANDLERS
# =========================================================

from handlers.admin_panel import (
    router as admin_router
)

from handlers.admin_payments import (
    router as admin_payments_router
)

from handlers.admin_users import (
    router as admin_users_router
)

from handlers.admin_search import (
    router as admin_search_router
)

from handlers.admin_promos import (
    router as admin_promos_router
)

from handlers.admin_stats import (
    router as admin_stats_router
)

from handlers.admin_broadcast import (
    router as admin_broadcast_router
)

from handlers.admin_settings import (
    router as admin_settings_router
)

from handlers.admin_extend import (
    router as admin_extend_router
)


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# USER ROUTERS
# =========================================================

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


# =========================================================
# ADMIN ROUTERS
# =========================================================

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


# =========================================================
# START
# =========================================================

async def main():

    global BOT_LOOP

    BOT_LOOP = (
        asyncio.get_running_loop()
    )

    print(
        "☂️ Запуск ixxy VPN..."
    )

    # =====================================================
    # DATABASE
    # =====================================================

    create_table()

    print(
        "💾 База данных инициализирована"
    )

    # =====================================================
    # ПРОВЕРКА ПРОСРОЧЕННЫХ
    # =====================================================

    try:

        check_expired_subscriptions()

        print(
            "✅ Просроченные подписки проверены"
        )

    except Exception as e:

        print(
            "❌ Ошибка проверки подписок:",
            e,
        )

    # =====================================================
    # СИНХРОНИЗАЦИЯ
    # =====================================================

    try:

        sync_all_active_users()

        print(
            "✅ GitHub-подписки синхронизированы"
        )

    except Exception as e:

        print(
            "❌ Ошибка синхронизации:",
            e,
        )

    # =====================================================
    # АВТОПРОВЕРКА
    # =====================================================

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
            e,
        )

    # =====================================================
    # BOT
    # =====================================================

    print(
        "☂️ ixxy VPN бот запущен"
    )

    try:

        await dp.start_polling(
            bot
        )

    finally:

        await bot.session.close()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    threading.Thread(
        target=run_webhook,
        daemon=True,
    ).start()

    asyncio.run(
        main()
    )