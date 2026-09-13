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
    get_payment_by_payment_id,
    process_paid_payment,
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
# HELPERS
# =========================================================

def format_datetime(value):
    """
    Превращает datetime/date/строку
    в нормальный формат для Telegram.
    """

    if value is None:
        return "—"

    try:
        return value.strftime("%d.%m.%Y")
    except Exception:
        pass

    try:
        text = str(value)

        if "T" in text:
            text = text.split("T")[0]

        if " " in text:
            text = text.split(" ")[0]

        parts = text.split("-")

        if len(parts) == 3:
            return (
                f"{parts[2]}.{parts[1]}.{parts[0]}"
            )

        return text

    except Exception:
        return str(value)


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

    # =====================================================
    # API KEY
    # =====================================================

    received_api_key = request.headers.get(
        "X-Api-Key",
        "",
    ).strip()

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

    received_secret = request.headers.get(
        "X-Secret",
        "",
    ).strip()

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
    # DATA
    # =====================================================

    status = str(
        transaction.get(
            "status",
            "",
        )
    ).lower()

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
            f"⏭ Платёж ещё не оплачен: {status}"
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
            f"{type(e).__name__}: {e}"
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
    # POSTGRESQL DICT
    # =====================================================

    user_id = payment.get(
        "user_id"
    )

    days = payment.get(
        "days"
    )

    old_status = payment.get(
        "status"
    )

    provider = payment.get(
        "provider"
    )

    db_amount = payment.get(
        "amount"
    )

    print(
        f"👤 USER ID: {user_id}"
    )

    print(
        f"📅 DAYS: {days}"
    )

    print(
        f"📊 STATUS: {old_status}"
    )

    print(
        f"💳 PROVIDER: {provider}"
    )

    print(
        f"💰 DB AMOUNT: {db_amount}"
    )

    # =====================================================
    # ПРОВЕРКА ПРОВАЙДЕРА
    # =====================================================

    if provider:

        if str(provider).lower() != "cashera":

            print(
                f"❌ Платёж принадлежит другому "
                f"провайдеру: {provider}"
            )

            return "OK", 200

    # =====================================================
    # ЗАЩИТА ОТ ПОВТОРА
    # =====================================================

    if old_status == "paid":

        print(
            f"⏭ Платёж {payment_uuid} "
            f"уже обработан"
        )

        return "OK", 200

    # =====================================================
    # USER ID
    # =====================================================

    try:

        user_id = int(
            user_id
        )

    except Exception:

        print(
            f"❌ Некорректный user_id: {user_id}"
        )

        return "OK", 200

    # =====================================================
    # DAYS
    # =====================================================

    try:

        days = int(
            days
        )

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
                f"❌ Неверная валюта: {currency}"
            )

            return "OK", 200

    # =====================================================
    # ПРОВЕРКА СУММЫ
    #
    # CasheRa:
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
            f"💰 Ожидалось: {expected_amount}"
        )

        print(
            f"💰 Получено: {received_amount}"
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
    # ПРОВЕРКА СУММЫ С БД
    # =====================================================

    if db_amount is not None:

        try:

            db_amount_int = int(
                db_amount
            )

            if (
                expected_amount is not None
                and db_amount_int != expected_amount
            ):

                print(
                    "❌ Сумма в БД не соответствует тарифу"
                )

                print(
                    f"DB: {db_amount_int}"
                )

                print(
                    f"Expected: {expected_amount}"
                )

                return "OK", 200

        except Exception:

            print(
                "⚠️ Не удалось проверить amount из БД"
            )

    # =====================================================
    # ПОЛУЧАЕМ ПОДПИСКУ
    # =====================================================

    try:

        print(
            "🎫 Начинаем выдачу подписки..."
        )

        # -------------------------------------------------
        # СНАЧАЛА УЗНАЁМ ТЕКУЩУЮ ДАТУ И ПРОДЛЯЕМ
        # ЧЕРЕЗ АТОМАРНУЮ ФУНКЦИЮ БД
        # -------------------------------------------------

        result = process_paid_payment(
            payment_uuid
        )

        if not result:

            print(
                "❌ process_paid_payment "
                "вернул None"
            )

            return "OK", 200

        # -------------------------------------------------
        # ПЛАТЁЖ УЖЕ БЫЛ ОБРАБОТАН
        # -------------------------------------------------

        if result.get(
            "already_paid"
        ):

            print(
                f"⏭ Платёж {payment_uuid} "
                f"уже был обработан"
            )

            return "OK", 200

        new_date = result.get(
            "subscription_until"
        )

        print(
            f"🎫 Подписка продлена: "
            f"{user_id} +{days} дней"
        )

        print(
            f"📅 Новая дата: {new_date}"
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

    except Exception as e:

        print(
            "❌ ОШИБКА ВЫДАЧИ ПОДПИСКИ:"
        )

        print(
            f"{type(e).__name__}: {e}"
        )

        return "OK", 200

    # =====================================================
    # УВЕДОМЛЕНИЕ
    # =====================================================

    if BOT_LOOP:

        try:

            subscription_link = (
                make_subscription_link(
                    user_id
                )
            )

            date_text = format_datetime(
                new_date
            )

            message = f"""
✅ <b>Оплата успешно получена!</b>

☂️ <b>ixxy VPN</b>

🎫 Подписка продлена на:
<b>{days} дней</b>

📅 Действует до:
<b>{date_text}</b>

🔄 Подписка обновлена автоматически.

🔗 Ваша подписка:

{subscription_link}

Откройте ссылку в Happ.

Спасибо за покупку! ❤️
"""

            future = (
                asyncio.run_coroutine_threadsafe(
                    bot.send_message(
                        user_id,
                        message,
                        parse_mode="HTML",
                    ),
                    BOT_LOOP,
                )
            )

            try:
                future.result(
                    timeout=15
                )
            except Exception as e:
                print(
                    "⚠️ Ошибка отправки "
                    f"уведомления: {e}"
                )

            print(
                f"📨 Уведомление отправлено: "
                f"{user_id}"
            )

        except Exception as e:

            print(
                "⚠️ Ошибка формирования "
                f"уведомления: {e}"
            )

    else:

        print(
            "⚠️ BOT_LOOP ещё не запущен"
        )

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

        from database import (
            extend_subscription,
        )

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

        date_text = format_datetime(
            new_date
        )

        print(
            f"☂️ ixxycodes +{days} дней "
            f"пользователю {user_id}"
        )

        return {
            "status": "ok",
            "date": date_text,
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
# FLASK
# =========================================================

def run_webhook():

    port = int(
        os.getenv(
            "PORT",
            "8080",
        )
    )

    print(
        f"🌐 Flask запускается на порту {port}"
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
        "💾 PostgreSQL инициализирован"
    )

    # =====================================================
    # EXPIRED
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
    # GITHUB SYNC
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
    # SUBSCRIPTION CHECKER
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