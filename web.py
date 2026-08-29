import os
import html
from datetime import datetime
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

# Если позже укажешь username бота:
# BOT_USERNAME=your_bot
BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "",
).strip().lstrip("@")

if BOT_USERNAME:
    TELEGRAM_URL = f"https://t.me/{BOT_USERNAME}"
else:
    TELEGRAM_URL = "https://t.me/"


# ============================================================
# USER ID ИЗ ТОКЕНА
# ============================================================

def get_user_id_from_token(token):

    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None

    user_id = token[len(SUBSCRIPTION_PREFIX):]

    if not user_id.isdigit():
        return None

    return int(user_id)


# ============================================================
# ТОКЕН
# ============================================================

def get_token(user_id):

    return f"{SUBSCRIPTION_PREFIX}{user_id}"


# ============================================================
# URL
# ============================================================

def get_urls(user_id):

    token = get_token(user_id)

    page_url = (
        f"{PUBLIC_SITE_URL}/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    # Добавление подписки в Happ
    happ_url = (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    # Добавление подписки в INCY
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
# БЕЗОПАСНАЯ JS-СТРОКА
# ============================================================

def js_escape(value):

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("</", "<\\/")
    )


# ============================================================
# СКЛОНЕНИЕ ДНЕЙ
# ============================================================

def days_word(days):

    days = abs(int(days))

    if 11 <= days % 100 <= 14:
        return "дней"

    last = days % 10

    if last == 1:
        return "день"

    if 2 <= last <= 4:
        return "дня"

    return "дней"


# ============================================================
# СТРАНИЦА ПОДПИСКИ
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    # --------------------------------------------------------
    # Пользователь
    # --------------------------------------------------------

    user = get_user(user_id)

    # --------------------------------------------------------
    # Контент подписки
    # --------------------------------------------------------

    content = get_subscription_content(user_id)

    if not content:

        return """
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<meta
    name="theme-color"
    content="#08080d"
>

<title>ixxy VPN</title>

<style>

* {
    box-sizing:border-box;
}

body {
    margin:0;
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
    padding:24px;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255,0,190,.22),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 5%,
            rgba(0,190,255,.20),
            transparent 32%
        ),
        #07070b;

    color:#fff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    text-align:center;
}

.box {
    width:100%;
    max-width:430px;
    padding:38px 26px;

    border-radius:30px;

    background:
        rgba(18,18,27,.88);

    border:
        1px solid rgba(255,255,255,.08);

    box-shadow:
        0 25px 80px rgba(0,0,0,.45);
}

.icon {
    width:80px;
    height:80px;

    margin:
        0 auto 20px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:25px;

    font-size:40px;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #773cff,
            #00c9ff
        );

    box-shadow:
        0 18px 45px
        rgba(115,60,255,.30);
}

h1 {
    margin:0 0 10px;
    font-size:28px;
}

p {
    margin:0;
    color:#90909c;
    line-height:1.55;
}

</style>

</head>

<body>

<div class="box">

    <div class="icon">
        ⛔
    </div>

    <h1>
        Подписка не найдена
    </h1>

    <p>
        Для этого пользователя пока нет
        доступной подписки.
    </p>

</div>

</body>

</html>
""", 404

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    # --------------------------------------------------------
    # Данные пользователя
    # --------------------------------------------------------

    username = "нет"
    first_name = "Пользователь"
    subscription = "none"
    until = ""

    if user:

        username = (
            str(user[1])
            if user[1]
            else "нет"
        )

        first_name = (
            str(user[2])
            if user[2]
            else "Пользователь"
        )

        subscription = (
            str(user[3])
            if user[3]
            else "none"
        )

        until = (
            str(user[4])
            if user[4]
            else ""
        )

    username = html.escape(username)
    first_name = html.escape(first_name)

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    status = "🔴 Не активна"
    status_class = "inactive"

    tariff_label = "🎫 Тариф"
    tariff = "Нет подписки"

    days_left = 0
    until_text = "—"

    # --------------------------------------------------------
    # Тариф
    # --------------------------------------------------------

    if subscription == "vip":

        tariff_label = "🎫 Тариф"
        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff_label = "🎁 Пробный период"
        tariff = "Активен"

    elif subscription in (
        "active",
        "premium",
        "standard",
    ):

        tariff_label = "🎫 Тариф"
        tariff = "ixxy VPN"

    # --------------------------------------------------------
    # Дата окончания
    # --------------------------------------------------------

    if until:

        try:

            expire_date = datetime.strptime(
                until,
                "%Y-%m-%d"
            ).date()

            today = datetime.now().date()

            until_text = expire_date.strftime(
                "%d.%m.%Y"
            )

            days_left = (
                expire_date - today
            ).days

            if days_left >= 0:

                status = "🟢 Подписка активна"
                status_class = "active"

            else:

                status = "🔴 Подписка истекла"
                status_class = "inactive"

                days_left = 0

        except Exception:

            pass

    # --------------------------------------------------------
    # Дни
    # --------------------------------------------------------

    days_text = (
        f"{days_left} {days_word(days_left)}"
    )

    # --------------------------------------------------------
    # Безопасные значения
    # --------------------------------------------------------

    safe_subscription_url = html.escape(
        subscription_url
    )

    js_subscription_url = js_escape(
        subscription_url
    )

    js_happ_url = js_escape(
        happ_url
    )

    js_incy_url = js_escape(
        incy_url
    )

    js_page_url = js_escape(
        page_url
    )

    js_telegram_url = js_escape(
        TELEGRAM_URL
    )

    safe_first_name = html.escape(
        first_name
    )

    safe_username = html.escape(
        username
    )

    safe_tariff = html.escape(
        tariff
    )

    safe_until = html.escape(
        until_text
    )

    safe_days = html.escape(
        days_text
    )

    # ========================================================
    # HTML
    # ========================================================

    html_page = f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="
        width=device-width,
        initial-scale=1.0,
        maximum-scale=1.0,
        user-scalable=no
"
>

<meta
    name="theme-color"
    content="#08080d"
>

<meta
    name="mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
>

<title>☂️ ixxy VPN — Моя подписка</title>

<style>

/* ============================================================
   RESET
============================================================ */

* {{

    box-sizing:border-box;

    -webkit-tap-highlight-color:
        transparent;

}}

html {{

    min-height:100%;

    scroll-behavior:smooth;

}}

body {{

    margin:0;

    min-height:100vh;

    padding:
        max(14px, env(safe-area-inset-top))
        15px
        max(28px, env(safe-area-inset-bottom));

    color:var(--text);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    background:

        radial-gradient(
            circle at 0% 0%,
            rgba(255,0,190,.23),
            transparent 31%
        ),

        radial-gradient(
            circle at 100% 4%,
            rgba(0,190,255,.21),
            transparent 31%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(115,50,255,.20),
            transparent 42%
        ),

        var(--bg);

    transition:
        background .3s ease,
        color .3s ease;

    overscroll-behavior-x:none;

}}


/* ============================================================
   VARIABLES
============================================================ */

:root {{

    --bg:#07070b;

    --card:
        rgba(18,18,27,.86);

    --card2:
        rgba(255,255,255,.045);

    --text:#ffffff;

    --muted:#91919d;

    --border:
        rgba(255,255,255,.09);

    --shadow:
        rgba(0,0,0,.48);

    --green:#00f59b;

    --red:#ff4d61;

}}

body.light {{

    --bg:#f3f4f8;

    --card:
        rgba(255,255,255,.88);

    --card2:
        rgba(0,0,0,.045);

    --text:#111118;

    --muted:#696974;

    --border:
        rgba(0,0,0,.08);

    --shadow:
        rgba(0,0,0,.12);

}}


/* ============================================================
   CONTAINER
============================================================ */

.container {{

    width:100%;

    max-width:540px;

    margin:0 auto;

}}


/* ============================================================
   TOPBAR
============================================================ */

.topbar {{

    height:48px;

    display:flex;

    justify-content:flex-end;

    align-items:center;

    margin-bottom:3px;

}}

.theme-toggle {{

    width:46px;

    height:46px;

    border:1px solid var(--border);

    border-radius:15px;

    background:var(--card2);

    color:var(--text);

    font-size:19px;

    display:flex;

    align-items:center;

    justify-content:center;

    cursor:pointer;

    backdrop-filter:blur(18px);

    -webkit-backdrop-filter:blur(18px);

    transition:
        transform .15s ease,
        background .3s ease;

}}

.theme-toggle:active {{

    transform:scale(.91);

}}


/* ============================================================
   HEADER
============================================================ */

.header {{

    text-align:center;

    margin-bottom:22px;

}}

.logo {{

    width:88px;

    height:88px;

    margin:
        2px auto 17px;

    display:flex;

    align-items:center;

    justify-content:center;

    border-radius:28px;

    font-size:43px;

    background:
        linear-gradient(
            135deg,
            #ff24c5,
            #773cff,
            #00c9ff
        );

    box-shadow:
        0 20px 60px
        rgba(115,60,255,.40);

    animation:
        logoFloat 4s ease-in-out infinite;

}}

@keyframes logoFloat {{

    0%,100% {{
        transform:translateY(0);
    }}

    50% {{
        transform:translateY(-4px);
    }}

}}

h1 {{

    margin:0;

    font-size:30px;

    line-height:1.1;

    font-weight:900;

    letter-spacing:-.7px;

}}

.subtitle {{

    margin:
        8px 0 0;

    color:var(--muted);

    font-size:14px;

}}


/* ============================================================
   MAIN CARD
============================================================ */

.card {{

    padding:17px;

    border-radius:30px;

    background:var(--card);

    border:1px solid var(--border);

    box-shadow:
        0 25px 80px var(--shadow);

    backdrop-filter:blur(28px);

    -webkit-backdrop-filter:blur(28px);

    animation:
        cardIn .45s ease;

}}

@keyframes cardIn {{

    from {{
        opacity:0;
        transform:translateY(12px);
    }}

    to {{
        opacity:1;
        transform:translateY(0);
    }}

}}


/* ============================================================
   STATUS
============================================================ */

.status {{

    padding:17px;

    border-radius:22px;

    display:flex;

    align-items:center;

    justify-content:space-between;

    border:1px solid var(--border);

}}

.status.active {{

    background:
        linear-gradient(
            135deg,
            rgba(0,255,165,.13),
            rgba(0,170,255,.06)
        );

}}

.status.inactive {{

    background:
        rgba(255,60,80,.07);

}}

.status-left {{

    display:flex;

    align-items:center;

    gap:12px;

}}

.dot {{

    width:12px;

    height:12px;

    border-radius:50%;

    flex-shrink:0;

}}

.active .dot {{

    background:var(--green);

    box-shadow:
        0 0 18px
        rgba(0,245,155,.9);

}}

.inactive .dot {{

    background:var(--red);

    box-shadow:
        0 0 15px
        rgba(255,77,97,.65);

}}

.status-title {{

    font-size:15px;

    font-weight:900;

}}

.status-info {{

    margin-top:4px;

    color:var(--muted);

    font-size:12px;

}}

.status-icon {{

    font-size:21px;

}}


/* ============================================================
   INFO
============================================================ */

.info-grid {{

    display:grid;

    grid-template-columns:
        1fr 1fr;

    gap:10px;

    margin-top:11px;

}}

.info-box {{

    padding:16px;

    border-radius:20px;

    background:var(--card2);

    border:1px solid var(--border);

}}

.info-label {{

    color:var(--muted);

    font-size:11px;

    margin-bottom:6px;

    font-weight:700;

}}

.info-value {{

    color:var(--text);

    font-size:14px;

    font-weight:850;

    word-break:break-word;

}}

.remaining {{

    margin-top:10px;

}}

.remaining-value {{

    font-size:18px;

}}


/* ============================================================
   TIME VISUAL
============================================================ */

.time-card {{

    margin-top:10px;

    padding:16px;

    border-radius:20px;

    background:
        linear-gradient(
            135deg,
            rgba(120,60,255,.10),
            rgba(0,200,255,.06)
        );

    border:1px solid var(--border);

}}

.time-top {{

    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:12px;

}}

.time-title {{

    font-size:12px;

    color:var(--muted);

}}

.time-days {{

    font-size:13px;

    font-weight:850;

    color:var(--text);

}}

.time-line {{

    margin-top:11px;

    height:8px;

    border-radius:20px;

    overflow:hidden;

    background:
        rgba(255,255,255,.08);

}}

.time-line-inner {{

    width:100%;

    height:100%;

    border-radius:20px;

    background:
        linear-gradient(
            90deg,
            #ff25bd,
            #773cff,
            #00c9ff
        );

    animation:
        progressIn .8s ease;

}}

@keyframes progressIn {{

    from {{
        width:0;
    }}

    to {{
        width:100%;
    }}

}}

body.light .time-line {{

    background:
        rgba(0,0,0,.08);

}}


/* ============================================================
   PROFILE
============================================================ */

.profile {{

    margin-top:10px;

    padding:15px;

    border-radius:20px;

    background:var(--card2);

    border:1px solid var(--border);

}}

.profile-title {{

    margin-bottom:7px;

    font-size:13px;

    font-weight:850;

}}

.profile-row {{

    display:flex;

    justify-content:space-between;

    align-items:flex-start;

    gap:15px;

    padding:7px 0;

}}

.profile-label {{

    color:var(--muted);

    font-size:12px;

}}

.profile-value {{

    color:var(--text);

    font-size:12px;

    font-weight:800;

    text-align:right;

    word-break:break-word;

}}


/* ============================================================
   ID
============================================================ */

.id {{

    margin-top:10px;

    padding:14px 15px;

    border-radius:18px;

    background:var(--card2);

    border:1px solid var(--border);

    color:var(--muted);

    font-size:12px;

}}

.id code {{

    color:var(--text);

    font-weight:850;

}}


/* ============================================================
   SECTION TITLES
============================================================ */

.section-title {{

    margin:
        22px 2px 6px;

    font-size:15px;

    font-weight:900;

}}

.section-subtitle {{

    margin:
        0 2px 11px;

    color:var(--muted);

    font-size:12px;

    line-height:1.5;

}}


/* ============================================================
   BUTTONS
============================================================ */

.button {{

    width:100%;

    min-height:56px;

    margin-top:10px;

    padding:
        0 17px;

    border:0;

    border-radius:18px;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:9px;

    color:white;

    text-decoration:none;

    font-family:inherit;

    font-size:15px;

    font-weight:900;

    cursor:pointer;

    touch-action:manipulation;

    transition:
        transform .12s ease,
        opacity .12s ease,
        filter .12s ease;

}}

.button:active {{

    transform:scale(.97);

    opacity:.86;

}}


/* ============================================================
   HAPP
============================================================ */

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff25b8,
            #ff5d78
        );

    box-shadow:
        0 10px 28px
        rgba(255,37,184,.18);

}}


