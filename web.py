import os
import html
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, abort

from database import (
    get_user,
    get_subscription_content,
)


# ============================================================
# IXXY VPN — WEB
# ============================================================

app = Flask(__name__)

APP_VERSION = "ixxy-2026.09.01-premium"

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy"
)

TELEGRAM_URL = os.getenv(
    "TELEGRAM_URL",
    "https://t.me/orelvpntopbot"
).strip()

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# HELPERS
# ============================================================

def parse_token(token: str):
    """
    Ожидается:
        2ix847xy123456789
    """

    if not token:
        return None

    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None

    raw_user_id = token[len(SUBSCRIPTION_PREFIX):]

    if not raw_user_id.isdigit():
        return None

    try:
        return int(raw_user_id)
    except Exception:
        return None


def build_subscription_url(token: str):
    return f"{PUBLIC_SITE_URL}/sub/{quote(token, safe='')}"


def build_happ_url(token: str):
    """
    Основная кнопка Happ.

    Crypt5 здесь специально не генерируем.
    Используем обычный happ://add/ URL.
    """

    subscription_url = build_subscription_url(token)

    return "happ://add/" + quote(
        subscription_url,
        safe=""
    )


def build_incy_url(token: str):
    subscription_url = build_subscription_url(token)

    return "incy://add/" + quote(
        subscription_url,
        safe=""
    )


def safe_text(value, default="—"):
    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return html.escape(value)


def format_date(value):
    if not value:
        return "—"

    try:
        if isinstance(value, datetime):
            dt = value
        else:
            text = str(value).strip()

            try:
                dt = datetime.fromisoformat(
                    text.replace("Z", "+00:00")
                )
            except Exception:
                return safe_text(text)

        return dt.strftime("%d.%m.%Y")
    except Exception:
        return safe_text(value)


def get_days_left(subscription_until):
    if not subscription_until:
        return 0

    try:
        if isinstance(subscription_until, datetime):
            dt = subscription_until
        else:
            text = str(subscription_until).strip()

            dt = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()

        seconds = (dt - now).total_seconds()

        if seconds <= 0:
            return 0

        return max(1, int(seconds / 86400))
    except Exception:
        return 0


def is_subscription_active(subscription_until):
    if not subscription_until:
        return False

    try:
        if isinstance(subscription_until, datetime):
            dt = subscription_until
        else:
            dt = datetime.fromisoformat(
                str(subscription_until).replace("Z", "+00:00")
            )

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()

        return dt > now

    except Exception:
        return False


# ============================================================
# PREMIUM HTML
# ============================================================

def render_page(
    token,
    user_id,
    first_name,
    subscription,
    subscription_until,
    subscription_link,
):

    active = is_subscription_active(subscription_until)
    days_left = get_days_left(subscription_until)

    name = safe_text(first_name, "Пользователь")
    tariff = safe_text(subscription, "ixxy VPN")

    expiry = format_date(subscription_until)

    if active:
        status_text = "VPN АКТИВЕН"
        status_class = "active"
    else:
        status_text = "ПОДПИСКА НЕАКТИВНА"
        status_class = "inactive"

    happ_url = build_happ_url(token)
    incy_url = build_incy_url(token)

    # ВАЖНО:
    # subscription_link намеренно НЕ показывается,
    # если это может раскрыть серверные настройки.
    #
    # Вместо него показываем безопасную ссылку /sub/<token>.
    safe_subscription_url = build_subscription_url(token)

    if active:
        days_text = (
            f"{days_left} дн."
            if days_left != 1
            else "1 день"
        )
    else:
        days_text = "Завершена"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0, viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#050507"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
>

<meta
    name="apple-mobile-web-app-title"
    content="ixxy VPN"
>

<title>ixxy VPN</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    background: #050507;
}}

body {{
    margin: 0;
    min-height: 100vh;

    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(255,255,255,.09),
            transparent 34%
        ),
        radial-gradient(
            circle at 100% 30%,
            rgba(255,255,255,.035),
            transparent 30%
        ),
        #050507;

    color: #fff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        Arial,
        sans-serif;

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
            transparent 0%,
            rgba(255,255,255,.025) 50%,
            transparent 100%
        );

    opacity: .7;
}}

.container {{
    width: 100%;
    max-width: 560px;

    margin: 0 auto;

    padding:
        calc(24px + env(safe-area-inset-top))
        18px
        calc(30px + env(safe-area-inset-bottom));
}}

.header {{
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 28px;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 11px;
}}

.logo {{
    width: 44px;
    height: 44px;

    border-radius: 14px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 22px;
    font-weight: 900;

    background:
        linear-gradient(
            145deg,
            #ffffff,
            #a7a7a7
        );

    color: #08080a;

    box-shadow:
        0 10px 30px rgba(255,255,255,.12);
}}

.brand-text {{
    font-size: 19px;
    font-weight: 800;
    letter-spacing: -.4px;
}}

.brand-sub {{
    margin-top: 2px;

    font-size: 11px;

    color: rgba(255,255,255,.42);

    letter-spacing: .5px;
}}

.status {{
    display: flex;
    align-items: center;
    gap: 7px;

    padding: 9px 12px;

    border-radius: 999px;

    font-size: 10px;
    font-weight: 800;

    letter-spacing: .5px;

    border: 1px solid rgba(255,255,255,.07);

    background: rgba(255,255,255,.035);

    color: rgba(255,255,255,.55);
}}

.status.active {{
    color: #fff;
}}

.status-dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: #777;

    box-shadow: 0 0 10px rgba(255,255,255,.25);
}}

.active .status-dot {{
    background: #fff;

    box-shadow:
        0 0 10px rgba(255,255,255,.8);
}}

.hero {{
    position: relative;

    padding: 30px 22px 24px;

    border-radius: 30px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );

    border: 1px solid rgba(255,255,255,.08);

    box-shadow:
        0 30px 80px rgba(0,0,0,.45),
        inset 0 1px 0 rgba(255,255,255,.04);

    overflow: hidden;
}}

.hero::before {{
    content: "";

    position: absolute;

    width: 220px;
    height: 220px;

    top: -130px;
    left: 50%;

    transform: translateX(-50%);

    background: rgba(255,255,255,.08);

    filter: blur(70px);

    pointer-events: none;
}}

.hero-content {{
    position: relative;
    z-index: 2;

    text-align: center;
}}

.eyebrow {{
    color: rgba(255,255,255,.4);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 1.6px;

    text-transform: uppercase;

    margin-bottom: 12px;
}}

.user-name {{
    font-size: 28px;

    font-weight: 850;

    letter-spacing: -1px;

    margin-bottom: 7px;

    word-break: break-word;
}}

.user-description {{
    color: rgba(255,255,255,.43);

    font-size: 13px;

    margin-bottom: 25px;
}}

.connect {{
    display: flex;

    align-items: center;
    justify-content: center;

    width: 100%;

    min-height: 60px;

    border-radius: 18px;

    text-decoration: none;

    color: #050507;

    background: #fff;

    font-size: 16px;

    font-weight: 850;

    letter-spacing: -.2px;

    box-shadow:
        0 15px 40px rgba(255,255,255,.12);

    transition:
        transform .15s ease,
        box-shadow .15s ease;
}}

.connect:active {{
    transform: scale(.975);

    box-shadow:
        0 8px 20px rgba(255,255,255,.08);
}}

.connect-icon {{
    margin-right: 9px;

    font-size: 18px;
}}

.cards {{
    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 11px;

    margin-top: 12px;
}}

.card {{
    padding: 18px;

    border-radius: 21px;

    background:
        rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.065);

    min-width: 0;
}}

.card-label {{
    color: rgba(255,255,255,.35);

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 1px;

    font-weight: 800;

    margin-bottom: 8px;
}}

.card-value {{
    font-size: 15px;

    font-weight: 750;

    color: rgba(255,255,255,.9);

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}}

.progress-card {{
    margin-top: 12px;

    padding: 19px;

    border-radius: 21px;

    background:
        rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.065);
}}

.progress-top {{
    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 11px;
}}

.progress-title {{
    font-size: 12px;

    color: rgba(255,255,255,.55);

    font-weight: 700;
}}

.progress-value {{
    font-size: 12px;

    color: rgba(255,255,255,.8);

    font-weight: 800;
}}

.progress {{
    width: 100%;

    height: 6px;

    border-radius: 999px;

    overflow: hidden;

    background: rgba(255,255,255,.08);
}}

.progress-bar {{
    width: {min(100, max(3, days_left))}%;

    height: 100%;

    border-radius: inherit;

    background: #fff;

    box-shadow:
        0 0 14px rgba(255,255,255,.4);
}}

.section {{
    margin-top: 25px;
}}

.section-title {{
    margin: 0 0 11px 4px;

    font-size: 13px;

    font-weight: 800;

    color: rgba(255,255,255,.7);
}}

.app-card {{
    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 12px;

    padding: 17px;

    margin-bottom: 9px;

    border-radius: 20px;

    color: #fff;

    text-decoration: none;

    background:
        rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.065);

    transition: background .15s ease;
}}

.app-card:active {{
    background:
        rgba(255,255,255,.07);
}}

.app-left {{
    display: flex;

    align-items: center;

    gap: 13px;

    min-width: 0;
}}

.app-icon {{
    width: 43px;
    height: 43px;

    flex: 0 0 43px;

    border-radius: 13px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        rgba(255,255,255,.07);

    border: 1px solid rgba(255,255,255,.06);

    font-size: 20px;
}}

.app-name {{
    font-size: 14px;

    font-weight: 800;

    margin-bottom: 3px;
}}

.app-description {{
    font-size: 11px;

    color: rgba(255,255,255,.36);
}}

.arrow {{
    color: rgba(255,255,255,.35);

    font-size: 20px;
}}

.subscription-box {{
    padding: 17px;

    border-radius: 20px;

    background:
        rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.065);
}}

.subscription-label {{
    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 1px;

    color: rgba(255,255,255,.35);

    margin-bottom: 10px;
}}

.subscription-row {{
    display: flex;

    align-items: center;

    gap: 9px;
}}

.subscription-url {{
    flex: 1;

    min-width: 0;

    padding: 12px 13px;

    border-radius: 13px;

    background:
        rgba(0,0,0,.22);

    border: 1px solid rgba(255,255,255,.05);

    color: rgba(255,255,255,.5);

    font-family: monospace;

    font-size: 10px;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}}

.copy {{
    border: 0;

    padding: 12px 14px;

    border-radius: 13px;

    background: #fff;

    color: #050507;

    font-size: 11px;

    font-weight: 850;

    cursor: pointer;
}}

.info {{
    margin-top: 25px;

    padding: 18px;

    border-radius: 21px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.045),
            rgba(255,255,255,.02)
        );

    border: 1px solid rgba(255,255,255,.06);
}}

.info-title {{
    font-size: 13px;

    font-weight: 800;

    margin-bottom: 13px;
}}

.step {{
    display: flex;

    gap: 11px;

    margin-top: 11px;

    color: rgba(255,255,255,.5);

    font-size: 12px;

    line-height: 1.45;
}}

.step-number {{
    width: 23px;
    height: 23px;

    flex: 0 0 23px;

    border-radius: 8px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        rgba(255,255,255,.07);

    color: rgba(255,255,255,.8);

    font-size: 10px;

    font-weight: 850;
}}

.support {{
    display: flex;

    align-items: center;

    justify-content: center;

    min-height: 52px;

    margin-top: 12px;

    border-radius: 17px;

    text-decoration: none;

    background:
        rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.065);

    color: rgba(255,255,255,.72);

    font-size: 13px;

    font-weight: 750;
}}

.security {{
    margin-top: 14px;

    text-align: center;

    color: rgba(255,255,255,.28);

    font-size: 10px;

    line-height: 1.5;
}}

.footer {{
    text-align: center;

    margin-top: 27px;

    color: rgba(255,255,255,.2);

    font-size: 10px;

    letter-spacing: .3px;
}}

@media (max-width: 380px) {{

    .container {{
        padding-left: 13px;
        padding-right: 13px;
    }}

    .hero {{
        padding-left: 17px;
        padding-right: 17px;
    }}

    .user-name {{
        font-size: 25px;
    }}

    .cards {{
        gap: 8px;
    }}

    .card {{
        padding: 15px;
    }}
}}

</style>
</head>

<body>

<div class="container">

    <header class="header">

        <div class="brand">

            <div class="logo">
                ⚡
            </div>

            <div>
                <div class="brand-text">
                    ixxy VPN
                </div>

                <div class="brand-sub">
                    PRIVATE NETWORK
                </div>
            </div>

        </div>

        <div class="status {status_class}">

            <span class="status-dot"></span>

            {status_text}

        </div>

    </header>


    <section class="hero">

        <div class="hero-content">

            <div class="eyebrow">
                Личный кабинет
            </div>

            <div class="user-name">
                {name}
            </div>

            <div class="user-description">
                Ваше защищённое подключение
            </div>

            <a
                class="connect"
                href="{happ_url}"
            >
                <span class="connect-icon">⚡</span>
                Подключить в Happ
            </a>

        </div>

    </section>


    <div class="cards">

        <div class="card">

            <div class="card-label">
                Тариф
            </div>

            <div class="card-value">
                {tariff}
            </div>

        </div>


        <div class="card">

            <div class="card-label">
                Осталось
            </div>

            <div class="card-value">
                {days_text}
            </div>

        </div>


        <div class="card">

            <div class="card-label">
                До
            </div>

            <div class="card-value">
                {expiry}
            </div>

        </div>


        <div class="card">

            <div class="card-label">
                Статус
            </div>

            <div class="card-value">
                {"Активен" if active else "Неактивен"}
            </div>

        </div>

    </div>


    <div class="progress-card">

        <div class="progress-top">

            <div class="progress-title">
                Состояние подписки
            </div>

            <div class="progress-value">
                {"ACTIVE" if active else "EXPIRED"}
            </div>

        </div>

        <div class="progress">

            <div class="progress-bar"></div>

        </div>

    </div>


    <section class="section">

        <div class="section-title">
            Приложения
        </div>


        <a
            class="app-card"
            href="{happ_url}"
        >

            <div class="app-left">

                <div class="app-icon">
                    ⚡
                </div>

                <div>

                    <div class="app-name">
                        Happ
                    </div>

                    <div class="app-description">
                        Быстрое подключение
                    </div>

                </div>

            </div>

            <div class="arrow">
                ›
            </div>

        </a>


        <a
            class="app-card"
            href="{incy_url}"
        >

            <div class="app-left">

                <div class="app-icon">
                    ◉
                </div>

                <div>

                    <div class="app-name">
                        INCY
                    </div>

                    <div class="app-description">
                        Альтернативный клиент
                    </div>

                </div>

            </div>

            <div class="arrow">
                ›
            </div>

        </a>

    </section>


    <section class="section">

        <div class="section-title">
            Ваша подписка
        </div>

        <div class="subscription-box">

            <div class="subscription-label">
                Персональная ссылка
            </div>

            <div class="subscription-row">

                <div
                    class="subscription-url"
                    id="subscriptionUrl"
                >
                    {html.escape(safe_subscription_url)}
                </div>

                <button
                    class="copy"
                    onclick="copySubscription()"
                >
                    КОПИРОВАТЬ
                </button>

            </div>

        </div>

    </section>


    <section class="info">

        <div class="info-title">
            Как подключиться
        </div>


        <div class="step">

            <div class="step-number">
                1
            </div>

            <div>
                Нажмите «Подключить в Happ».
            </div>

        </div>


        <div class="step">

            <div class="step-number">
                2
            </div>

            <div>
                Подтвердите добавление подписки в приложении.
            </div>

        </div>


        <div class="step">

            <div class="step-number">
                3
            </div>

            <div>
                Включите VPN одной кнопкой.
            </div>

        </div>


        <div class="step">

            <div class="step-number">
                4
            </div>

            <div>
                Готово — подключение работает автоматически.
            </div>

        </div>

    </section>


    <a
        class="support"
        href="{html.escape(TELEGRAM_URL)}"
        target="_blank"
        rel="noopener noreferrer"
    >
        💬 Поддержка ixxy VPN
    </a>


    <div class="security">
        🔒 Конфигурация серверов не отображается
        в личном кабинете.
        Управление подключением выполняется автоматически.
    </div>


    <div class="footer">
        ixxy VPN · ID {user_id} · {APP_VERSION}
    </div>

</div>


<script>

const SUB_URL = {safe_subscription_url!r};


async function copySubscription() {{

    try {{

        await navigator.clipboard.writeText(SUB_URL);

        const button =
            document.querySelector(".copy");

        if (!button) {{
            return;
        }}

        const oldText = button.innerText;

        button.innerText = "СКОПИРОВАНО";

        setTimeout(() => {{
            button.innerText = oldText;
        }}, 1600);

    }} catch (error) {{

        const input =
            document.createElement("textarea");

        input.value = SUB_URL;

        document.body.appendChild(input);

        input.select();

        document.execCommand("copy");

        input.remove();

        const button =
            document.querySelector(".copy");

        if (button) {{

            const oldText = button.innerText;

            button.innerText = "СКОПИРОВАНО";

            setTimeout(() => {{
                button.innerText = oldText;
            }}, 1600);

        }}

    }}

}}

</script>

</body>
</html>
"""


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():

    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width,initial-scale=1"
        >
        <meta name="theme-color" content="#050507">
        <title>ixxy VPN</title>

        <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;

            display: flex;
            align-items: center;
            justify-content: center;

            background: #050507;

            color: white;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                Arial,
                sans-serif;

            text-align: center;
        }

        .box {
            padding: 35px;
        }

        .logo {
            font-size: 54px;
            margin-bottom: 15px;
        }

        h1 {
            margin: 0 0 8px;
            font-size: 30px;
        }

        p {
            color: rgba(255,255,255,.4);
            font-size: 13px;
        }

        </style>
    </head>

    <body>

        <div class="box">

            <div class="logo">
                ⚡
            </div>

            <h1>
                ixxy VPN
            </h1>

            <p>
                Private network
            </p>

        </div>

    </body>
    </html>
    """


@app.route("/health")
def health():

    response = Response(
        '{"service":"ixxy VPN","status":"ok"}',
        mimetype="application/json"
    )

    response.headers.update(NO_CACHE_HEADERS)

    return response


# ============================================================
# PERSONAL CABINET
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = parse_token(token)

    if user_id is None:
        abort(404)

    try:
        user = get_user(user_id)
    except Exception as e:
        return Response(
            f"Database error: {html.escape(str(e))}",
            status=500,
            mimetype="text/plain"
        )

    if not user:
        abort(404)

    # database.py mapping:
    #
    # 0 user_id
    # 1 username
    # 2 first_name
    # 3 subscription
    # 4 subscription_until
    # 5 subscription_link
    # 6 uuid
    # 7 trial_used
    # 8 pending_days
    # 9 notify
    # 10 accepted_terms
    # 11 created_at

    user_id_db = user[0]
    first_name = user[2] or user[1] or "Пользователь"
    subscription = user[3] or "ixxy VPN"
    subscription_until = user[4] or ""
    subscription_link = user[5] or ""

    page = render_page(
        token=token,
        user_id=user_id_db,
        first_name=first_name,
        subscription=subscription,
        subscription_until=subscription_until,
        subscription_link=subscription_link,
    )

    response = Response(
        page,
        mimetype="text/html"
    )

    response.headers.update(NO_CACHE_HEADERS)

    return response


# ============================================================
# SUBSCRIPTION ENDPOINT
# ============================================================

@app.route("/sub/<token>")
def subscription(token):

    user_id = parse_token(token)

    if user_id is None:
        abort(404)

    try:
        content = get_subscription_content(user_id)
    except Exception:
        content = ""

    if not content:
        abort(404)

    response = Response(
        content,
        mimetype="text/plain"
    )

    response.headers.update(NO_CACHE_HEADERS)

    return response


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return Response(
        "Not Found",
        status=404,
        mimetype="text/plain"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )