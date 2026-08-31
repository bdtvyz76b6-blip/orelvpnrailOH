import os
import html
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, abort

from database import (
    get_subscription_content,
    get_user,
)


# ============================================================
# IXXY VPN — PREMIUM WEB
# ============================================================

app = Flask(__name__)


# ============================================================
# CONFIG
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()

TELEGRAM_URL = "https://t.me/orelvpntopbot"


# ============================================================
# TOKEN
# ============================================================

def get_user_id_from_token(token):

    if not token:
        return None

    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None

    user_id = token[len(SUBSCRIPTION_PREFIX):]

    if not user_id.isdigit():
        return None

    try:
        return int(user_id)
    except Exception:
        return None


def get_token(user_id):

    return f"{SUBSCRIPTION_PREFIX}{user_id}"


# ============================================================
# URLS
# ============================================================

def get_urls(user_id):

    token = get_token(user_id)

    page_url = (
        f"{PUBLIC_SITE_URL}/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    # Deep links используются ТОЛЬКО JavaScript-ом.
    # В Telegram InlineKeyboard их использовать нельзя.

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
# DATE
# ============================================================

def parse_subscription_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y",
    )

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            ).date()

        except Exception:
            pass

    return None


# ============================================================
# DAYS
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
# SAFE JS
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
# NO SUBSCRIPTION
# ============================================================

def no_subscription_page():

    return """
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
/>

<meta
    name="theme-color"
    content="#070709"
/>

<title>ixxy VPN</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    min-height: 100%;
}

body {

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;

    background: #070709;

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

}

body::before {

    content: "";

    position: fixed;

    width: 380px;

    height: 380px;

    left: -160px;

    top: -160px;

    background:
        radial-gradient(
            circle,
            rgba(123,70,255,.35),
            transparent 68%
        );

    pointer-events: none;

}

body::after {

    content: "";

    position: fixed;

    width: 360px;

    height: 360px;

    right: -150px;

    bottom: -150px;

    background:
        radial-gradient(
            circle,
            rgba(255,25,170,.25),
            transparent 68%
        );

    pointer-events: none;

}

.box {

    width: 100%;

    max-width: 430px;

    padding: 38px 25px;

    text-align: center;

    border-radius: 32px;

    background:
        rgba(20,20,25,.84);

    border:
        1px solid rgba(255,255,255,.08);

    box-shadow:
        0 30px 100px rgba(0,0,0,.55);

    backdrop-filter: blur(30px);

    -webkit-backdrop-filter: blur(30px);

}

.logo {

    width: 82px;

    height: 82px;

    margin: 0 auto 22px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 25px;

    font-size: 42px;

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 20px 60px rgba(117,60,255,.38);

}

h1 {

    margin: 0;

    font-size: 29px;

    font-weight: 900;

}

p {

    margin: 10px 0 0;

    color: #909098;

    line-height: 1.55;

}

.button {

    display: flex;

    align-items: center;

    justify-content: center;

    min-height: 55px;

    margin-top: 24px;

    border-radius: 17px;

    text-decoration: none;

    color: white;

    font-weight: 900;

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff
        );

}

</style>

</head>

<body>

<div class="box">

    <div class="logo">
        ☂️
    </div>

    <h1>
        Подписка не найдена
    </h1>

    <p>
        У этого пользователя пока нет
        активной персональной подписки.
    </p>

    <a
        class="button"
        href="https://t.me/orelvpntopbot"
    >
        Открыть Telegram-бота
    </a>

</div>

</body>

</html>
"""


# ============================================================
# SUBSCRIPTION PAGE
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ get_user error {user_id}: {e}"
        )
        user = None

    try:
        content = get_subscription_content(user_id)
    except Exception as e:
        print(
            f"❌ subscription content error "
            f"{user_id}: {e}"
        )
        content = ""

    if not content:

        return Response(
            no_subscription_page(),
            status=404,
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

    # ========================================================
    # USER
    # ========================================================

    username = "нет"

    first_name = "Пользователь"

    subscription = "none"

    until = ""

    if user:

        try:
            username = (
                str(user[1])
                if user[1]
                else "нет"
            )
        except Exception:
            username = "нет"

        try:
            first_name = (
                str(user[2])
                if user[2]
                else "Пользователь"
            )
        except Exception:
            first_name = "Пользователь"

        try:
            subscription = (
                str(user[3])
                if user[3]
                else "none"
            )
        except Exception:
            subscription = "none"

        try:
            until = (
                str(user[4])
                if user[4]
                else ""
            )
        except Exception:
            until = ""

    # ========================================================
    # STATUS
    # ========================================================

    status_text = "Подписка неактивна"

    status_class = "inactive"

    status_icon = "×"

    tariff = "Нет подписки"

    until_text = "—"

    days_left = 0

    expire_date = parse_subscription_date(
        until
    )

    if expire_date:

        today = datetime.now().date()

        until_text = expire_date.strftime(
            "%d.%m.%Y"
        )

        days_left = (
            expire_date - today
        ).days

        if days_left >= 0:

            status_text = "Подписка активна"

            status_class = "active"

            status_icon = "✓"

        else:

            status_text = "Подписка истекла"

            status_class = "inactive"

            status_icon = "×"

            days_left = 0

    # ========================================================
    # TARIFF
    # ========================================================

    if subscription == "vip":

        tariff = "ixxy VIP"

    elif subscription == "trial":

        tariff = "Пробный период"

    elif subscription in (
        "active",
        "premium",
        "standard",
    ):

        tariff = "ixxy VPN"

    elif subscription not in (
        "",
        "none",
    ):

        tariff = subscription

    # ========================================================
    # DAYS
    # ========================================================

    days_text = (
        f"{days_left} "
        f"{days_word(days_left)}"
    )

    # ========================================================
    # URLS
    # ========================================================

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    # ========================================================
    # HTML ESCAPE
    # ========================================================

    safe_username = html.escape(
        username
    )

    safe_first_name = html.escape(
        first_name
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

    safe_subscription_url = html.escape(
        subscription_url
    )

    # ========================================================
    # JS
    # ========================================================

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

    # ========================================================
    # PROGRESS
    # ========================================================

    # Просто визуальный индикатор.
    # Не меняет работу подписки.

    if days_left >= 30:
        progress = 100
    elif days_left > 0:
        progress = max(
            8,
            min(
                100,
                int(days_left / 30 * 100)
            )
        )
    else:
        progress = 0

    # ========================================================
    # HTML
    # ========================================================

    page = f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="
        width=device-width,
        initial-scale=1,
        maximum-scale=1,
        user-scalable=no
    "
/>

<meta
    name="theme-color"
    content="#070709"
/>

<meta
    name="mobile-web-app-capable"
    content="yes"
/>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
/>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
/>

<title>ixxy VPN — Подписка</title>

<style>

/* ============================================================
   RESET
============================================================ */

* {{

    box-sizing: border-box;

    -webkit-tap-highlight-color:
        transparent;

}}

html {{

    min-height: 100%;

    scroll-behavior: smooth;

}}

body {{

    margin: 0;

    min-height: 100vh;

    padding:
        max(14px, env(safe-area-inset-top))
        14px
        max(25px, env(safe-area-inset-bottom));

    color: var(--text);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    background: var(--bg);

    transition:
        background .3s ease,
        color .3s ease;

}}

:root {{

    --bg: #070709;

    --card: rgba(18,18,23,.88);

    --card-soft:
        rgba(255,255,255,.045);

    --border:
        rgba(255,255,255,.085);

    --text: #ffffff;

    --muted: #909099;

    --green: #00ed9b;

    --red: #ff5265;

}}

body.light {{

    --bg: #f2f3f7;

    --card: rgba(255,255,255,.91);

    --card-soft:
        rgba(0,0,0,.045);

    --border:
        rgba(0,0,0,.08);

    --text: #111116;

    --muted: #707078;

}}

/* ============================================================
   BACKGROUND
============================================================ */

.background-orb {{

    position: fixed;

    width: 360px;

    height: 360px;

    border-radius: 50%;

    filter: blur(75px);

    opacity: .23;

    pointer-events: none;

    z-index: -1;

}}

.orb-one {{

    left: -210px;

    top: -130px;

    background: #743cff;

}}

.orb-two {{

    right: -210px;

    top: 20px;

    background: #ff25bd;

}}

.orb-three {{

    left: 30%;

    bottom: -250px;

    background: #00bfff;

}}

/* ============================================================
   APP
============================================================ */

.container {{

    width: 100%;

    max-width: 560px;

    margin: 0 auto;

}}

/* ============================================================
   TOPBAR
============================================================ */

.topbar {{

    height: 55px;

    display: flex;

    align-items: center;

    justify-content: space-between;

}}

.brand-mini {{

    display: flex;

    align-items: center;

    gap: 9px;

    font-size: 15px;

    font-weight: 950;

}}

.brand-icon {{

    width: 32px;

    height: 32px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 11px;

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff
        );

    font-size: 17px;

}}

.theme {{

    width: 43px;

    height: 43px;

    border: 1px solid var(--border);

    border-radius: 14px;

    background: var(--card-soft);

    color: var(--text);

    font-size: 18px;

    cursor: pointer;

    backdrop-filter: blur(18px);

    -webkit-backdrop-filter: blur(18px);

}}

/* ============================================================
   HERO
============================================================ */

.hero {{

    text-align: center;

    padding:
        19px 0 24px;

}}

.logo {{

    width: 78px;

    height: 78px;

    margin: 0 auto 17px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 25px;

    font-size: 40px;

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 22px 65px
        rgba(116,60,255,.35);

    animation:
        floatLogo 4s ease-in-out infinite;

}}

@keyframes floatLogo {{

    0%,100% {{
        transform: translateY(0);
    }}

    50% {{
        transform: translateY(-4px);
    }}

}}

.hero h1 {{

    margin: 0;

    font-size: 31px;

    line-height: 1.08;

    font-weight: 950;

    letter-spacing: -1px;

}}

.hero p {{

    margin:
        9px 0 0;

    color: var(--muted);

    font-size: 13px;

}}

/* ============================================================
   MAIN CARD
============================================================ */

.card {{

    padding: 14px;

    border-radius: 31px;

    background: var(--card);

    border:
        1px solid var(--border);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.45);

    backdrop-filter: blur(30px);

    -webkit-backdrop-filter: blur(30px);

    animation:
        cardIn .45s ease;

}}

@keyframes cardIn {{

    from {{
        opacity: 0;
        transform: translateY(14px);
    }}

    to {{
        opacity: 1;
        transform: translateY(0);
    }}

}}

/* ============================================================
   STATUS
============================================================ */

.status {{

    padding: 18px;

    border-radius: 23px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    border:
        1px solid var(--border);

}}

.status.active {{

    background:
        linear-gradient(
            135deg,
            rgba(0,237,155,.13),
            rgba(0,170,255,.05)
        );

}}

.status.inactive {{

    background:
        rgba(255,70,90,.075);

}}

.status-left {{

    display: flex;

    align-items: center;

    gap: 12px;

}}

.status-dot {{

    width: 12px;

    height: 12px;

    border-radius: 50%;

    flex-shrink: 0;

}}

.active .status-dot {{

    background: var(--green);

    box-shadow:
        0 0 18px
        rgba(0,237,155,.85);

}}

.inactive .status-dot {{

    background: var(--red);

    box-shadow:
        0 0 18px
        rgba(255,82,101,.7);

}}

.status-title {{

    font-size: 15px;

    font-weight: 950;

}}

.status-sub {{

    margin-top: 4px;

    color: var(--muted);

    font-size: 11px;

}}

.status-icon {{

    width: 38px;

    height: 38px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 13px;

    background: var(--card-soft);

    font-size: 17px;

}}

/* ============================================================
   STATS
============================================================ */

.stats {{

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 9px;

    margin-top: 9px;

}}

.stat {{

    padding: 17px;

    border-radius: 21px;

    background: var(--card-soft);

    border:
        1px solid var(--border);

}}

.stat-label {{

    color: var(--muted);

    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: .4px;

}}

.stat-value {{

    margin-top: 7px;

    font-size: 15px;

    font-weight: 950;

    word-break: break-word;

}}

/* ============================================================
   DAYS
============================================================ */

.days {{

    margin-top: 9px;

    padding: 17px;

    border-radius: 21px;

    background:
        linear-gradient(
            135deg,
            rgba(116,60,255,.12),
            rgba(0,200,255,.06)
        );

    border:
        1px solid var(--border);

}}

.days-top {{

    display: flex;

    align-items: center;

    justify-content: space-between;

}}

.days-title {{

    color: var(--muted);

    font-size: 11px;

    font-weight: 800;

}}

.days-number {{

    font-size: 14px;

    font-weight: 950;

}}

.progress {{

    height: 7px;

    margin-top: 13px;

    overflow: hidden;

    border-radius: 20px;

    background:
        rgba(255,255,255,.08);

}}

body.light .progress {{

    background:
        rgba(0,0,0,.08);

}}

.progress-inner {{

    width: {progress}%;

    height: 100%;

    border-radius: inherit;

    background:
        linear-gradient(
            90deg,
            #ff27ba,
            #743cff,
            #00c9ff
        );

}}

/* ============================================================
   PROFILE
============================================================ */

.profile {{

    margin-top: 9px;

    padding: 17px;

    border-radius: 21px;

    background: var(--card-soft);

    border:
        1px solid var(--border);

}}

.profile-head {{

    display: flex;

    align-items: center;

    gap: 10px;

    margin-bottom: 9px;

    font-size: 13px;

    font-weight: 950;

}}

.profile-avatar {{

    width: 35px;

    height: 35px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 12px;

    background:
        linear-gradient(
            135deg,
            #743cff,
            #ff27ba
        );

}}

.profile-row {{

    display: flex;

    justify-content: space-between;

    gap: 15px;

    padding: 8px 0;

}}

.profile-label {{

    color: var(--muted);

    font-size: 11px;

}}

.profile-value {{

    max-width: 62%;

    text-align: right;

    font-size: 12px;

    font-weight: 850;

    word-break: break-word;

}}

/* ============================================================
   CONNECTION
============================================================ */

.section {{

    margin-top: 23px;

}}

.section-title {{

    font-size: 18px;

    font-weight: 950;

}}

.section-sub {{

    margin-top: 5px;

    color: var(--muted);

    font-size: 11px;

    line-height: 1.45;

}}

.button {{

    width: 100%;

    min-height: 57px;

    margin-top: 10px;

    border: 0;

    border-radius: 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 9px;

    color: white;

    font-family: inherit;

    font-size: 14px;

    font-weight: 950;

    cursor: pointer;

    text-decoration: none;

    transition:
        transform .12s ease,
        opacity .12s ease;

}}

.button:active {{

    transform: scale(.97);

    opacity: .86;

}}

.primary {{

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff
        );

    box-shadow:
        0 13px 35px
        rgba(116,60,255,.24);

}}

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #ff607c
        );

}}

.incy {{

    background:
        linear-gradient(
            135deg,
            #663cff,
            #00baff
        );

}}

.secondary {{

    color: var(--text);

    background: var(--card-soft);

    border:
        1px solid var(--border);

}}

.refresh {{

    color: var(--muted);

    background: transparent;

    border:
        1px solid var(--border);

}}

/* ============================================================
   LINK
============================================================ */

.link-title {{

    margin:
        22px 2px 8px;

    color: var(--muted);

    font-size: 10px;

    font-weight: 900;

    letter-spacing: .4px;

}}

.link-box {{

    padding: 14px;

    border-radius: 17px;

    background:
        rgba(0,0,0,.20);

    border:
        1px solid var(--border);

    color: var(--muted);

    font-size: 10px;

    line-height: 1.5;

    word-break: break-all;

    cursor: pointer;

}}

body.light .link-box {{

    background:
        rgba(0,0,0,.035);

}}

/* ============================================================
   TELEGRAM
============================================================ */

.telegram {{

    margin-top: 10px;

    min-height: 52px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 17px;

    border:
        1px solid var(--border);

    color: var(--text);

    text-decoration: none;

    font-size: 12px;

    font-weight: 850;

    background: var(--card-soft);

}}

/* ============================================================
   FOOTER
============================================================ */

.footer {{

    padding: 18px 0 4px;

    text-align: center;

    color: var(--muted);

    opacity: .7;

    font-size: 10px;

}}

/* ============================================================
   TOAST
============================================================ */

.toast {{

    position: fixed;

    left: 50%;

    bottom:
        max(22px, env(safe-area-inset-bottom));

    transform:
        translate(-50%,25px);

    width: max-content;

    max-width:
        calc(100% - 28px);

    padding:
        12px 17px;

    border-radius: 15px;

    background:
        rgba(25,25,31,.97);

    border:
        1px solid rgba(255,255,255,.1);

    color: white;

    font-size: 12px;

    font-weight: 850;

    box-shadow:
        0 18px 55px
        rgba(0,0,0,.45);

    opacity: 0;

    pointer-events: none;

    transition:
        opacity .2s ease,
        transform .2s ease;

    z-index: 9999;

}}

.toast.show {{

    opacity: 1;

    transform:
        translate(-50%,0);

}}

/* ============================================================
   SMALL
============================================================ */

@media (max-width: 380px) {{

    body {{
        padding-left: 10px;
        padding-right: 10px;
    }}

    .card {{
        padding: 11px;
        border-radius: 27px;
    }}

    .hero h1 {{
        font-size: 28px;
    }}

}}

/* ============================================================
   DESKTOP
============================================================ */

@media (min-width: 700px) {{

    body {{
        padding-top: 25px;
    }}

    .topbar {{
        margin-bottom: 8px;
    }}

}}

</style>

</head>

<body>

<div class="background-orb orb-one"></div>
<div class="background-orb orb-two"></div>
<div class="background-orb orb-three"></div>

<div class="container">

    <!-- =====================================================
         TOP
    ====================================================== -->

    <div class="topbar">

        <div class="brand-mini">

            <div class="brand-icon">
                ☂️
            </div>

            ixxy VPN

        </div>

        <button
            class="theme"
            id="themeButton"
            type="button"
            onclick="toggleTheme()"
        >
            🌙
        </button>

    </div>


    <!-- =====================================================
         HERO
    ====================================================== -->

    <div class="hero">

        <div class="logo">
            ☂️
        </div>

        <h1>
            Моя подписка
        </h1>

        <p>
            Персональный доступ к ixxy VPN
        </p>

    </div>


    <!-- =====================================================
         CARD
    ====================================================== -->

    <div class="card">

        <!-- STATUS -->

        <div class="status {status_class}">

            <div class="status-left">

                <div class="status-dot"></div>

                <div>

                    <div class="status-title">
                        {status_text}
                    </div>

                    <div class="status-sub">
                        Защищённое VPN-подключение
                    </div>

                </div>

            </div>

            <div class="status-icon">
                {status_icon}
            </div>

        </div>


        <!-- STATS -->

        <div class="stats">

            <div class="stat">

                <div class="stat-label">
                    Тариф
                </div>

                <div class="stat-value">
                    {safe_tariff}
                </div>

            </div>

            <div class="stat">

                <div class="stat-label">
                    Действует до
                </div>

                <div class="stat-value">
                    {safe_until}
                </div>

            </div>

        </div>


        <!-- DAYS -->

        <div class="days">

            <div class="days-top">

                <div class="days-title">
                    ОСТАЛОСЬ
                </div>

                <div class="days-number">
                    {safe_days}
                </div>

            </div>

            <div class="progress">

                <div class="progress-inner"></div>

            </div>

        </div>


        <!-- PROFILE -->

        <div class="profile">

            <div class="profile-head">

                <div class="profile-avatar">
                    👤
                </div>

                Профиль

            </div>

            <div class="profile-row">

                <div class="profile-label">
                    Имя
                </div>

                <div class="profile-value">
                    {safe_first_name}
                </div>

            </div>

            <div class="profile-row">

                <div class="profile-label">
                    Username
                </div>

                <div class="profile-value">
                    @{safe_username}
                </div>

            </div>

            <div class="profile-row">

                <div class="profile-label">
                    Telegram ID
                </div>

                <div class="profile-value">
                    {user_id}
                </div>

            </div>

        </div>


        <!-- CONNECTION -->

        <div class="section">

            <div class="section-title">
                Подключение
            </div>

            <div class="section-sub">
                Добавьте вашу персональную подписку
                в VPN-клиент.
            </div>


            <!-- HAPP -->

            <button
                type="button"
                class="button happ"
                onclick="openApp('happ')"
            >
                📲 Добавить в Happ
            </button>


            <!-- INCY -->

            <button
                type="button"
                class="button incy"
                onclick="openApp('incy')"
            >
                🚀 Добавить в INCY
            </button>


            <!-- COPY -->

            <button
                type="button"
                class="button secondary"
                onclick="copyLink()"
            >
                📋 Скопировать ссылку
            </button>


            <!-- REFRESH -->

            <button
                type="button"
                class="button refresh"
                onclick="refreshPage()"
            >
                🔄 Обновить подписку
            </button>

        </div>


        <!-- LINK -->

        <div class="link-title">
            ПЕРСОНАЛЬНАЯ ССЫЛКА
        </div>

        <div
            class="link-box"
            onclick="copyLink()"
        >
            {safe_subscription_url}
        </div>


        <!-- TELEGRAM -->

        <a
            class="telegram"
            href="{js_telegram_url}"
        >
            ← Вернуться в Telegram
        </a>

    </div>


    <!-- FOOTER -->

    <div class="footer">
        ☂️ ixxy VPN • Premium VPN
    </div>

</div>


<!-- TOAST -->

<div
    id="toast"
    class="toast"
></div>


<script>

/* ============================================================
   URLS
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

    const button =
        document.getElementById(
            "themeButton"
        );

    if (theme === "light") {{

        document.body.classList.add(
            "light"
        );

        if (button) {{
            button.textContent = "☀️";
        }}

    }} else {{

        document.body.classList.remove(
            "light"
        );

        if (button) {{
            button.textContent = "🌙";
        }}

    }}

}}


function toggleTheme() {{

    const current =
        localStorage.getItem(
            "ixxy_theme"
        ) || "dark";

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
    localStorage.getItem(
        "ixxy_theme"
    ) || "dark"
);


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;


function showToast(text) {{

    const toast =
        document.getElementById(
            "toast"
        );

    if (!toast) {{
        return;
    }}

    toast.textContent =
        text;

    toast.classList.add(
        "show"
    );

    clearTimeout(
        toastTimer
    );

    toastTimer =
        setTimeout(() => {{

            toast.classList.remove(
                "show"
            );

        }}, 2200);

}}


/* ============================================================
   OPEN APP
============================================================ */

function openApp(appName) {{

    const url =
        appName === "happ"
            ? happUrl
            : incyUrl;

    const name =
        appName === "happ"
            ? "Happ"
            : "INCY";

    showToast(
        "📲 Открываем "
        + name
        + "..."
    );

    const started =
        Date.now();

    document.addEventListener(
        "visibilitychange",
        function handleVisibility() {{

            if (document.hidden) {{

                document.removeEventListener(
                    "visibilitychange",
                    handleVisibility
                );

            }}

        }}
    );

    try {{

        window.location.href =
            url;

    }} catch (e) {{

        console.log(e);

    }}

    setTimeout(() => {{

        if (
            !document.hidden &&
            Date.now() - started >= 1600
        ) {{

            showToast(
                "⚠️ Приложение не открылось. "
                + "Скопируйте ссылку."
            );

        }}

    }}, 1700);

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
            "✅ Ссылка скопирована"
        );

        return;

    }} catch (e) {{

        console.log(e);

    }}

    try {{

        const textarea =
            document.createElement(
                "textarea"
            );

        textarea.value =
            subscriptionLink;

        textarea.style.position =
            "fixed";

        textarea.style.left =
            "-9999px";

        document.body.appendChild(
            textarea
        );

        textarea.focus();

        textarea.select();

        const success =
            document.execCommand(
                "copy"
            );

        textarea.remove();

        if (success) {{

            showToast(
                "✅ Ссылка скопирована"
            );

        }} else {{

            throw new Error(
                "copy failed"
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

    }}, 350);

}}

</script>

</body>

</html>
"""

    return Response(

        page,

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
# RAW SUBSCRIPTION
# ============================================================

@app.route("/sub/<token>")
def subscription_content(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    try:

        content = get_subscription_content(
            user_id
        )

    except Exception as e:

        print(
            f"❌ subscription error "
            f"{user_id}: {e}"
        )

        content = ""

    if not content:

        return Response(

            "#profile-title: ⛔ ixxy VPN\n"
            "#announce: Подписка не найдена",

            status=404,

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

            "Access-Control-Allow-Origin":
                "*",

        },
    )


# ============================================================
# MAIN
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
/>

<meta
    name="theme-color"
    content="#070709"
/>

<title>☂️ ixxy VPN</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    min-height: 100%;
}

body {

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;

    color: white;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255,30,190,.25),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 0%,
            rgba(0,190,255,.20),
            transparent 32%
        ),
        #070709;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

}

.box {

    width: 100%;

    max-width: 430px;

    padding: 42px 26px;

    text-align: center;

    border-radius: 31px;

    background:
        rgba(18,18,24,.88);

    border:
        1px solid rgba(255,255,255,.08);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.5);

    backdrop-filter:
        blur(30px);

}

.logo {

    width: 82px;

    height: 82px;

    margin:
        0 auto 20px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 26px;

    font-size: 42px;

    background:
        linear-gradient(
            135deg,
            #ff27ba,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 20px 60px
        rgba(116,60,255,.4);

}

h1 {

    margin: 0;

    font-size: 31px;

    font-weight: 950;

}

p {

    margin:
        10px 0 0;

    color: #909099;

    font-size: 14px;

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
        Персональный VPN-сервис
    </p>

</div>

</body>

</html>
"""


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return Response(
        "OK",
        status=200,
        mimetype="text/plain",
        headers={
            "Cache-Control":
                "no-cache, no-store, must-revalidate"
        },
    )


# ============================================================
# START
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