/* ============================================================
   INCY
============================================================ */

.incy {{

    background:
        linear-gradient(
            135deg,
            #654cff,
            #00baff
        );

    box-shadow:
        0 10px 28px
        rgba(70,100,255,.18);

}}


/* ============================================================
   COPY
============================================================ */

.copy-secondary {{

    background:var(--card2);

    color:var(--text);

    border:1px solid var(--border);

}}


/* ============================================================
   REFRESH
============================================================ */

.refresh {{

    background:transparent;

    color:var(--muted);

    border:1px solid var(--border);

}}


/* ============================================================
   SUBSCRIPTION LINK
============================================================ */

.subscription-box {{

    margin-top:10px;

    padding:14px;

    border-radius:18px;

    background:
        rgba(0,0,0,.18);

    border:1px solid var(--border);

    color:var(--muted);

    font-size:11px;

    line-height:1.55;

    word-break:break-all;

    user-select:text;

    -webkit-user-select:text;

    cursor:pointer;

}}

body.light .subscription-box {{

    background:
        rgba(0,0,0,.035);

}}

.subscription-label {{

    margin:
        20px 2px 8px;

    color:var(--muted);

    font-size:11px;

    font-weight:800;

    letter-spacing:.2px;

}}


/* ============================================================
   INSTRUCTION CARDS
============================================================ */

