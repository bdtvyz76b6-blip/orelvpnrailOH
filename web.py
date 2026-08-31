import os
import html
import json
from datetime import datetime, date
from urllib.parse import quote

from flask import Flask, Response, abort


from database import (
    get_subscription_content,
    get_user,
)


# ============================================================
# IXXY VPN
# PREMIUM WEB PANEL
# web.py
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


TELEGRAM_URL = os.getenv(
    "TELEGRAM_URL",
    "https://t.me/orelvpntopbot",
)


APP_NAME = "ixxy VPN"


# ============================================================
# BASIC HELPERS
# ============================================================

def get_user_id_from_token(token):
    """
    2ix847xy123456789
    ->
    123456789
    """

    if not token:
        return None

    token = str(token).strip()

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


def get_urls(user_id):

    token = get_token(user_id)

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
# ESCAPING
# ============================================================

def esc(value):

    return html.escape(
        str(value),
        quote=True
    )


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
# DATE
# ============================================================

def parse_subscription_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
    )

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt
            ).date()

        except Exception:
            continue

    return None


def days_word(days):

    try:
        days = abs(int(days))
    except Exception:
        days = 0

    if 11 <= days % 100 <= 14:
        return "дней"

    last = days % 10

    if last == 1:
        return "день"

    if 2 <= last <= 4:
        return "дня"

    return "дней"


# ============================================================
# USER DATA
# ============================================================

def read_user_data(user):

    data = {
        "username": "нет",
        "first_name": "Пользователь",
        "subscription": "none",
        "until": "",
        "user_id": "",
    }

    if not user:
        return data

    try:
        data["user_id"] = user[0]
    except Exception:
        pass

    try:
        data["username"] = (
            str(user[1])
            if user[1]
            else "нет"
        )
    except Exception:
        pass

    try:
        data["first_name"] = (
            str(user[2])
            if user[2]
            else "Пользователь"
        )
    except Exception:
        pass

    try:
        data["subscription"] = (
            str(user[3])
            if user[3]
            else "none"
        )
    except Exception:
        pass

    try:
        data["until"] = (
            str(user[4])
            if user[4]
            else ""
        )
    except Exception:
        pass

    return data


# ============================================================
# SUBSCRIPTION INFORMATION
# ============================================================

def get_subscription_info(user_data):

    subscription = (
        user_data["subscription"]
        or "none"
    )

    until = user_data["until"]

    tariff = "Нет подписки"
    tariff_icon = "○"

    if subscription == "vip":

        tariff = "ixxy VIP"
        tariff_icon = "👑"

    elif subscription == "trial":

        tariff = "Пробный период"
        tariff_icon = "🎁"

    elif subscription in (
        "active",
        "premium",
        "standard",
    ):

        tariff = "ixxy VPN"
        tariff_icon = "☂️"

    expire_date = parse_subscription_date(
        until
    )

    today = datetime.now().date()

    days_left = 0

    status = "Неактивна"
    status_class = "inactive"

    if expire_date:

        days_left = (
            expire_date - today
        ).days

        if days_left >= 0:

            status = "Активна"
            status_class = "active"

        else:

            status = "Истекла"
            status_class = "inactive"

            days_left = 0

    until_text = "—"

    if expire_date:

        until_text = expire_date.strftime(
            "%d.%m.%Y"
        )

    return {
        "tariff": tariff,
        "tariff_icon": tariff_icon,
        "expire_date": expire_date,
        "until_text": until_text,
        "days_left": days_left,
        "days_text": (
            f"{days_left} "
            f"{days_word(days_left)}"
        ),
        "status": status,
        "status_class": status_class,
    }


# ============================================================
# NO SUBSCRIPTION
# ============================================================

def no_subscription_page():

    return r"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1,viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#06070b"
>

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
    min-height: 100dvh;

    display: flex;
    align-items: center;
    justify-content: center;

    padding: 22px;

    background:
        radial-gradient(
            circle at 15% 0%,
            rgba(124,92,255,.30),
            transparent 35%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(0,205,255,.18),
            transparent 35%
        ),
        #06070b;

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}

.box {

    width: 100%;
    max-width: 430px;

    padding: 34px 24px;

    border-radius: 34px;

    background:
        rgba(19,21,30,.78);

    border:
        1px solid rgba(255,255,255,.09);

    box-shadow:
        0 35px 100px rgba(0,0,0,.55);

    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);

    text-align: center;
}

.icon {

    width: 86px;
    height: 86px;

    margin: 0 auto 22px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 27px;

    background:
        linear-gradient(
            145deg,
            #765cff,
            #a348ff,
            #ff42b7
        );

    font-size: 42px;

    box-shadow:
        0 20px 65px
        rgba(120,80,255,.42);
}

h1 {

    margin: 0;

    font-size: 29px;
    font-weight: 900;
}

p {

    margin: 10px 0 0;

    color: #9397a5;

    font-size: 14px;

    line-height: 1.6;
}

a {

    display: flex;

    align-items: center;
    justify-content: center;

    min-height: 54px;

    margin-top: 25px;

    border-radius: 18px;

    color: white;

    text-decoration: none;

    font-weight: 850;

    background:
        linear-gradient(
            135deg,
            #755cff,
            #a347ff
        );
}

</style>

</head>

<body>

<div class="box">

    <div class="icon">
        ☂️
    </div>

    <h1>
        Подписка не найдена
    </h1>

    <p>
        У этого аккаунта пока нет активной
        VPN-подписки.
    </p>

    <a href="https://t.me/orelvpntopbot">
        Открыть Telegram-бот
    </a>

</div>

</body>
</html>
"""


# ============================================================
# PREMIUM PAGE
# ============================================================

def premium_page(
    user_id,
    user_data,
    subscription_info,
    urls,
):

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = urls

    tariff = subscription_info["tariff"]
    tariff_icon = subscription_info["tariff_icon"]

    status = subscription_info["status"]
    status_class = subscription_info["status_class"]

    until_text = subscription_info["until_text"]

    days_left = subscription_info["days_left"]
    days_text = subscription_info["days_text"]

    username = user_data["username"]
    first_name = user_data["first_name"]

    if username != "нет":
        username_display = "@" + username
    else:
        username_display = "Не указан"

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    progress = 100

    if days_left <= 0:
        progress = 0

    elif days_left <= 7:
        progress = 18

    elif days_left <= 14:
        progress = 32

    elif days_left <= 30:
        progress = 55

    elif days_left <= 90:
        progress = 72

    else:
        progress = 88

    # --------------------------------------------------------
    # SAFE
    # --------------------------------------------------------

    s_first_name = esc(first_name)
    s_username = esc(username_display)
    s_tariff = esc(tariff)
    s_until = esc(until_text)
    s_days = esc(days_text)
    s_status = esc(status)

    s_subscription = esc(
        subscription_url
    )

    js_subscription = js_escape(
        subscription_url
    )

    js_happ = js_escape(
        happ_url
    )

    js_incy = js_escape(
        incy_url
    )

    js_page = js_escape(
        page_url
    )

    js_telegram = js_escape(
        TELEGRAM_URL
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    return f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1,viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#06070b"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
>

<title>☂️ ixxy VPN — Личный кабинет</title>

<style>

/* ============================================================
   RESET
============================================================ */

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    min-height: 100%;
    scroll-behavior: smooth;
}}

body {{

    margin: 0;

    min-height: 100vh;
    min-height: 100dvh;

    color: var(--text);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at 0% 0%,
            rgba(122,91,255,.26),
            transparent 29%
        ),
        radial-gradient(
            circle at 100% 0%,
            rgba(0,211,255,.19),
            transparent 31%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(255,41,180,.12),
            transparent 38%
        ),
        var(--bg);

    color-scheme: dark;

    overflow-x: hidden;

    -webkit-font-smoothing: antialiased;

    padding:
        0
        0
        calc(96px + env(safe-area-inset-bottom));
}}

:root {{

    --bg: #06070b;

    --panel:
        rgba(17,19,28,.72);

    --panel-strong:
        rgba(20,22,33,.90);

    --surface:
        rgba(255,255,255,.055);

    --surface-2:
        rgba(255,255,255,.075);

    --border:
        rgba(255,255,255,.085);

    --border-strong:
        rgba(255,255,255,.13);

    --text:
        #ffffff;

    --muted:
        #8e93a3;

    --muted-2:
        #646978;

    --purple:
        #8067ff;

    --purple-2:
        #aa6fff;

    --blue:
        #38bdf8;

    --pink:
        #ff43b8;

    --green:
        #35e69a;

    --red:
        #ff5b70;

    --shadow:
        rgba(0,0,0,.48);
}}

/* ============================================================
   BACKGROUND
============================================================ */

.background {{
    position: fixed;
    inset: 0;

    pointer-events: none;

    overflow: hidden;

    z-index: 0;
}}

.orb {{
    position: absolute;

    width: 300px;
    height: 300px;

    border-radius: 50%;

    filter: blur(90px);

    opacity: .18;

    animation:
        orbFloat 9s ease-in-out infinite;
}}

.orb.one {{

    top: -150px;
    left: -120px;

    background:
        #805fff;
}}

.orb.two {{

    top: 25%;
    right: -170px;

    background:
        #00bfff;

    animation-delay:
        -3s;
}}

.orb.three {{

    bottom: -190px;
    left: 25%;

    background:
        #ff39ad;

    animation-delay:
        -6s;
}}

@keyframes orbFloat {{

    0%,100% {{
        transform: translate3d(0,0,0) scale(1);
    }}

    50% {{
        transform: translate3d(0,22px,0) scale(1.08);
    }}
}}

/* ============================================================
   APP
============================================================ */

.app {{
    position: relative;

    z-index: 2;

    width: 100%;
    max-width: 620px;

    margin: 0 auto;

    padding:
        max(18px, env(safe-area-inset-top))
        16px
        0;
}}

/* ============================================================
   TOP NAV
============================================================ */

.top-nav {{

    height: 58px;

    display: flex;

    align-items: center;

    justify-content: space-between;
}}

.nav-brand {{

    display: flex;

    align-items: center;

    gap: 10px;
}}

.nav-logo {{

    width: 40px;
    height: 40px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 13px;

    background:
        linear-gradient(
            145deg,
            #735cff,
            #aa55ff,
            #ff3bb3
        );

    box-shadow:
        0 10px 30px
        rgba(120,80,255,.28);

    font-size: 21px;
}}

.nav-name {{

    font-size: 15px;

    font-weight: 900;

    letter-spacing: -.3px;
}}

.nav-sub {{

    margin-top: 1px;

    color: var(--muted);

    font-size: 10px;
}}

.nav-actions {{

    display: flex;

    gap: 7px;
}}

.icon-button {{

    width: 41px;
    height: 41px;

    display: flex;

    align-items: center;
    justify-content: center;

    border:
        1px solid var(--border);

    border-radius: 13px;

    background:
        var(--surface);

    color: white;

    cursor: pointer;

    font-size: 17px;

    backdrop-filter: blur(18px);

    -webkit-backdrop-filter: blur(18px);

    transition:
        transform .15s ease,
        background .2s ease;
}}

.icon-button:active {{
    transform: scale(.91);
}}

/* ============================================================
   HERO
============================================================ */

.hero {{

    margin-top: 16px;

    padding: 24px 20px 20px;

    border:
        1px solid var(--border);

    border-radius: 32px;

    background:
        linear-gradient(
            145deg,
            rgba(29,28,47,.78),
            rgba(13,15,23,.72)
        );

    box-shadow:
        0 28px 90px var(--shadow);

    backdrop-filter:
        blur(30px);

    -webkit-backdrop-filter:
        blur(30px);

    overflow: hidden;

    position: relative;
}}

.hero::before {{

    content: "";

    position: absolute;

    width: 240px;
    height: 240px;

    right: -120px;
    top: -130px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(132,98,255,.42),
            transparent 68%
        );

    pointer-events: none;
}}

.hero-top {{

    position: relative;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;
}}

.hero-copy {{

    min-width: 0;
}}

.eyebrow {{

    display: flex;

    align-items: center;

    gap: 7px;

    color: #aaa4ff;

    font-size: 11px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: .7px;
}}

.live-dot {{

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background:
        var(--green);

    box-shadow:
        0 0 15px
        rgba(53,230,154,.8);
}}

.hero h1 {{

    margin:
        7px 0 0;

    font-size: 31px;

    line-height: 1.03;

    font-weight: 950;

    letter-spacing:
        -1.3px;
}}

.hero-description {{

    margin-top: 8px;

    color: var(--muted);

    font-size: 12px;

    line-height: 1.5;
}}

.hero-avatar {{

    width: 74px;
    height: 74px;

    flex-shrink: 0;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 24px;

    background:
        linear-gradient(
            145deg,
            rgba(127,99,255,.28),
            rgba(255,55,180,.16)
        );

    border:
        1px solid
        rgba(157,130,255,.22);

    box-shadow:
        inset 0 1px 0
        rgba(255,255,255,.08),
        0 15px 45px
        rgba(90,60,255,.22);

    font-size: 34px;
}}

.hero-user {{

    margin-top: 20px;

    padding: 12px 14px;

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 10px;

    border-radius: 17px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid var(--border);
}}

.hero-user-left {{

    min-width: 0;

    display: flex;

    align-items: center;

    gap: 10px;
}}

.user-circle {{

    width: 36px;
    height: 36px;

    display: flex;

    align-items: center;
    justify-content: center;

    flex-shrink: 0;

    border-radius: 12px;

    background:
        rgba(128,103,255,.14);

    border:
        1px solid
        rgba(128,103,255,.18);
}}

.user-info {{

    min-width: 0;
}}

.user-name {{

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

    font-size: 12px;

    font-weight: 850;
}}

.user-username {{

    margin-top: 2px;

    color: var(--muted);

    font-size: 10px;
}}

.telegram-link {{

    color: #a69aff;

    text-decoration: none;

    font-size: 11px;

    font-weight: 800;
}}

/* ============================================================
   MAIN VPN CARD
============================================================ */

.vpn-card {{

    margin-top: 12px;

    padding: 20px;

    border-radius: 29px;

    background:
        var(--panel-strong);

    border:
        1px solid var(--border);

    box-shadow:
        0 25px 75px
        rgba(0,0,0,.35);

    backdrop-filter: blur(28px);

    -webkit-backdrop-filter: blur(28px);
}}

.vpn-status {{

    display: flex;

    align-items: center;

    justify-content: space-between;
}}

.status-pill {{

    display: inline-flex;

    align-items: center;

    gap: 8px;

    padding:
        8px 11px;

    border-radius: 999px;

    font-size: 11px;

    font-weight: 850;
}}

.status-pill.active {{

    color:
        #8ff2c4;

    background:
        rgba(53,230,154,.08);

    border:
        1px solid
        rgba(53,230,154,.14);
}}

.status-pill.inactive {{

    color:
        #ff9aaa;

    background:
        rgba(255,91,112,.08);

    border:
        1px solid
        rgba(255,91,112,.14);
}}

.status-mini-dot {{

    width: 7px;
    height: 7px;

    border-radius: 50%;
}}

.status-pill.active .status-mini-dot {{

    background:
        var(--green);

    box-shadow:
        0 0 12px
        rgba(53,230,154,.85);
}}

.status-pill.inactive .status-mini-dot {{

    background:
        var(--red);
}}

.vpn-badge {{

    color: var(--muted);

    font-size: 10px;

    font-weight: 700;
}}

.big-connect {{

    margin:
        22px auto 20px;

    width: 188px;
    height: 188px;

    border-radius: 50%;

    position: relative;

    display: flex;

    align-items: center;
    justify-content: center;

    cursor: pointer;

    border: 0;

    background:
        radial-gradient(
            circle,
            rgba(120,97,255,.24) 0%,
            rgba(120,97,255,.10) 47%,
            transparent 48%
        );

    color: white;

    font-family: inherit;

    transition:
        transform .2s ease;
}}

.big-connect::before {{

    content: "";

    position: absolute;

    inset: 9px;

    border-radius: 50%;

    border:
        1px solid
        rgba(146,124,255,.28);

    box-shadow:
        0 0 45px
        rgba(119,91,255,.15);

    animation:
        pulseRing 2.8s ease-in-out infinite;
}}

.big-connect::after {{

    content: "";

    position: absolute;

    inset: 22px;

    border-radius: 50%;

    background:
        linear-gradient(
            145deg,
            #8b6cff,
            #7657ff,
            #a15bff
        );

    box-shadow:
        0 20px 60px
        rgba(113,82,255,.40),
        inset 0 1px 0
        rgba(255,255,255,.18);

    z-index: 0;
}}

.big-connect:active {{
    transform: scale(.95);
}}

@keyframes pulseRing {{

    0%,100% {{
        transform: scale(1);
        opacity: .65;
    }}

    50% {{
        transform: scale(1.04);
        opacity: 1;
    }}
}}

.connect-content {{

    position: relative;

    z-index: 2;

    text-align: center;
}}

.connect-icon {{

    font-size: 31px;

    line-height: 1;
}}

.connect-title {{

    margin-top: 8px;

    font-size: 14px;

    font-weight: 900;
}}

.connect-sub {{

    margin-top: 3px;

    color: rgba(255,255,255,.70);

    font-size: 9px;

    font-weight: 700;
}}

.vpn-caption {{

    text-align: center;

    color: var(--muted);

    font-size: 11px;

    line-height: 1.5;
}}

/* ============================================================
   QUICK STATS
============================================================ */

.stats {{

    display: grid;

    grid-template-columns:
        repeat(3,1fr);

    gap: 8px;

    margin-top: 13px;
}}

.stat {{

    min-width: 0;

    padding: 14px 10px;

    border-radius: 18px;

    background:
        var(--surface);

    border:
        1px solid var(--border);

    text-align: center;
}}

.stat-icon {{

    font-size: 16px;
}}

.stat-value {{

    margin-top: 7px;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

    font-size: 12px;

    font-weight: 900;
}}

.stat-label {{

    margin-top: 3px;

    color: var(--muted);

    font-size: 9px;

    font-weight: 650;
}}

/* ============================================================
   SECTION
============================================================ */

.section-head {{

    margin:
        27px 3px 11px;

    display: flex;

    align-items: flex-end;

    justify-content: space-between;
}}

.section-title {{

    font-size: 17px;

    font-weight: 920;

    letter-spacing: -.4px;
}}

.section-subtitle {{

    margin-top: 3px;

    color: var(--muted);

    font-size: 10px;
}}

/* ============================================================
   SUBSCRIPTION
============================================================ */

.subscription-card {{

    padding: 18px;

    border-radius: 25px;

    background:
        linear-gradient(
            145deg,
            rgba(126,99,255,.13),
            rgba(255,255,255,.035)
        );

    border:
        1px solid
        rgba(132,105,255,.17);

    box-shadow:
        0 20px 55px
        rgba(0,0,0,.22);
}}

.tariff-row {{

    display: flex;

    align-items: center;

    gap: 12px;
}}

.tariff-icon {{

    width: 48px;
    height: 48px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 16px;

    background:
        rgba(128,103,255,.13);

    border:
        1px solid
        rgba(128,103,255,.18);

    font-size: 22px;
}}

.tariff-name {{

    font-size: 14px;

    font-weight: 900;
}}

.tariff-caption {{

    margin-top: 3px;

    color: var(--muted);

    font-size: 10px;
}}

.expiry {{

    margin-top: 17px;

    display: flex;

    justify-content: space-between;

    align-items: flex-end;

    gap: 15px;
}}

.expiry-label {{

    color: var(--muted);

    font-size: 10px;
}}

.expiry-date {{

    margin-top: 4px;

    font-size: 19px;

    font-weight: 900;
}}

.expiry-days {{

    color: #a69aff;

    font-size: 12px;

    font-weight: 850;

    text-align: right;
}}

.progress-track {{

    height: 9px;

    margin-top: 14px;

    overflow: hidden;

    border-radius: 999px;

    background:
        rgba(255,255,255,.06);
}}

.progress-bar {{

    width: {progress}%;

    height: 100%;

    border-radius: inherit;

    background:
        linear-gradient(
            90deg,
            #795fff,
            #aa6cff,
            #e05fff
        );

    box-shadow:
        0 0 18px
        rgba(127,95,255,.45);

    transition:
        width 1s ease;
}}

/* ============================================================
   CONNECT APPS
============================================================ */

.apps-grid {{

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 10px;
}}

.app-card {{

    min-width: 0;

    padding: 17px;

    border-radius: 22px;

    border:
        1px solid var(--border);

    background:
        var(--surface);

    cursor: pointer;

    text-align: left;

    color: white;

    font-family: inherit;

    transition:
        transform .15s ease,
        background .2s ease,
        border-color .2s ease;
}}

.app-card:active {{
    transform: scale(.97);
}}

.app-card:hover {{
    border-color:
        var(--border-strong);
}}

.app-card-top {{

    display: flex;

    align-items: center;

    justify-content: space-between;
}}

.app-icon {{

    width: 44px;
    height: 44px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 14px;

    background:
        rgba(128,103,255,.12);

    font-size: 21px;
}}

.app-arrow {{

    color: var(--muted);

    font-size: 20px;
}}

.app-name {{

    margin-top: 14px;

    font-size: 13px;

    font-weight: 900;
}}

.app-caption {{

    margin-top: 3px;

    color: var(--muted);

    font-size: 9px;
}}

/* ============================================================
   LINK CARD
============================================================ */

.link-card {{

    padding: 17px;

    border-radius: 23px;

    background:
        var(--surface);

    border:
        1px solid var(--border);
}}

.link-label {{

    color: var(--muted);

    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: .5px;
}}

.link-box {{

    margin-top: 9px;

    min-height: 50px;

    padding: 13px;

    display: flex;

    align-items: center;

    border-radius: 15px;

    background:
        rgba(0,0,0,.18);

    border:
        1px solid
        rgba(255,255,255,.06);

    color: #9ca1b0;

    font-size: 10px;

    line-height: 1.4;

    word-break: break-all;

    user-select: text;
}}

.copy-link {{

    width: 100%;

    min-height: 48px;

    margin-top: 9px;

    border: 0;

    border-radius: 15px;

    background:
        linear-gradient(
            135deg,
            rgba(128,103,255,.18),
            rgba(165,96,255,.11)
        );

    border:
        1px solid
        rgba(128,103,255,.18);

    color: white;

    font-family: inherit;

    font-size: 12px;

    font-weight: 850;

    cursor: pointer;

    transition:
        transform .15s ease;
}}

.copy-link:active {{
    transform: scale(.98);
}}

/* ============================================================
   SECURITY
============================================================ */

.security-card {{

    padding: 17px;

    border-radius: 23px;

    background:
        linear-gradient(
            145deg,
            rgba(40,220,150,.055),
            rgba(255,255,255,.03)
        );

    border:
        1px solid
        rgba(53,230,154,.10);
}}

.security-row {{

    display: flex;

    align-items: center;

    gap: 12px;

    padding: 8px 0;
}}

.security-icon {{

    width: 36px;
    height: 36px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 12px;

    background:
        rgba(53,230,154,.08);

    font-size: 15px;
}}

.security-text strong {{

    display: block;

    font-size: 11px;

    font-weight: 850;
}}

.security-text span {{

    display: block;

    margin-top: 2px;

    color: var(--muted);

    font-size: 9px;
}}

/* ============================================================
   PROFILE
============================================================ */

.profile-card {{

    padding: 18px;

    border-radius: 23px;

    background:
        var(--surface);

    border:
        1px solid var(--border);
}}

.profile-row {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 15px;

    padding: 12px 0;

    border-bottom:
        1px solid
        rgba(255,255,255,.045);
}}

.profile-row:last-child {{
    border-bottom: 0;
}}

.profile-label {{

    color: var(--muted);

    font-size: 10px;
}}

.profile-value {{

    max-width: 60%;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

    color: var(--text);

    font-size: 11px;

    font-weight: 850;

    text-align: right;
}}

/* ============================================================
   FAQ
============================================================ */

.faq {{


    display: flex;

    flex-direction: column;

    gap: 8px;
}}

details {{

    padding: 0;

    border-radius: 18px;

    background:
        var(--surface);

    border:
        1px solid var(--border);

    overflow: hidden;
}}

summary {{

    padding: 16px;

    cursor: pointer;

    list-style: none;

    font-size: 11px;

    font-weight: 850;
}}

summary::-webkit-details-marker {{
    display: none;
}}

.answer {{

    padding:
        0 16px 16px;

    color: var(--muted);

    font-size: 10px;

    line-height: 1.6;
}}

/* ============================================================
   FOOTER
============================================================ */

.footer {{

    padding:
        24px 0 10px;

    text-align: center;

    color: var(--muted-2);

    font-size: 9px;

    line-height: 1.6;
}}

.footer-brand {{

    color: #9b8cff;

    font-weight: 850;
}}

/* ============================================================
   BOTTOM NAV
============================================================ */

.bottom-nav {{

    position: fixed;

    z-index: 100;

    left: 50%;

    bottom:
        max(12px, env(safe-area-inset-bottom));

    transform:
        translateX(-50%);

    width:
        min(470px, calc(100% - 28px));

    padding: 7px;

    display: grid;

    grid-template-columns:
        repeat(4,1fr);

    gap: 5px;

    border-radius: 22px;

    background:
        rgba(17,19,27,.86);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 18px 55px
        rgba(0,0,0,.50);

    backdrop-filter:
        blur(25px);

    -webkit-backdrop-filter:
        blur(25px);
}}

.bottom-item {{

    min-height: 48px;

    display: flex;

    flex-direction: column;

    align-items: center;

    justify-content: center;

    gap: 3px;

    border: 0;

    border-radius: 16px;

    background: transparent;

    color: var(--muted);

    font-family: inherit;

    cursor: pointer;

    font-size: 16px;

    transition:
        background .2s ease,
        color .2s ease;
}}

.bottom-item span:last-child {{

    font-size: 8px;

    font-weight: 750;
}}

.bottom-item.active {{

    background:
        rgba(128,103,255,.14);

    color: #c0b7ff;
}}

/* ============================================================
   TOAST
============================================================ */

.toast {{

    position: fixed;

    z-index: 999;

    left: 50%;

    bottom:
        calc(84px + env(safe-area-inset-bottom));

    transform:
        translate(-50%,20px);

    max-width:
        calc(100% - 30px);

    padding:
        12px 17px;

    border-radius: 15px;

    background:
        rgba(28,30,39,.95);

    border:
        1px solid
        rgba(255,255,255,.10);

    box-shadow:
        0 18px 50px
        rgba(0,0,0,.45);

    color: white;

    font-size: 11px;

    font-weight: 800;

    opacity: 0;

    pointer-events: none;

    transition:
        opacity .22s ease,
        transform .22s ease;

    backdrop-filter:
        blur(20px);

    -webkit-backdrop-filter:
        blur(20px);

    white-space: nowrap;
}}

.toast.show {{

    opacity: 1;

    transform:
        translate(-50%,0);
}}

/* ============================================================
   LIGHT
============================================================ */

body.light {{

    --bg: #eef0f6;

    --panel:
        rgba(255,255,255,.78);

    --panel-strong:
        rgba(255,255,255,.88);

    --surface:
        rgba(0,0,0,.035);

    --surface-2:
        rgba(0,0,0,.055);

    --border:
        rgba(0,0,0,.08);

    --border-strong:
        rgba(0,0,0,.13);

    --text:
        #11131a;

    --muted:
        #6d7180;

    --muted-2:
        #9498a4;

    color-scheme: light;

    background:
        radial-gradient(
            circle at 0% 0%,
            rgba(122,91,255,.15),
            transparent 29%
        ),
        radial-gradient(
            circle at 100% 0%,
            rgba(0,211,255,.12),
            transparent 31%
        ),
        var(--bg);
}}

body.light .bottom-nav {{

    background:
        rgba(255,255,255,.86);
}}

body.light .link-box {{

    background:
        rgba(0,0,0,.035);
}}

/* ============================================================
   RESPONSIVE
============================================================ */

@media (max-width: 390px) {{

    .app {{
        padding-left: 11px;
        padding-right: 11px;
    }}

    .hero {{
        padding:
            21px 16px 17px;
        border-radius: 28px;
    }}

    .hero h1 {{
        font-size: 27px;
    }}

    .hero-avatar {{
        width: 62px;
        height: 62px;
        border-radius: 21px;
        font-size: 28px;
    }}

    .vpn-card {{
        padding: 16px;
        border-radius: 26px;
    }}

    .big-connect {{
        width: 168px;
        height: 168px;
    }}

    .big-connect::after {{
        inset: 21px;
    }}

    .stats {{
        gap: 6px;
    }}
}}

@media (min-width: 700px) {{

    .app {{
        padding-top: 30px;
    }}

    .bottom-nav {{
        bottom: 20px;
    }}
}}

@media (prefers-reduced-motion: reduce) {{

    *,
    *::before,
    *::after {{
        animation: none !important;
        transition: none !important;
    }}
}}

</style>

</head>

<body>

<!-- ==========================================================
     BACKGROUND
========================================================== -->

<div class="background">

    <div class="orb one"></div>

    <div class="orb two"></div>

    <div class="orb three"></div>

</div>


<!-- ==========================================================
     APP
========================================================== -->

<div class="app">


    <!-- ======================================================
         TOP NAV
    ====================================================== -->

    <header class="top-nav">

        <div class="nav-brand">

            <div class="nav-logo">
                ☂️
            </div>

            <div>

                <div class="nav-name">
                    ixxy VPN
                </div>

                <div class="nav-sub">
                    Premium network
                </div>

            </div>

        </div>


        <div class="nav-actions">

            <button
                class="icon-button"
                type="button"
                onclick="toggleTheme()"
                id="themeButton"
                aria-label="Тема"
            >
                🌙
            </button>

            <button
                class="icon-button"
                type="button"
                onclick="refreshPage()"
                aria-label="Обновить"
            >
                ↻
            </button>

        </div>

    </header>


    <!-- ======================================================
         HERO
    ====================================================== -->

    <section
        class="hero"
        id="home"
    >

        <div class="hero-top">

            <div class="hero-copy">

                <div class="eyebrow">

                    <span class="live-dot"></span>

                    PRIVATE CONNECTION

                </div>

                <h1>
                    Привет, {s_first_name} 👋
                </h1>

                <div class="hero-description">
                    Ваш персональный VPN-профиль
                    готов к использованию.
                </div>

            </div>


            <div class="hero-avatar">
                ☂️
            </div>

        </div>


        <div class="hero-user">

            <div class="hero-user-left">

                <div class="user-circle">
                    👤
                </div>

                <div class="user-info">

                    <div class="user-name">
                        {s_first_name}
                    </div>

                    <div class="user-username">
                        {s_username}
                    </div>

                </div>

            </div>


            <a
                class="telegram-link"
                href="{js_telegram}"
            >
                Telegram →
            </a>

        </div>

    </section>


    <!-- ======================================================
         VPN CARD
    ====================================================== -->

    <section
        class="vpn-card"
        id="connect"
    >

        <div class="vpn-status">

            <div
                class="status-pill {status_class}"
            >

                <span class="status-mini-dot"></span>

                {s_status}

            </div>


            <div class="vpn-badge">
                IXXY SECURE
            </div>

        </div>


        <button
            class="big-connect"
            type="button"
            onclick="openHapp()"
            aria-label="Подключить VPN"
        >

            <div class="connect-content">

                <div class="connect-icon">
                    ⚡
                </div>

                <div class="connect-title">
                    Подключиться
                </div>

                <div class="connect-sub">
                    OPEN HAPP
                </div>

            </div>

        </button>


        <div class="vpn-caption">

            Нажмите, чтобы открыть VPN-клиент
            и подключить персональную конфигурацию.

        </div>


        <!-- ==================================================
             STATS
        ================================================== -->

        <div class="stats">

            <div class="stat">

                <div class="stat-icon">
                    {tariff_icon}
                </div>

                <div class="stat-value">
                    {s_tariff}
                </div>

                <div class="stat-label">
                    Тариф
                </div>

            </div>


            <div class="stat">

                <div class="stat-icon">
                    📅
                </div>

                <div class="stat-value">
                    {s_until}
                </div>

                <div class="stat-label">
                    До
                </div>

            </div>


            <div class="stat">

                <div class="stat-icon">
                    ⏳
                </div>

                <div class="stat-value">
                    {s_days}
                </div>

                <div class="stat-label">
                    Осталось
                </div>

            </div>

        </div>

    </section>


    <!-- ======================================================
         SUBSCRIPTION
    ====================================================== -->

    <section id="subscription">

        <div class="section-head">

            <div>

                <div class="section-title">
                    Подписка
                </div>

                <div class="section-subtitle">
                    Состояние вашего доступа
                </div>

            </div>

        </div>


        <div class="subscription-card">

            <div class="tariff-row">

                <div class="tariff-icon">
                    {tariff_icon}
                </div>

                <div>

                    <div class="tariff-name">
                        {s_tariff}
                    </div>

                    <div class="tariff-caption">
                        Персональный доступ ixxy VPN
                    </div>

                </div>

            </div>


            <div class="expiry">

                <div>

                    <div class="expiry-label">
                        Подписка активна до
                    </div>

                    <div class="expiry-date">
                        {s_until}
                    </div>

                </div>


                <div class="expiry-days">
                    {s_days}
                </div>

            </div>


            <div class="progress-track">

                <div
                    class="progress-bar"
                    id="progressBar"
                ></div>

            </div>

        </div>

    </section>


    <!-- ======================================================
         APPLICATIONS
    ====================================================== -->

    <section id="apps">

        <div class="section-head">

            <div>

                <div class="section-title">
                    Подключение
                </div>

                <div class="section-subtitle">
                    Выберите приложение
                </div>

            </div>

        </div>


        <div class="apps-grid">


            <button
                class="app-card"
                type="button"
                onclick="openHapp()"
            >

                <div class="app-card-top">

                    <div class="app-icon">
                        🚀
                    </div>

                    <div class="app-arrow">
                        ›
                    </div>

                </div>

                <div class="app-name">
                    Happ
                </div>

                <div class="app-caption">
                    Открыть VPN-конфигурацию
                </div>

            </button>


            <button
                class="app-card"
                type="button"
                onclick="openIncy()"
            >

                <div class="app-card-top">

                    <div class="app-icon">
                        ⚡
                    </div>

                    <div class="app-arrow">
                        ›
                    </div>

                </div>

                <div class="app-name">
                    INCY
                </div>

                <div class="app-caption">
                    Открыть VPN-конфигурацию
                </div>

            </button>


        </div>

    </section>


    <!-- ======================================================
         SUBSCRIPTION LINK
    ====================================================== -->

    <section id="link">

        <div class="section-head">

            <div>

                <div class="section-title">
                    Ваша ссылка
                </div>

                <div class="section-subtitle">
                    Персональная ссылка подписки
                </div>

            </div>

        </div>


        <div class="link-card">

            <div class="link-label">
                Subscription URL
            </div>


            <div
                class="link-box"
                id="subscriptionLink"
                onclick="copySubscription()"
            >
                {s_subscription}
            </div>


            <button
                class="copy-link"
                type="button"
                onclick="copySubscription()"
            >
                📋 Скопировать ссылку
            </button>

        </div>

    </section>


    <!-- ======================================================
         SECURITY
    ====================================================== -->

    <section>

        <div class="section-head">

            <div>

                <div class="section-title">
                    Защита
                </div>

                <div class="section-subtitle">
                    Состояние вашего доступа
                </div>

            </div>

        </div>


        <div class="security-card">


            <div class="security-row">

                <div class="security-icon">
                    🔐
                </div>

                <div class="security-text">

                    <strong>
                        Персональная конфигурация
                    </strong>

                    <span>
                        Доступ привязан к вашему Telegram ID
                    </span>

                </div>

            </div>


            <div class="security-row">

                <div class="security-icon">
                    🛡️
                </div>

                <div class="security-text">

                    <strong>
                        Защищённое подключение
                    </strong>

                    <span>
                        Конфигурация передаётся через HTTPS
                    </span>

                </div>

            </div>


            <div class="security-row">

                <div class="security-icon">
                    🔄
                </div>

                <div class="security-text">

                    <strong>
                        Автообновление
                    </strong>

                    <span>
                        Клиент может обновлять подписку автоматически
                    </span>

                </div>

            </div>


        </div>

    </section>


    <!-- ======================================================
         PROFILE
    ====================================================== -->

    <section id="profile">

        <div class="section-head">

            <div>

                <div class="section-title">
                    Профиль
                </div>

                <div class="section-subtitle">
                    Данные аккаунта
                </div>

            </div>

        </div>


        <div class="profile-card">


            <div class="profile-row">

                <div class="profile-label">
                    Имя
                </div>

                <div class="profile-value">
                    {s_first_name}
                </div>

            </div>


            <div class="profile-row">

                <div class="profile-label">
                    Username
                </div>

                <div class="profile-value">
                    {s_username}
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


            <div class="profile-row">

                <div class="profile-label">
                    Тариф
                </div>

                <div class="profile-value">
                    {s_tariff}
                </div>

            </div>


            <div class="profile-row">

                <div class="profile-label">
                    Статус
                </div>

                <div class="profile-value">
                    {s_status}
                </div>

            </div>


        </div>

    </section>


    <!-- ======================================================
         FAQ
    ====================================================== -->

    <section id="faq">

        <div class="section-head">

            <div>

                <div class="section-title">
                    Частые вопросы
                </div>

                <div class="section-subtitle">
                    Всё необходимое в одном месте
                </div>

            </div>

        </div>


        <div class="faq">


            <details>

                <summary>
                    Как подключить VPN?
                </summary>

                <div class="answer">

                    Нажмите «Подключиться» или выберите
                    Happ / INCY выше. Приложение получит
                    вашу персональную подписку автоматически.

                </div>

            </details>


            <details>

                <summary>
                    Где моя ссылка?
                </summary>

                <div class="answer">

                    Она находится в разделе «Ваша ссылка».
                    Нажмите на неё или кнопку копирования.

                </div>

            </details>


            <details>

                <summary>
                    Нужно ли каждый раз добавлять подписку?
                </summary>

                <div class="answer">

                    Нет. После добавления подписки приложение
                    сможет обновлять конфигурацию по вашей
                    персональной ссылке.

                </div>

            </details>


            <details>

                <summary>
                    Что делать, если VPN не подключается?
                </summary>

                <div class="answer">

                    Обновите подписку в VPN-клиенте и попробуйте
                    подключиться ещё раз. Если проблема остаётся,
                    обратитесь в Telegram-бот поддержки.

                </div>

            </details>


        </div>

    </section>


    <!-- ======================================================
         FOOTER
    ====================================================== -->

    <footer class="footer">

        <div>
            <span class="footer-brand">
                ☂️ ixxy VPN
            </span>
            • Premium network
        </div>

        <div>
            Ваш персональный VPN-доступ
        </div>

    </footer>


</div>


<!-- ==========================================================
     BOTTOM NAV
========================================================== -->

<nav class="bottom-nav">


    <button
        class="bottom-item active"
        type="button"
        onclick="scrollToSection('home', this)"
    >

        <span>⌂</span>
        <span>Главная</span>

    </button>


    <button
        class="bottom-item"
        type="button"
        onclick="scrollToSection('subscription', this)"
    >

        <span>◉</span>
        <span>Подписка</span>

    </button>


    <button
        class="bottom-item"
        type="button"
        onclick="scrollToSection('apps', this)"
    >

        <span>⚡</span>
        <span>Подключение</span>

    </button>


    <button
        class="bottom-item"
        type="button"
        onclick="scrollToSection('profile', this)"
    >

        <span>●</span>
        <span>Профиль</span>

    </button>


</nav>


<!-- ==========================================================
     TOAST
========================================================== -->

<div
    class="toast"
    id="toast"
>
    <span id="toastText">
        Готово
    </span>
</div>


<!-- ==========================================================
     JAVASCRIPT
========================================================== -->

<script>

/* ============================================================
   URLS
============================================================ */

const subscriptionUrl =
    '{js_subscription}';

const happUrl =
    '{js_happ}';

const incyUrl =
    '{js_incy}';

const pageUrl =
    '{js_page}';


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;


function showToast(message) {{

    const toast =
        document.getElementById("toast");

    const text =
        document.getElementById("toastText");

    if (!toast || !text) {{
        return;
    }}

    text.textContent = message;

    toast.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {{

        toast.classList.remove("show");

    }}, 2200);
}}


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
   COPY
============================================================ */

async function copySubscription() {{

    if (!subscriptionUrl) {{

        showToast(
            "Ссылка недоступна"
        );

        return;
    }}

    try {{

        await navigator.clipboard.writeText(
            subscriptionUrl
        );

        showToast(
            "✓ Ссылка скопирована"
        );

        return;

    }} catch (error) {{

        console.log(error);

    }}


    try {{

        const textarea =
            document.createElement(
                "textarea"
            );

        textarea.value =
            subscriptionUrl;

        textarea.style.position =
            "fixed";

        textarea.style.left =
            "-9999px";

        document.body.appendChild(
            textarea
        );

        textarea.focus();
        textarea.select();

        document.execCommand(
            "copy"
        );

        textarea.remove();

        showToast(
            "✓ Ссылка скопирована"
        );

    }} catch (error) {{

        showToast(
            "Не удалось скопировать"
        );
    }}
}}


/* ============================================================
   HAPP
============================================================ */

function openHapp() {{

    if (!subscriptionUrl) {{

        showToast(
            "Ссылка недоступна"
        );

        return;
    }}

    showToast(
        "🚀 Открываем Happ..."
    );

    setTimeout(() => {{

        window.location.href =
            happUrl;

    }}, 120);

}}


/* ============================================================
   INCY
============================================================ */

function openIncy() {{

    if (!subscriptionUrl) {{

        showToast(
            "Ссылка недоступна"
        );

        return;
    }}

    showToast(
        "⚡ Открываем INCY..."
    );

    setTimeout(() => {{

        window.location.href =
            incyUrl;

    }}, 120);

}}


/* ============================================================
   REFRESH
============================================================ */

function refreshPage() {{

    showToast(
        "↻ Обновляем данные..."
    );

    setTimeout(() => {{

        window.location.href =
            pageUrl
            + "?t="
            + Date.now();

    }}, 350);
}}


/* ============================================================
   NAVIGATION
============================================================ */

function scrollToSection(
    id,
    button
) {{

    const element =
        document.getElementById(id);

    if (!element) {{
        return;
    }}

    element.scrollIntoView({{
        behavior: "smooth",
        block: "start"
    }});

    document
        .querySelectorAll(
            ".bottom-item"
        )
        .forEach(item => {{
            item.classList.remove(
                "active"
            );
        }});

    if (button) {{
        button.classList.add(
            "active"
        );
    }}
}}


/* ============================================================
   PROGRESS ANIMATION
============================================================ */

window.addEventListener(
    "load",
    () => {{

        const bar =
            document.getElementById(
                "progressBar"
            );

        if (!bar) {{
            return;
        }}

        const width =
            bar.style.width;

        bar.style.width = "0%";

        setTimeout(() => {{

            bar.style.width =
                "{progress}%";

        }}, 180);

    }}
);


/* ============================================================
   LINK CLICK
============================================================ */

const linkElement =
    document.getElementById(
        "subscriptionLink"
    );

if (linkElement) {{

    linkElement.addEventListener(
        "click",
        copySubscription
    );

}}


/* ============================================================
   SCROLL ACTIVE NAV
============================================================ */

const sections = [
    "home",
    "subscription",
    "apps",
    "profile"
];


window.addEventListener(
    "scroll",
    () => {{

        let current =
            "home";

        const position =
            window.scrollY + 180;

        sections.forEach(id => {{

            const section =
                document.getElementById(
                    id
                );

            if (
                section &&
                section.offsetTop <= position
            ) {{
                current = id;
            }}

        }});

        const items =
            document.querySelectorAll(
                ".bottom-item"
            );

        items.forEach(
            item =>
                item.classList.remove(
                    "active"
                )
        );

        const index =
            sections.indexOf(
                current
            );

        if (
            index >= 0 &&
            items[index]
        ) {{
            items[index].classList.add(
                "active"
            );
        }}

    }},
    {{
        passive: true
    }}
);


/* ============================================================
   PREVENT DOUBLE TAP ZOOM
============================================================ */

let lastTouchEnd = 0;

document.addEventListener(
    "touchend",
    event => {{

        const now =
            Date.now();

        if (
            now - lastTouchEnd <= 300
        ) {{
            event.preventDefault();
        }}

        lastTouchEnd = now;

    }},
    {{
        passive: false
    }}
);

</script>

</body>

</html>
"""


# ============================================================
# SUBSCRIPTION PAGE
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    try:

        user = get_user(
            user_id
        )

    except Exception as error:

        print(
            "get_user error:",
            error
        )

        user = None


    # --------------------------------------------------------
    # SUBSCRIPTION
    # --------------------------------------------------------

    try:

        content = get_subscription_content(
            user_id
        )

    except Exception as error:

        print(
            "get_subscription_content error:",
            error
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


    # --------------------------------------------------------
    # USER DATA
    # --------------------------------------------------------

    user_data =
        read_user_data(user)

    user_data["user_id"] =
        user_id


    # --------------------------------------------------------
    # SUBSCRIPTION INFO
    # --------------------------------------------------------

    subscription_info =
        get_subscription_info(
            user_data
        )


    # --------------------------------------------------------
    # URLS
    # --------------------------------------------------------

    urls =
        get_urls(
            user_id
        )


    # --------------------------------------------------------
    # PAGE
    # --------------------------------------------------------

    page =
        premium_page(
            user_id,
            user_data,
            subscription_info,
            urls,
        )


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

    user_id =
        get_user_id_from_token(
            token
        )

    if user_id is None:
        abort(404)


    try:

        content =
            get_subscription_content(
                user_id
            )

    except Exception as error:

        print(
            "subscription error:",
            error
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
# ROOT
# ============================================================

@app.route("/")
def index():

    return r"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1,viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#06070b"
>

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
    min-height: 100dvh;

    display: flex;
    align-items: center;
    justify-content: center;

    padding: 22px;

    background:
        radial-gradient(
            circle at 0% 0%,
            rgba(124,92,255,.28),
            transparent 32%
        ),
        radial-gradient(
            circle at 100% 0%,
            rgba(0,210,255,.18),
            transparent 32%
        ),
        #06070b;

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}

.box {

    width: 100%;
    max-width: 450px;

    padding: 36px 24px;

    border-radius: 34px;

    background:
        rgba(17,19,28,.78);

    border:
        1px solid rgba(255,255,255,.09);

    box-shadow:
        0 35px 100px
        rgba(0,0,0,.55);

    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);

    text-align: center;
}

.logo {

    width: 88px;
    height: 88px;

    margin:
        0 auto 22px;

    display: flex;

    align-items: center;
    justify-content: center;

    border-radius: 28px;

    background:
        linear-gradient(
            145deg,
            #765cff,
            #a74cff,
            #ff3db5
        );

    font-size: 43px;

    box-shadow:
        0 20px 65px
        rgba(120,80,255,.4);
}

h1 {

    margin: 0;

    font-size: 31px;

    font-weight: 950;

    letter-spacing: -1px;
}

p {

    margin-top: 9px;

    color: #9296a5;

    font-size: 13px;

    line-height: 1.55;
}

.badge {

    margin-top: 23px;

    display: inline-flex;

    align-items: center;

    gap: 7px;

    padding: 9px 13px;

    border-radius: 999px;

    background:
        rgba(53,230,154,.08);

    border:
        1px solid
        rgba(53,230,154,.13);

    color: #8deebd;

    font-size: 10px;

    font-weight: 850;
}

.dot {

    width: 7px;
    height: 7px;

    border-radius: 50%;

    background:
        #35e69a;

    box-shadow:
        0 0 12px
        rgba(53,230,154,.8);
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
        Premium VPN-сервис с персональными
        конфигурациями и быстрым подключением.
    </p>

    <div class="badge">

        <span class="dot"></span>

        Система работает

    </div>

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
                "no-cache, no-store, must-revalidate",

        },
    )


# ============================================================
# FAVICON
# ============================================================

@app.route("/favicon.ico")
def favicon():

    return Response(
        "",
        status=204,
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return Response(

        """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
        <meta charset="UTF-8">
        <meta
            name="viewport"
            content="width=device-width,initial-scale=1"
        >
        <title>ixxy VPN</title>
        <style>
        body {
            margin:0;
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#06070b;
            color:white;
            font-family:-apple-system,BlinkMacSystemFont,
            "Segoe UI",sans-serif;
            text-align:center;
        }
        .box {
            padding:30px;
            max-width:400px;
        }
        h1 {
            font-size:55px;
            margin:0;
        }
        p {
            color:#8f93a0;
            line-height:1.6;
        }
        a {
            display:inline-flex;
            margin-top:18px;
            padding:13px 20px;
            border-radius:15px;
            background:#765cff;
            color:white;
            text-decoration:none;
            font-weight:800;
        }
        </style>
        </head>
        <body>
        <div class="box">
            <h1>404</h1>
            <p>Страница ixxy VPN не найдена.</p>
            <a href="/">На главную</a>
        </div>
        </body>
        </html>
        """,

        status=404,

        mimetype="text/html",
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