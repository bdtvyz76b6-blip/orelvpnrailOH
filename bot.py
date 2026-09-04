import asyncio
import threading
import os
import hmac

from urllib.parse import quote

from flask import Flask, request, Response

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

from database import (
    create_table,
    check_expired_subscriptions,
    extend_subscription,
    get_payment_by_payment_id,
    update_payment_status,
    get_subscription_content,
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
# PUBLIC SITE
# =========================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")


SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy"
).strip()


# =========================================================
# CASHERA
# =========================================================

CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY",
    ""
).strip()


CASHERA_API_SECRET = os.getenv(
    "CASHERA_API_SECRET",
    ""
).strip()


# =========================================================
# ПОЛУЧЕНИЕ USER ID ИЗ КРАСИВОГО ТОКЕНА
# =========================================================

def get_user_id_from_token(token):

    prefix = SUBSCRIPTION_PREFIX

    if not token.startswith(prefix):
        return None

    user_id_text = token[len(prefix):]

    if not user_id_text.isdigit():
        return None

    try:
        return int(user_id_text)

    except Exception:
        return None


# =========================================================
# HTML СТРАНИЦЫ ПОДПИСКИ
# =========================================================

def subscription_page_html(
    user_id,
    subscription_url
):

    happ_url = (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    incy_url = (
        "incy://import/"
        + subscription_url
    )

    escaped_subscription = (
        subscription_url
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace('"', '\\"')
    )

    return f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="theme-color"
    content="#08080d"
>

<title>
    ixxy VPN — Подписка
</title>

<style>

* {{
    box-sizing: border-box;
}}

html,
body {{
    margin: 0;
    padding: 0;
    min-height: 100%;
}}

body {{
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at top,
            #24213d 0%,
            #0c0b12 45%,
            #07070b 100%
        );

    color: #ffffff;

    display: flex;

    justify-content: center;

    padding:
        24px
        16px
        40px;
}}

.container {{
    width: 100%;
    max-width: 520px;
}}

.logo {{
    width: 78px;
    height: 78px;

    margin:
        20px auto
        18px;

    border-radius: 24px;

    background:
        linear-gradient(
            135deg,
            #9b7cff,
            #6d4aff
        );

    display: flex;

    align-items: center;
    justify-content: center;

    font-size: 40px;

    box-shadow:
        0 18px 60px
        rgba(119, 80, 255, .35);
}}

h1 {{
    text-align: center;

    margin: 0;

    font-size: 32px;

    font-weight: 800;

    letter-spacing: -1px;
}}

.subtitle {{
    text-align: center;

    margin:
        9px
        0
        28px;

    color: #a9a7b5;

    font-size: 15px;
}}

.card {{
    background:
        rgba(255,255,255,.065);

    border:
        1px solid
        rgba(255,255,255,.09);

    border-radius: 26px;

    padding: 22px;

    backdrop-filter:
        blur(22px);

    box-shadow:
        0 25px 80px
        rgba(0,0,0,.35);
}}

.title {{
    font-size: 19px;

    font-weight: 750;

    margin-bottom: 9px;
}}

.description {{
    color: #aaa8b6;

    line-height: 1.55;

    font-size: 14px;

    margin-bottom: 20px;
}}

.button {{
    display: flex;

    width: 100%;

    min-height: 56px;

    align-items: center;

    justify-content: center;

    border-radius: 17px;

    text-decoration: none;

    font-size: 16px;

    font-weight: 700;

    margin-top: 11px;

    transition:
        transform .15s ease,
        opacity .15s ease;
}}

.button:active {{
    transform: scale(.98);

    opacity: .8;
}}

.happ {{
    background:
        linear-gradient(
            135deg,
            #8e6cff,
            #6543ff
        );

    color: white;

    box-shadow:
        0 12px 35px
        rgba(103,68,255,.28);
}}

.incy {{
    background:
        rgba(255,255,255,.10);

    border:
        1px solid
        rgba(255,255,255,.12);

    color: white;
}}

.copy {{
    background:
        rgba(255,255,255,.055);

    border:
        1px solid
        rgba(255,255,255,.09);

    color: #dddce5;

    cursor: pointer;
}}

.link-box {{
    margin-top: 20px;

    padding: 14px;

    border-radius: 15px;

    background:
        rgba(0,0,0,.25);

    border:
        1px solid
        rgba(255,255,255,.07);

    word-break: break-all;

    color: #92909e;

    font-size: 12px;

    line-height: 1.5;
}}

.steps {{
    margin-top: 18px;

    display: grid;

    gap: 10px;
}}

.step {{
    display: flex;

    gap: 12px;

    align-items: flex-start;

    padding: 13px;

    border-radius: 15px;

    background:
        rgba(255,255,255,.035);
}}

.number {{
    width: 27px;
    height: 27px;

    min-width: 27px;

    border-radius: 9px;

    background: #29233e;

    color: #a98dff;

    display: flex;

    align-items: center;
    justify-content: center;

    font-weight: 800;

    font-size: 13px;
}}

.step-text {{
    color: #aaa8b5;

    font-size: 13px;

    line-height: 1.45;
}}

.footer {{
    text-align: center;

    margin-top: 22px;

    color: #666472;

    font-size: 12px;
}}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        ☂️
    </div>

    <h1>
        ixxy VPN
    </h1>

    <div class="subtitle">
        Ваша персональная подписка
    </div>

    <div class="card">

        <div class="title">
            🚀 Добавьте подписку
        </div>

        <div class="description">

            Выберите приложение ниже.

            После нажатия подписка автоматически
            откроется в выбранном VPN-клиенте.

        </div>

        <a
            class="button happ"
            href="{happ_url}"
        >
            🟣 Добавить в Happ
        </a>

        <a
            class="button incy"
            href="{incy_url}"
        >
            🟢 Добавить в INCY
        </a>

        <button
            class="button copy"
            onclick="copySubscription()"
            id="copyButton"
        >
            📋 Скопировать ссылку
        </button>

        <div class="link-box">
            {subscription_url}
        </div>

        <div class="steps">

            <div class="step">

                <div class="number">
                    1
                </div>

                <div class="step-text">

                    Установите Happ или INCY,
                    если приложение ещё не установлено.

                </div>

            </div>


            <div class="step">

                <div class="number">
                    2
                </div>

                <div class="step-text">

                    Нажмите кнопку
                    «Добавить подписку».

                </div>

            </div>


            <div class="step">

                <div class="number">
                    3
                </div>

                <div class="step-text">

                    Подписка загрузится автоматически.

                    После этого выберите сервер
                    и подключитесь.

                </div>

            </div>

        </div>

    </div>

    <div class="footer">
        ixxy VPN • ID {user_id}
    </div>

</div>


<script>

const subscriptionUrl =
    '{escaped_subscription}';


async function copySubscription() {{

    const button =
        document.getElementById(
            'copyButton'
        );

    try {{

        await navigator.clipboard.writeText(
            subscriptionUrl
        );

        button.innerText =
            '✅ Ссылка скопирована';

        setTimeout(() => {{

            button.innerText =
                '📋 Скопировать ссылку';

        }}, 1800);

    }}

    catch (error) {{

        const textarea =
            document.createElement(
                'textarea'
            );

        textarea.value =
            subscriptionUrl;

        document.body.appendChild(
            textarea
        );

        textarea.select();

        document.execCommand(
            'copy'
        );

        textarea.remove();

        button.innerText =
            '✅ Ссылка скопирована';

        setTimeout(() => {{

            button.innerText =
                '📋 Скопировать ссылку';

        }}, 1800);

    }}

}}

</script>

</body>

</html>
"""


# =========================================================
# СТРАНИЦА ПОДПИСКИ
# =========================================================

@app.route(
    "/s/<token>",
    methods=["GET"]
)
def subscription_page(token):

    user_id = get_user_id_from_token(
        token
    )

    if not user_id:

        return (
            "<h1>404</h1>"
            "<p>Неверная ссылка подписки.</p>",
            404
        )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )

    return Response(

        subscription_page_html(
            user_id,
            subscription_url
        ),

        mimetype="text/html"
    )


# =========================================================
# ЧИСТАЯ ПОДПИСКА
# =========================================================

@app.route(
    "/sub/<token>",
    methods=["GET"]
)
def subscription_endpoint(token):

    user_id = get_user_id_from_token(
        token
    )

    if not user_id:

        return (
            "Invalid subscription",
            404
        )

    content = get_subscription_content(
        user_id
    )

    if not content:

        return (
            "Subscription not found",
            404
        )

    return Response(
        content,
        status=200,
        mimetype="text/plain"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return {
        "service": "ixxy VPN",
        "status": "ok"
    }


@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return {
        "status": "ok"
    }


# =========================================================
# CASHERA WEBHOOK
# =========================================================

@app.route(
    "/webhook/cashera",
    methods=["POST"]
)
def cashera():

    print("")
    print("========================================")
    print("💳 CASHERA WEBHOOK RECEIVED")
    print("========================================")


    # =====================================================
    # ПРОВЕРКА API KEY
    # =====================================================

    received_api_key = request.headers.get(
        "X-Api-Key",
        ""
    ).strip()


    received_secret = request.headers.get(
        "X-Secret",
        ""
    ).strip()


    if CASHERA_API_KEY:

        if not hmac.compare_digest(
            received_api_key,
            CASHERA_API_KEY
        ):

            print(
                "❌ Неверный X-Api-Key"
            )

            return (
                "Unauthorized",
                401
            )


    if CASHERA_API_SECRET:

        if not hmac.compare_digest(
            received_secret,
            CASHERA_API_SECRET
        ):

            print(
                "❌ Неверный X-Secret"
            )

            return (
                "Unauthorized",
                401
            )


    # =====================================================
    # ПОЛУЧАЕМ JSON
    # =====================================================

    data = request.get_json(
        silent=True
    )


    print(
        "💳 CASHERA DATA:"
    )

    print(data)


    if not data:

        print(
            "⚠️ Пустой webhook"
        )

        return "OK", 200


    # =====================================================
    # ИЩЕМ TRANSACTION
    # =====================================================

    transaction = None


    if isinstance(
        data,
        dict
    ):

        transaction = (

            data.get(
                "transaction"
            )

            or

            data.get(
                "data"
            )

            or

            data.get(
                "result"
            )

            or

            data

        )


    elif isinstance(
        data,
        (list, tuple)
    ):

        for item in data:

            if not isinstance(
                item,
                dict
            ):
                continue


            if (

                "transaction"
                in item

                or

                "status"
                in item

                or

                "uuid"
                in item

            ):

                transaction = item

                break


    # =====================================================
    # ЕСЛИ TRANSACTION ВЛОЖЕН
    # =====================================================

    if isinstance(
        transaction,
        dict
    ):

        nested_transaction = (
            transaction.get(
                "transaction"
            )
        )


        if isinstance(
            nested_transaction,
            dict
        ):

            transaction = (
                nested_transaction
            )


    if not isinstance(
        transaction,
        dict
    ):

        print(
            "⚠️ Неверный формат transaction"
        )

        return "OK", 200


    print(
        "💳 TRANSACTION:"
    )

    print(transaction)


    # =====================================================
    # ПОЛУЧАЕМ ДАННЫЕ
    # =====================================================

    status = transaction.get(
        "status"
    )


    payment_uuid = (

        transaction.get(
            "uuid"
        )

        or

        transaction.get(
            "id"
        )

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
    # ОБРАБАТЫВАЕМ ТОЛЬКО PAID
    # =====================================================

    if status != "paid":

        print(
            f"⏭ Платёж ещё не оплачен: "
            f"{status}"
        )

        return "OK", 200


    # =====================================================
    # UUID
    # =====================================================

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

        payment = (
            get_payment_by_payment_id(
                payment_uuid
            )
        )

    except Exception as e:

        print(
            "❌ Ошибка поиска платежа:"
        )

        print(
            type(e).__name__,
            str(e)
        )

        return "OK", 200


    if not payment:

        print(
            "❌ Платёж не найден в БД"
        )

        print(
            f"UUID: {payment_uuid}"
        )

        print(
            "⚠️ Проверь payment_id "
            "в таблице payments"
        )

        return "OK", 200


    # =====================================================
    # ДАННЫЕ ИЗ БД
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
    # ПОВТОРНЫЙ WEBHOOK
    # =====================================================

    if old_status == "paid":

        print(
            f"⏭ Платёж {payment_uuid} "
            f"уже обработан"
        )

        return "OK", 200


    # =====================================================
    # ПРОВЕРКА DAYS
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
    # ПРОВЕРКА ВАЛЮТЫ
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
    # =====================================================

    expected_amounts = {

        30: 12900,

        90: 37900,

        180: 65900,

        365: 108900,

    }


    expected_amount = (
        expected_amounts.get(
            days
        )
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


        if (
            received_amount
            != expected_amount
        ):

            print(
                "❌ НЕСОВПАДЕНИЕ СУММЫ!"
            )

            print(
                f"Ожидалось: "
                f"{expected_amount}"
            )

            print(
                f"Получено: "
                f"{received_amount}"
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
            days
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
        # ОБНОВЛЯЕМ GITHUB / HAPP
        # -------------------------------------------------

        update_subscription_file(
            user_id,
            new_date
        )


        print(
            f"☂️ Subscription file "
            f"обновлён: {user_id}"
        )


        # -------------------------------------------------
        # ПОМЕЧАЕМ ПЛАТЁЖ PAID
        # -------------------------------------------------

        update_payment_status(
            payment_db_id,
            "paid"
        )


        print(
            f"✅ Платёж "
            f"{payment_uuid} "
            f"помечен как paid"
        )


        # -------------------------------------------------
        # УВЕДОМЛЕНИЕ ПОЛЬЗОВАТЕЛЮ
        # -------------------------------------------------

        if BOT_LOOP:

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
{make_subscription_link(user_id)}

Спасибо за покупку! ❤️
"""


            asyncio.run_coroutine_threadsafe(

                bot.send_message(
                    user_id,
                    message
                ),

                BOT_LOOP

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
    methods=["POST"]
)
def add_days_api():

    data = request.get_json(
        silent=True
    )


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


    if (
        user_id is None
        or days is None
    ):

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
                "message":
                    "days must be greater than 0"
            }, 400


        new_date = extend_subscription(
            user_id,
            days
        )


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

            "date": new_date,

            "subscription":
                make_subscription_link(
                    user_id
                )

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


# =========================================================
# FLASK
# =========================================================

def run_webhook():

    port = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        threaded=True

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
            e
        )


    # =====================================================
    # СИНХРОНИЗАЦИЯ
    # =====================================================

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
            e
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
        daemon=True
    ).start()


    asyncio.run(
        main()
    )