.devices {{

    display:grid;

    grid-template-columns:
        1fr 1fr;

    gap:10px;

}}

.device {{

    min-height:88px;

    padding:15px;

    border-radius:20px;

    background:var(--card2);

    border:1px solid var(--border);

    cursor:pointer;

    transition:
        transform .12s ease,
        background .2s ease;

}}

.device:active {{

    transform:scale(.97);

}}

.device-icon {{

    font-size:25px;

    margin-bottom:8px;

}}

.device-name {{

    font-size:13px;

    font-weight:850;

}}

.device-hint {{

    margin-top:3px;

    color:var(--muted);

    font-size:10px;

}}


/* ============================================================
   ACTION CARDS
============================================================ */

.action {{

    margin-top:10px;

    padding:17px;

    border-radius:20px;

    background:var(--card2);

    border:1px solid var(--border);

    display:flex;

    align-items:center;

    gap:13px;

    text-decoration:none;

    color:var(--text);

    transition:
        transform .12s ease;

}}

.action:active {{

    transform:scale(.98);

}}

.action-icon {{

    width:44px;

    height:44px;

    border-radius:14px;

    display:flex;

    align-items:center;

    justify-content:center;

    flex-shrink:0;

    background:
        linear-gradient(
            135deg,
            rgba(255,37,189,.25),
            rgba(119,60,255,.25)
        );

    font-size:21px;

}}

.action-content {{

    flex:1;

}}

.action-title {{

    font-size:14px;

    font-weight:850;

}}

.action-description {{

    margin-top:3px;

    color:var(--muted);

    font-size:11px;

    line-height:1.4;

}}

.action-arrow {{

    color:var(--muted);

    font-size:18px;

}}


/* ============================================================
   TELEGRAM
============================================================ */

.telegram {{

    margin-top:10px;

    min-height:52px;

    display:flex;

    align-items:center;

    justify-content:center;

    text-decoration:none;

    color:var(--text);

    font-size:13px;

    font-weight:800;

    border-radius:17px;

    border:1px solid var(--border);

    background:var(--card2);

}}


/* ============================================================
   FOOTER
============================================================ */

.footer {{

    margin-top:18px;

    text-align:center;

    color:var(--muted);

    opacity:.7;

    font-size:11px;

}}


/* ============================================================
   TOAST
============================================================ */

.toast {{

    position:fixed;

    left:50%;

    bottom:
        max(22px, env(safe-area-inset-bottom));

    transform:
        translate(-50%,20px);

    width:max-content;

    max-width:
        calc(100% - 30px);

    padding:
        12px 17px;

    border-radius:15px;

    background:
        rgba(25,25,34,.96);

    border:
        1px solid
        rgba(255,255,255,.1);

    box-shadow:
        0 15px 45px
        rgba(0,0,0,.4);

    color:white;

    font-size:13px;

    font-weight:800;

    opacity:0;

    pointer-events:none;

    transition:
        opacity .2s ease,
        transform .2s ease;

    z-index:9999;

}}

.toast.show {{

    opacity:1;

    transform:
        translate(-50%,0);

}}


/* ============================================================
   MODAL
============================================================ */

.modal {{

    position:fixed;

    inset:0;

    padding:20px;

    display:flex;

    align-items:flex-end;

    justify-content:center;

    background:
        rgba(0,0,0,.55);

    backdrop-filter:blur(8px);

    -webkit-backdrop-filter:blur(8px);

    opacity:0;

    pointer-events:none;

    transition:
        opacity .2s ease;

    z-index:5000;

}}

.modal.show {{

    opacity:1;

    pointer-events:auto;

}}

.modal-box {{

    width:100%;

    max-width:540px;

    max-height:78vh;

    overflow:auto;

    padding:22px;

    border-radius:
        28px 28px 22px 22px;

    background:
        #15151d;

    color:#fff;

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 -15px 60px
        rgba(0,0,0,.35);

    transform:
        translateY(20px);

    transition:
        transform .25s ease;

}}

.modal.show .modal-box {{

    transform:
        translateY(0);

}}

.modal-close {{

    width:40px;

    height:40px;

    margin-left:auto;

    display:flex;

    align-items:center;

    justify-content:center;

    border:0;

    border-radius:13px;

    background:
        rgba(255,255,255,.07);

    color:#fff;

    font-size:18px;

    cursor:pointer;

}}

.modal h2 {{

    margin:
        13px 0 8px;

    font-size:22px;

}}

.modal p {{

    color:#a3a3af;

    font-size:13px;

    line-height:1.6;

}}

.steps {{

    margin-top:16px;

}}

.step {{

    display:flex;

    gap:12px;

    margin-bottom:13px;

}}

.step-number {{

    width:28px;

    height:28px;

    border-radius:10px;

    display:flex;

    align-items:center;

    justify-content:center;

    flex-shrink:0;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #773cff
        );

    font-size:12px;

    font-weight:900;

}}

.step-text {{

    padding-top:4px;

    color:#ddd;

    font-size:13px;

    line-height:1.5;

}}


/* ============================================================
   SMALL SCREENS
============================================================ */

@media (max-width:380px) {{

    body {{
        padding-left:11px;
        padding-right:11px;
    }}

    .card {{
        padding:14px;
    }}

    h1 {{
        font-size:27px;
    }}

}}

</style>

</head>

<body>

<div class="container">

    <!-- =====================================================
         TOP
         ===================================================== -->

    <div class="topbar">

        <button
            class="theme-toggle"
            id="themeButton"
            type="button"
            onclick="toggleTheme()"
            aria-label="Сменить тему"
        >
            🌙
        </button>

    </div>


    <!-- =====================================================
         HEADER
         ===================================================== -->

    <div class="header">

        <div class="logo">
            ☂️
        </div>

        <h1>
            Моя подписка
        </h1>

        <div class="subtitle">
            ixxy VPN • безопасное подключение
        </div>

    </div>


    <div class="card">

        <!-- =================================================
             STATUS
             ================================================= -->

        <div class="status {status_class}">

            <div class="status-left">

                <div class="dot"></div>

                <div>

                    <div class="status-title">
                        {status}
                    </div>

                    <div class="status-info">
                        Персональный доступ ixxy VPN
                    </div>

                </div>

            </div>

            <div class="status-icon">
                🔐
            </div>

        </div>


        <!-- =================================================
             INFO
             ================================================= -->

        <div class="info-grid">

            <div class="info-box">

                <div class="info-label">
                    {tariff_label}
                </div>

                <div class="info-value">
                    {safe_tariff}
                </div>

            </div>


            <div class="info-box">

                <div class="info-label">
                    📅 Активна до
                </div>

                <div class="info-value">
                    {safe_until}
                </div>

            </div>

        </div>


        <div class="info-box remaining">

            <div class="info-label">
                ⏳ Осталось
            </div>

            <div class="info-value remaining-value">
                {safe_days}
            </div>

        </div>


        <!-- =================================================
             TIME
             ================================================= -->

        <div class="time-card">

            <div class="time-top">

                <div class="time-title">
                    ⏱ Состояние подписки
                </div>

                <div class="time-days">
                    {safe_days}
                </div>

            </div>

            <div class="time-line">

                <div class="time-line-inner"></div>

            </div>

        </div>


        <!-- =================================================
             PROFILE
             ================================================= -->

        <div class="profile">

            <div class="profile-title">
                👤 Профиль
            </div>

            <div class="profile-row">

                <div class="profile-label">
                    Пользователь
                </div>

                <div class="profile-value">
                    {safe_first_name}
                </div>

            </div>

            <div class="profile-row">

                <div class="profile-label">
                    @ Username
                </div>

                <div class="profile-value">
                    @{safe_username}
                </div>

            </div>

        </div>


        <!-- =================================================
             ID
             ================================================= -->

        <div class="id">

            🆔 Telegram ID:
            <code>{user_id}</code>

        </div>


        <!-- =================================================
             CONNECTION
             ================================================= -->

        <div class="section-title">
            ⚡ Подключение
        </div>

        <div class="section-subtitle">
            Добавьте свою подписку прямо в приложение.
        </div>


        <!-- =================================================
             HAPP BUTTON
             ================================================= -->

        <button
            type="button"
            class="button happ"
            onclick="openApp('happ')"
        >
            📲 Добавить в Happ
        </button>


        <!-- =================================================
             INCY BUTTON
             ================================================= -->

        <button
            type="button"
            class="button incy"
            onclick="openApp('incy')"
        >
            🚀 Добавить в INCY
        </button>


        <!-- =================================================
             COPY
             ================================================= -->

        <button
            type="button"
            class="button copy-secondary"
            onclick="copyLink()"
        >
            📋 Скопировать ссылку
        </button>


        <!-- =================================================
             REFRESH
             ================================================= -->

        <button
            type="button"
            class="button refresh"
            onclick="refreshPage()"
        >
            🔄 Обновить страницу
        </button>


        <!-- =================================================
             SUBSCRIPTION LINK
             ================================================= -->

        <div class="subscription-label">
            🔗 ССЫЛКА ПОДПИСКИ
        </div>

        <div
            class="subscription-box"
            onclick="copyLink()"
        >
            {safe_subscription_url}
        </div>


        <!-- =================================================
             TELEGRAM
             ================================================= -->

        <a
            class="telegram"
            href="{js_telegram_url}"
        >
            ← Вернуться в Telegram
        </a>

    </div>


    <div class="footer">
        ☂️ ixxy VPN • Ваш персональный VPN
    </div>

</div>


<!-- =========================================================
     TOAST
========================================================= -->

<div
    id="toast"
    class="toast"
></div>


<script>

/* ============================================================
   URL
============================================================ */

const subscriptionLink =
    '{js_subscription_url}';

const happUrl =
    '{js_happ_url}';

const incyUrl =
    '{js_incy_url}';

const pageUrl =
    '{js_page_url}';


/* ============================================================
   THEME
============================================================ */

function applyTheme(theme) {{

    if (theme === "light") {{

        document.body.classList.add("light");

        document
            .getElementById("themeButton")
            .textContent = "☀️";

    }} else {{

        document.body.classList.remove("light");

        document
            .getElementById("themeButton")
            .textContent = "🌙";

    }}

}}


function toggleTheme() {{

    const current =
        localStorage.getItem("ixxy_theme")
        || "dark";

    const next =
        current === "dark"
            ? "light"
            : "dark";

    localStorage.setItem(
        "ixxy_theme",
        next
    );

    applyTheme(next);

}}


applyTheme(
    localStorage.getItem("ixxy_theme")
    || "dark"
);


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;

function showToast(text) {{

    const toast =
        document.getElementById("toast");

    toast.textContent = text;

    toast.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {{

        toast.classList.remove("show");

    }}, 2200);

}}


/* ============================================================
   OPEN APP
============================================================ */

function openApp(app) {{

    const url =
        app === "happ"
            ? happUrl
            : incyUrl;

    showToast(
        app === "happ"
            ? "📲 Открываем Happ..."
            : "🚀 Открываем INCY..."
    );

    try {{

        window.location.href = url;

    }} catch (e) {{

        console.log(e);

    }}

    setTimeout(() => {{

        try {{

            const iframe =
                document.createElement("iframe");

            iframe.style.display = "none";

            iframe.src = url;

            document.body.appendChild(
                iframe
            );

            setTimeout(() => {{

                try {{

                    iframe.remove();

                }} catch (e) {{}}

            }}, 1200);

        }} catch (e) {{

            console.log(e);

        }}

    }}, 100);

    setTimeout(() => {{

        if (!document.hidden) {{

            showToast(
                "⚠️ Приложение не открылось. Скопируйте ссылку."
            );

        }}

    }}, 1600);

}}


/* ============================================================
   COPY
============================================================ */

async function copyLink() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        showToast(
            "✅ Ссылка скопирована!"
        );

        return;

    }} catch (e) {{

        console.log(e);

    }}

    try {{

        const textarea =
            document.createElement("textarea");

        textarea.value =
            subscriptionLink;

        textarea.style.position =
            "fixed";

        textarea.style.left =
            "-9999px";

        textarea.style.top =
            "0";

        document.body.appendChild(
            textarea
        );

        textarea.focus();

        textarea.select();

        const success =
            document.execCommand("copy");

        textarea.remove();

        if (success) {{

            showToast(
                "✅ Ссылка скопирована!"
            );

        }} else {{

            throw new Error(
                "Copy failed"
            );

        }}

    }} catch (e) {{

        prompt(
            "Скопируйте ссылку:",
            subscriptionLink
        );

    }}

}}


/* ============================================================
   REFRESH
============================================================ */

function refreshPage() {{

    showToast(
        "🔄 Обновляем..."
    );

    setTimeout(() => {{

        window.location.href =
            pageUrl
            + "?t="
            + Date.now();

    }}, 300);

}}

</script>

</body>

</html>
"""

    return Response(
        html_page,
        status=200,
        mimetype="text/html",
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
# ЧИСТАЯ ПОДПИСКА
# ============================================================

@app.route("/sub/<token>")
def subscription_content(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    content = get_subscription_content(
        user_id
    )

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

    return """
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<meta
    name="theme-color"
    content="#08080d"
>

<title>☂️ ixxy VPN</title>

<style>

* {
    box-sizing:border-box;
}

body {
    margin:0;
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
    padding:25px;

    background:
        radial-gradient(
            circle at 20% 0%,
            rgba(255,0,190,.22),
            transparent 35%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(0,190,255,.22),
            transparent 35%
        ),
        #07070b;

    color:white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    text-align:center;
}

.box {
    width:100%;
    max-width:430px;
    padding:38px 25px;

    border-radius:30px;

    background:
        rgba(18,18,27,.88);

    border:
        1px solid rgba(255,255,255,.08);

    box-shadow:
        0 25px 80px rgba(0,0,0,.45);
}

.logo {
    width:80px;
    height:80px;

    margin:
        0 auto 18px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:25px;

    font-size:42px;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #773cff,
            #00c9ff
        );
}

h1 {
    margin:0;
    font-size:30px;
}

p {
    margin:10px 0 0;
    color:#92929e;
}

</style>

</head>

<body>

<div class="box">

    <div class="logo">
        ☂️
    </div>

    <h1>
        ixxy VPN
    </h1>

    <p>
        Web server is running
    </p>

</div>

</body>

</html>
"""


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
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )