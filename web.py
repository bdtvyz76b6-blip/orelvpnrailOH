import os
from urllib.parse import quote

from flask import Flask, Response, abort

from database import (
    get_subscription_content,
    get_user,
)


app = Flask(__name__)


# ============================================================
# НАСТРОЙКИ
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()


# ============================================================
# USER ID ИЗ TOKEN
# ============================================================

def get_user_id_from_token(token):

    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None

    user_id = token[len(SUBSCRIPTION_PREFIX):]

    if not user_id.isdigit():
        return None

    return int(user_id)


# ============================================================
# URL
# ============================================================

def get_urls(user_id):

    token = f"{SUBSCRIPTION_PREFIX}{user_id}"

    page_url = (
        f"{PUBLIC_SITE_URL}/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    happ_url = (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    incy_url = (
        "incy://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    return (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    )


# ============================================================
# ИНФОРМАЦИЯ О ПОДПИСКЕ
# ============================================================

def get_subscription_info(user):

    if not user:
        return {
            "tariff": "❌ Нет подписки",
            "status": "🔴 Неактивна",
            "days": 0,
            "date": "—",
            "active": False,
        }

    subscription = user[3]
    subscription_until = user[4]

    # --------------------------------------------------------
    # ТАРИФ
    # --------------------------------------------------------

    if subscription == "vip":
        tariff = "👑 ixxy VIP"

    elif subscription == "trial":
        tariff = "🎁 Пробный период"

    else:
        tariff = "❌ Нет подписки"

    # --------------------------------------------------------
    # ДАТА
    # --------------------------------------------------------

    if not subscription_until:
        return {
            "tariff": tariff,
            "status": "🔴 Неактивна",
            "days": 0,
            "date": "—",
            "active": False,
        }

    try:
        from datetime import datetime

        expire_date = datetime.strptime(
            str(subscription_until),
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        # Дата окончания считается активной
        # до конца указанного дня.
        if expire_date < today:
            return {
                "tariff": tariff,
                "status": "⛔ Истекла",
                "days": 0,
                "date": expire_date.strftime("%d.%m.%Y"),
                "active": False,
            }

        days = (
            expire_date - today
        ).days

        return {
            "tariff": tariff,
            "status": "🟢 Активна",
            "days": days,
            "date": expire_date.strftime("%d.%m.%Y"),
            "active": True,
        }

    except Exception:
        return {
            "tariff": tariff,
            "status": "⚠️ Ошибка даты",
            "days": 0,
            "date": str(subscription_until),
            "active": False,
        }


# ============================================================
# HTML
# ============================================================

def render_page(
    user_id,
    user,
    subscription_url,
    happ_url,
    incy_url,
):

    info = get_subscription_info(user)

    username = (
        user[1]
        if user and user[1]
        else "нет"
    )

    first_name = (
        user[2]
        if user and user[2]
        else "нет"
    )

    status_class = (
        "active"
        if info["active"]
        else "expired"
    )

    if info["active"]:
        status_icon = "🟢"
        status_title = "Подписка активна"
        status_description = (
            "VPN доступен для использования"
        )
    else:
        status_icon = "🔴"
        status_title = "Подписка недоступна"
        status_description = (
            "Продлите подписку для продолжения"
        )

    return f"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0,
             maximum-scale=1.0, user-scalable=no"
>

<meta
    name="theme-color"
    content="#08080d"
>

<title>☂️ ixxy VPN — Моя подписка</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    min-height: 100%;
}}

body {{

    margin: 0;

    min-height: 100vh;

    padding:
        24px
        16px
        40px;

    color: #fff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255, 0, 190, .30),
            transparent 32%
        ),
        radial-gradient(
            circle at 100% 10%,
            rgba(0, 190, 255, .28),
            transparent 32%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(115, 45, 255, .30),
            transparent 42%
        ),
        #07070b;

    overflow-x: hidden;
}}

body::before {{

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    background:
        linear-gradient(
            120deg,
            transparent,
            rgba(255,255,255,.025),
            transparent
        );

}}

.container {{

    position: relative;

    width: 100%;

    max-width: 520px;

    margin: 0 auto;

}}

.header {{

    text-align: center;

    margin-bottom: 24px;

    animation:
        fadeUp .45s ease both;

}}

.logo {{

    width: 82px;
    height: 82px;

    margin:
        0 auto 16px;

    border-radius: 26px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 42px;

    background:
        linear-gradient(
            135deg,
            #ff28ce,
            #743cff 55%,
            #00c9ff
        );

    box-shadow:
        0 18px 60px
        rgba(117,60,255,.42);

}}

h1 {{

    margin: 0;

    font-size: 30px;

    line-height: 1.1;

    font-weight: 850;

    letter-spacing: -.7px;

}}

.subtitle {{

    margin-top: 8px;

    color: #92929e;

    font-size: 14px;

}}

.card {{

    padding: 18px;

    border-radius: 28px;

    background:
        rgba(18,18,27,.86);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 25px 90px
        rgba(0,0,0,.50);

    backdrop-filter:
        blur(25px);

    animation:
        fadeUp .55s ease both;

}}

.status {{

    padding: 18px;

    border-radius: 21px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        rgba(255,255,255,.07);

}}

.status.active {{

    background:
        linear-gradient(
            135deg,
            rgba(0,255,165,.13),
            rgba(0,170,255,.07)
        );

    border-color:
        rgba(0,255,180,.13);

}}

.status.expired {{

    background:
        rgba(255,70,90,.08);

    border-color:
        rgba(255,70,90,.13);

}}

.status-left {{

    display: flex;

    align-items: center;

    gap: 12px;

}}

.dot {{

    width: 12px;
    height: 12px;

    flex-shrink: 0;

    border-radius: 50%;

    background: #ff5267;

    box-shadow:
        0 0 18px
        rgba(255,82,103,.7);

}}

.active .dot {{

    background: #00f59b;

    box-shadow:
        0 0 18px
        rgba(0,245,155,.9);

}}

.status-title {{

    font-size: 15px;

    font-weight: 850;

}}

.status-description {{

    margin-top: 4px;

    color: #858590;

    font-size: 12px;

}}

.status-icon {{

    font-size: 23px;

}}

.info-grid {{

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 10px;

    margin-top: 12px;

}}

.info-box {{

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        rgba(255,255,255,.06);

}}

.info-label {{

    color: #777782;

    font-size: 11px;

    margin-bottom: 6px;

}}

.info-value {{

    font-size: 14px;

    font-weight: 750;

    word-break: break-word;

}}

.full-info {{

    margin-top: 10px;

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        rgba(255,255,255,.06);

}}

.full-row {{

    display: flex;

    justify-content: space-between;

    gap: 15px;

    padding: 7px 0;

}}

.full-row + .full-row {{

    border-top:
        1px solid
        rgba(255,255,255,.05);

}}

.full-label {{

    color: #777782;

    font-size: 12px;

}}

.full-value {{

    text-align: right;

    font-size: 13px;

    font-weight: 700;

}}

.button {{

    width: 100%;

    min-height: 56px;

    margin-top: 11px;

    padding: 0 16px;

    border: 0;

    border-radius: 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 9px;

    color: white;

    text-decoration: none;

    font-size: 15px;

    font-weight: 850;

    cursor: pointer;

    transition:
        transform .15s ease,
        opacity .15s ease;

}}

.button:active {{

    transform: scale(.97);

    opacity: .85;

}}

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff25b8,
            #ff5d78
        );

    box-shadow:
        0 10px 30px
        rgba(255,37,184,.23);

}}

.incy {{

    background:
        linear-gradient(
            135deg,
            #654cff,
            #00baff
        );

    box-shadow:
        0 10px 30px
        rgba(0,186,255,.20);

}}

.copy {{

    background:
        rgba(255,255,255,.075);

    border:
        1px solid
        rgba(255,255,255,.08);

}}

.subscription {{

    margin-top: 17px;

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(0,0,0,.25);

    border:
        1px solid
        rgba(255,255,255,.05);

}}

.subscription-title {{

    margin-bottom: 7px;

    color: #777782;

    font-size: 11px;

}}

.subscription-link {{

    color: #a9a9b5;

    font-size: 11px;

    line-height: 1.55;

    word-break: break-all;

}}

.toast {{

    position: fixed;

    left: 50%;

    bottom: 25px;

    z-index: 999;

    transform:
        translate(-50%, 20px);

    padding:
        12px
        17px;

    border-radius: 15px;

    background:
        rgba(25,25,34,.95);

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 15px 40px
        rgba(0,0,0,.40);

    font-size: 13px;

    opacity: 0;

    pointer-events: none;

    transition:
        .25s ease;

}}

.toast.show {{

    opacity: 1;

    transform:
        translate(-50%, 0);

}}

.footer {{

    margin-top: 20px;

    text-align: center;

    color: #666672;

    font-size: 11px;

}}

@keyframes fadeUp {{

    from {{
        opacity: 0;
        transform: translateY(12px);
    }}

    to {{
        opacity: 1;
        transform: translateY(0);
    }}

}}

</style>

</head>

<body>

<div class="container">

    <div class="header">

        <div class="logo">
            ☂️
        </div>

        <h1>
            Моя подписка
        </h1>

        <div class="subtitle">
            ixxy VPN • Личный кабинет
        </div>

    </div>

    <div class="card">

        <div class="status {status_class}">

            <div class="status-left">

                <div class="dot"></div>

                <div>

                    <div class="status-title">
                        {status_title}
                    </div>

                    <div class="status-description">
                        {status_description}
                    </div>

                </div>

            </div>

            <div class="status-icon">
                {status_icon}
            </div>

        </div>

        <div class="info-grid">

            <div class="info-box">

                <div class="info-label">
                    🎫 ТАРИФ
                </div>

                <div class="info-value">
                    {info["tariff"]}
                </div>

            </div>

            <div class="info-box">

                <div class="info-label">
                    ⏳ ОСТАЛОСЬ
                </div>

                <div class="info-value">
                    {info["days"]} д.
                </div>

            </div>

            <div class="info-box">

                <div class="info-label">
                    📅 ДЕЙСТВУЕТ ДО
                </div>

                <div class="info-value">
                    {info["date"]}
                </div>

            </div>

            <div class="info-box">

                <div class="info-label">
                    🆔 TELEGRAM ID
                </div>

                <div class="info-value">
                    {user_id}
                </div>

            </div>

        </div>

        <div class="full-info">

            <div class="full-row">

                <div class="full-label">
                    👤 Username
                </div>

                <div class="full-value">
                    @{username}
                </div>

            </div>

            <div class="full-row">

                <div class="full-label">
                    🧑‍💻 Имя
                </div>

                <div class="full-value">
                    {first_name}
                </div>

            </div>

        </div>

        <a
            class="button happ"
            href="{happ_url}"
        >
            ⚡ Добавить в Happ
        </a>

        <a
            class="button incy"
            href="{incy_url}"
        >
            🚀 Добавить в INCY
        </a>

        <button
            class="button copy"
            onclick="copyLink()"
        >
            📋 Скопировать ссылку
        </button>

        <div class="subscription">

            <div class="subscription-title">
                🔗 ПЕРСОНАЛЬНАЯ ССЫЛКА
            </div>

            <div class="subscription-link">
                {subscription_url}
            </div>

        </div>

    </div>

    <div class="footer">
        ixxy VPN • Защищённое подключение
    </div>

</div>

<div
    id="toast"
    class="toast"
>
    ✅ Ссылка скопирована
</div>

<script>

const subscriptionLink =
    {subscription_url!r};

async function copyLink() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        showToast(
            "✅ Ссылка скопирована"
        );

    }} catch (error) {{

        const input =
            document.createElement("input");

        input.value =
            subscriptionLink;

        document.body.appendChild(input);

        input.select();

        document.execCommand("copy");

        input.remove();

        showToast(
            "✅ Ссылка скопирована"
        );

    }}

}}

function showToast(text) {{

    const toast =
        document.getElementById("toast");

    toast.textContent = text;

    toast.classList.add("show");

    setTimeout(() => {{

        toast.classList.remove("show");

    }}, 2200);

}}

</script>

</body>

</html>
"""


# ============================================================
# СТРАНИЦА ПОДПИСКИ
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    user = get_user(user_id)

    if not user:
        return (
            """
            <html>
            <body style="
                background:#07070b;
                color:white;
                font-family:Arial;
                text-align:center;
                padding:50px 20px;
            ">
                <h2>⛔ Пользователь не найден</h2>
            </body>
            </html>
            """,
            404,
        )

    content = get_subscription_content(user_id)

    if not content:
        return (
            """
            <html>
            <body style="
                background:#07070b;
                color:white;
                font-family:Arial;
                text-align:center;
                padding:50px 20px;
            ">
                <h2>⛔ Подписка не найдена</h2>
                <p style="color:#888;">
                    Для этого пользователя
                    ещё не создана подписка.
                </p>
            </body>
            </html>
            """,
            404,
        )

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    html = render_page(
        user_id,
        user,
        subscription_url,
        happ_url,
        incy_url,
    )

    return html


# ============================================================
# ЧИСТАЯ ПОДПИСКА
# ============================================================

@app.route("/sub/<token>")
def subscription_content(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    content = get_subscription_content(user_id)

    if not content:

        return Response(
            "#profile-title: ⛔ ixxy VPN\n\n"
            "#announce: Подписка не найдена",
            status=404,
            mimetype="text/plain",
        )

    return Response(
        content,
        status=200,
        mimetype="text/plain",
        headers={
            "Cache-Control":
                "no-cache, no-store, must-revalidate",
            "Pragma":
                "no-cache",
            "Expires":
                "0",
        },
    )


# ============================================================
# ГЛАВНАЯ
# ============================================================

@app.route("/")
def index():

    return (
        "☂️ ixxy VPN web server is running"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return "OK"


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )