import asyncio
import os
import threading
import hmac
import logging

from flask import Flask, request
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, ADMIN_IDS

from database import (
    create_table,
    check_expired_subscriptions,
    get_payment_by_payment_id,
    process_paid_payment,
    extend_subscription,
)

from github_update import (
    update_subscription_file,
    sync_all_active_users,
    get_subscription_link as make_subscription_link,
)

from subscription_checker import check_subscriptions


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# =========================================================
# ADMIN IDS
# =========================================================

def normalize_admin_ids(value):
    result = set()

    if value is None:
        return result

    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = str(value).replace(",", " ").split()

    for item in items:
        try:
            result.add(int(str(item).strip()))
        except Exception:
            pass

    return result


ADMIN_IDS = normalize_admin_ids(ADMIN_IDS)

logger.info(
    "👑 ADMIN IDS: %s",
    sorted(ADMIN_IDS),
)


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

BOT_LOOP = None


def run_webhook():
    port = int(
        os.getenv(
            "PORT",
            "8080",
        )
    )

    logger.info(
        "🌐 Flask запускается на порту %s",
        port,
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
    )


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

    if value is None:
        return "—"

    try:
        if hasattr(value, "strftime"):
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

    logger.info(
        "💳 CASHERA WEBHOOK RECEIVED"
    )

    # -----------------------------------------------------
    # API KEY
    # -----------------------------------------------------

    received_api_key = request.headers.get(
        "X-Api-Key",
        "",
    ).strip()

    if CASHERA_API_KEY:

        if not hmac.compare_digest(
            received_api_key,
            CASHERA_API_KEY,
        ):

            logger.warning(
                "❌ Неверный X-Api-Key"
            )

            return "Unauthorized", 401

    # -----------------------------------------------------
    # SECRET
    # -----------------------------------------------------

    received_secret = request.headers.get(
        "X-Secret",
        "",
    ).strip()

    if CASHERA_API_SECRET:

        if not hmac.compare_digest(
            received_secret,
            CASHERA_API_SECRET,
        ):

            logger.warning(
                "❌ Неверный X-Secret"
            )

            return "Unauthorized", 401

    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    )

    logger.info(
        "💳 CASHERA DATA: %s",
        data,
    )

    if not data:
        return "OK", 200

    # -----------------------------------------------------
    # TRANSACTION
    # -----------------------------------------------------

    transaction = None

    if isinstance(data, dict):

        transaction = (
            data.get("transaction")
            or data.get("data")
            or data.get("result")
            or data
        )

    elif isinstance(data, (list, tuple)):

        for item in data:

            if not isinstance(item, dict):
                continue

            if (
                "transaction" in item
                or "status" in item
                or "uuid" in item
            ):

                transaction = item
                break

    if isinstance(transaction, dict):

        nested = transaction.get(
            "transaction"
        )

        if isinstance(nested, dict):
            transaction = nested

    if not isinstance(
        transaction,
        dict,
    ):
        return "OK", 200

    logger.info(
        "💳 TRANSACTION: %s",
        transaction,
    )

    status = str(
        transaction.get(
            "status",
            "",
        )
    ).strip().lower()

    payment_uuid = (
        transaction.get("uuid")
        or transaction.get("id")
    )

    amount = transaction.get(
        "amount"
    )

    currency = transaction.get(
        "currency"
    )

    logger.info(
        "💳 status=%s uuid=%s amount=%s currency=%s",
        status,
        payment_uuid,
        amount,
        currency,
    )

    # -----------------------------------------------------
    # ONLY PAID
    # -----------------------------------------------------

    if status != "paid":

        logger.info(
            "⏭ Платёж ещё не оплачен: %s",
            status,
        )

        return "OK", 200

    if not payment_uuid:

        logger.warning(
            "❌ UUID отсутствует"
        )

        return "OK", 200

    payment_uuid = str(
        payment_uuid
    )

    # -----------------------------------------------------
    # FIND PAYMENT
    # -----------------------------------------------------

    try:

        payment = get_payment_by_payment_id(
            payment_uuid
        )

    except Exception:

        logger.exception(
            "❌ Ошибка поиска платежа"
        )

        return "OK", 200

    if not payment:

        logger.warning(
            "❌ Платёж не найден: %s",
            payment_uuid,
        )

        return "OK", 200

    # -----------------------------------------------------
    # PAYMENT DATA
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PROVIDER
    # -----------------------------------------------------

    if provider:

        if str(provider).lower() != "cashera":

            logger.warning(
                "❌ Другой provider: %s",
                provider,
            )

            return "OK", 200

    # -----------------------------------------------------
    # ALREADY PAID
    # -----------------------------------------------------

    if str(old_status).lower() == "paid":

        logger.info(
            "⏭ Платёж уже обработан: %s",
            payment_uuid,
        )

        return "OK", 200

    # -----------------------------------------------------
    # USER / DAYS
    # -----------------------------------------------------

    try:

        user_id = int(user_id)
        days = int(days)

    except Exception:

        logger.warning(
            "❌ Некорректные user_id/days"
        )

        return "OK", 200

    if days <= 0:
        return "OK", 200

    # -----------------------------------------------------
    # CURRENCY
    # -----------------------------------------------------

    if currency:

        if str(currency).upper() != "RUB":

            logger.warning(
                "❌ Неверная валюта: %s",
                currency,
            )

            return "OK", 200

    # -----------------------------------------------------
    # EXPECTED AMOUNTS
    # -----------------------------------------------------

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

            logger.warning(
                "❌ Невозможно определить сумму"
            )

            return "OK", 200

        if received_amount != expected_amount:

            logger.warning(
                "❌ Неверная сумма: "
                "получено=%s ожидалось=%s",
                received_amount,
                expected_amount,
            )

            return "OK", 200

    # -----------------------------------------------------
    # DB AMOUNT
    # -----------------------------------------------------

    if db_amount is not None:

        try:

            db_amount_int = int(
                db_amount
            )

            if (
                expected_amount is not None
                and db_amount_int != expected_amount
            ):

                logger.warning(
                    "❌ Неверная сумма в БД"
                )

                return "OK", 200

        except Exception:
            pass

    # -----------------------------------------------------
    # PROCESS PAYMENT
    # -----------------------------------------------------

    try:

        result = process_paid_payment(
            payment_uuid
        )

        if not result:

            logger.warning(
                "❌ process_paid_payment "
                "вернул None"
            )

            return "OK", 200

        if result.get("already_paid"):

            logger.info(
                "⏭ Платёж уже обработан"
            )

            return "OK", 200

        new_date = result.get(
            "subscription_until"
        )

        update_subscription_file(
            user_id
        )

        logger.info(
            "☂️ Подписка выдана: "
            "user=%s days=%s until=%s",
            user_id,
            days,
            new_date,
        )

    except Exception:

        logger.exception(
            "❌ ОШИБКА ВЫДАЧИ ПОДПИСКИ"
        )

        return "OK", 200

    # -----------------------------------------------------
    # TELEGRAM NOTIFICATION
    # -----------------------------------------------------

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

            message = (
                "✅ <b>Оплата успешно получена!</b>\n\n"
                "☂️ <b>ixxy VPN</b>\n\n"
                f"🎫 Подписка продлена на: "
                f"<b>{days} дней</b>\n\n"
                f"📅 Действует до: "
                f"<b>{date_text}</b>\n\n"
                "🔗 Ваша подписка:\n\n"
                f"{subscription_link}\n\n"
                "Откройте ссылку в Happ.\n\n"
                "Спасибо за покупку! ❤️"
            )

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

            future.result(
                timeout=15
            )

            logger.info(
                "📨 Уведомление отправлено: %s",
                user_id,
            )

        except Exception:

            logger.exception(
                "⚠️ Ошибка Telegram-уведомления"
            )

    return "OK", 200


# =========================================================
# IXXY ADD DAYS API
# =========================================================

@app.route(
    "/add-days",
    methods=["POST"],
)
def add_days_api():

    secret = os.getenv(
        "IXXY_API_SECRET",
        "",
    ).strip()

    received_secret = request.headers.get(
        "X-IXXY-Secret",
        "",
    ).strip()

    if secret:

        if not hmac.compare_digest(
            received_secret,
            secret,
        ):

            return {
                "status": "error",
                "message": "unauthorized",
            }, 401

    data = request.get_json(
        silent=True
    )

    if not data:

        return {
            "status": "error",
            "message": "no json",
        }, 400

    try:

        user_id = int(
            data.get("user_id")
        )

        days = int(
            data.get("days")
        )

    except Exception:

        return {
            "status": "error",
            "message": "invalid user_id or days",
        }, 400

    if days <= 0:

        return {
            "status": "error",
            "message": "days must be greater than 0",
        }, 400

    try:

        new_date = extend_subscription(
            user_id,
            days,
        )

        update_subscription_file(
            user_id
        )

        subscription_link = (
            make_subscription_link(
                user_id
            )
        )

        return {
            "status": "ok",
            "date": format_datetime(
                new_date
            ),
            "subscription": subscription_link,
        }

    except Exception as e:

        logger.exception(
            "❌ ADD DAYS ERROR"
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

from handlers.admin import (
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
# MAIN
# =========================================================

async def main():

    global BOT_LOOP

    BOT_LOOP = asyncio.get_running_loop()

    logger.info(
        "☂️ Запуск ixxy VPN..."
    )

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    try:

        create_table()

        logger.info(
            "💾 PostgreSQL готов"
        )

    except Exception:

        logger.exception(
            "❌ Ошибка инициализации PostgreSQL"
        )

        raise

    # -----------------------------------------------------
    # EXPIRED
    # -----------------------------------------------------

    try:

        check_expired_subscriptions()

        logger.info(
            "✅ Проверка подписок выполнена"
        )

    except Exception:

        logger.exception(
            "❌ Ошибка проверки подписок"
        )

    # -----------------------------------------------------
    # GITHUB
    # -----------------------------------------------------

    try:

        sync_all_active_users()

        logger.info(
            "✅ Подписки синхронизированы"
        )

    except Exception:

        logger.exception(
            "❌ Ошибка GitHub-синхронизации"
        )

    # -----------------------------------------------------
    # CHECKER
    # -----------------------------------------------------

    try:

        asyncio.create_task(
            check_subscriptions(
                bot
            )
        )

        logger.info(
            "🔄 Subscription checker запущен"
        )

    except Exception:

        logger.exception(
            "❌ Ошибка запуска checker"
        )

    # -----------------------------------------------------
    # POLLING
    # -----------------------------------------------------

    logger.info(
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

    logger.info(
        "🚀 Запуск Flask + Telegram..."
    )

    threading.Thread(
        target=run_webhook,
        daemon=True,
    ).start()

    asyncio.run(
        main()
    )