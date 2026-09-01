import os
import html
import shutil
import subprocess
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, abort, make_response

from database import (
    get_user,
    get_subscription_content,
)

app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================

APP_VERSION = "ixxy-2026.09.01"

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy"
).strip()

TELEGRAM_URL = os.getenv(
    "TELEGRAM_URL",
    "https://t.me/orelvpntopbot"
)

HPWNR_PATH = os.getenv(
    "HPWNR_PATH",
    "bin/hpwnr"
)

# ============================================================
# CACHE
# ============================================================

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# ESCAPE
# ============================================================

def esc(value):
    return html.escape(str(value or ""))


# ============================================================
# DATABASE
# ============================================================

def user_value(user, index, default=""):
    try:
        if user and len(user) > index:
            value = user[index]

            if value is not None:
                return value

    except Exception:
        pass

    return default


def get_real_user(user_id):

    try:
        return get_user(user_id)

    except Exception as e:

        print(
            "[WEB] Ошибка PostgreSQL get_user:",
            repr(e)
        )

        return None


def get_real_subscription(user_id):

    try:
        return get_subscription_content(user_id) or ""

    except Exception as e:

        print(
            "[WEB] Ошибка PostgreSQL subscription_content:",
            repr(e)
        )

        return ""


# ============================================================
# TOKEN
# ============================================================

def get_token(user_id):

    return f"{SUBSCRIPTION_PREFIX}{user_id}"


def get_user_id_from_token(token):

    if not token:
        return None

    token = str(token).strip()

    if not token.startswith(
        SUBSCRIPTION_PREFIX
    ):
        return None

    user_id = token[
        len(SUBSCRIPTION_PREFIX):
    ]

    if not user_id.isdigit():
        return None

    try:
        return int(user_id)

    except Exception:
        return None


# ============================================================
# HPWNR
# ============================================================

def find_hpwnr():

    candidates = [

        HPWNR_PATH,

        "./bin/hpwnr",

        "bin/hpwnr",

        "./hpwnr",

        "hpwnr",

        "/opt/render/project/src/bin/hpwnr",

        "/opt/render/project/src/hpwnr",

        "/usr/local/bin/hpwnr",

        "/usr/bin/hpwnr",

        "/opt/hpwnr",

        "/opt/bin/hpwnr",
    ]

    for candidate in candidates:

        if not candidate:
            continue

        try:

            if (
                os.path.isfile(candidate)
                and os.access(
                    candidate,
                    os.X_OK
                )
            ):

                return candidate

        except Exception:
            pass

        try:

            found = shutil.which(
                candidate
            )

            if found:
                return found

        except Exception:
            pass

    return None


# ============================================================
# HAPP CRYPT5
# ============================================================

def generate_happ_crypt5(
    subscription_url
):

    if not subscription_url:
        return ""

    hpwnr = find_hpwnr()

    if not hpwnr:

        print(
            "[HAPP] ❌ hpwnr не найден"
        )

        return ""

    try:

        print(
            "[HAPP] ================================="
        )

        print(
            "[HAPP] hpwnr:",
            hpwnr
        )

        print(
            "[HAPP] URL:",
            subscription_url
        )

        # ====================================================
        # ОСНОВНАЯ КОМАНДА
        #
        # hpwnr <URL> crypt5
        # ====================================================

        commands = [

            [
                hpwnr,
                subscription_url,
                "crypt5",
            ],

            [
                hpwnr,
                "crypt5",
                subscription_url,
            ],
        ]

        for command in commands:

            print(
                "[HAPP] Команда:",
                command
            )

            try:

                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )

            except Exception as e:

                print(
                    "[HAPP] Ошибка запуска:",
                    repr(e)
                )

                continue

            stdout = (
                result.stdout or ""
            ).strip()

            stderr = (
                result.stderr or ""
            ).strip()

            print(
                "[HAPP] returncode:",
                result.returncode
            )

            if stdout:

                print(
                    "[HAPP] stdout:",
                    stdout[:2000]
                )

            if stderr:

                print(
                    "[HAPP] stderr:",
                    stderr[:2000]
                )

            # =================================================
            # ИЩЕМ CRYPT5
            # =================================================

            for line in stdout.splitlines():

                line = line.strip()

                if line.startswith(
                    "happ://crypt5/"
                ):

                    print(
                        "[HAPP] ✅ Crypt5 найден"
                    )

                    print(
                        "[HAPP] ================================="
                    )

                    return line

            # =================================================
            # CRYPT5 МОЖЕТ БЫТЬ ВНУТРИ СТРОКИ
            # =================================================

            marker = "happ://crypt5/"

            position = stdout.find(
                marker
            )

            if position >= 0:

                value = (
                    stdout[position:]
                    .strip()
                )

                value = (
                    value
                    .splitlines()[0]
                    .strip()
                )

                value = value.strip(
                    "\"'"
                )

                if value.startswith(
                    marker
                ):

                    print(
                        "[HAPP] ✅ Crypt5 найден внутри вывода"
                    )

                    return value

        print(
            "[HAPP] ❌ Crypt5 создать не удалось"
        )

        print(
            "[HAPP] ================================="
        )

        return ""

    except subprocess.TimeoutExpired:

        print(
            "[HAPP] ❌ hpwnr timeout"
        )

        return ""

    except Exception as e:

        print(
            "[HAPP] ❌ Ошибка:",
            repr(e)
        )

        return ""


# ============================================================
# URLS
# ============================================================

def build_happ_url(
    subscription_url
):

    crypt5 = generate_happ_crypt5(
        subscription_url
    )

    if crypt5:

        return crypt5

    # ========================================================
    # FALLBACK
    # ========================================================

    return (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )


def build_incy_url(
    subscription_url
):

    return (
        "incy://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )


def get_urls(user_id):

    token = get_token(
        user_id
    )

    page_url = (
        f"{PUBLIC_SITE_URL}/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    happ_url = build_happ_url(
        subscription_url
    )

    incy_url = build_incy_url(
        subscription_url
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

def parse_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = [

        "%Y-%m-%d",

        "%Y-%m-%d %H:%M",

        "%Y-%m-%d %H:%M:%S",

        "%d.%m.%Y",

        "%d.%m.%Y %H:%M",

        "%d.%m.%Y %H:%M:%S",
    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                value,
                fmt
            )

        except Exception:
            pass

    try:

        return datetime.fromisoformat(
            value.replace(
                "Z",
                ""
            )
        )

    except Exception:

        return None


def format_date(value):

    if not value:
        return "Не указана"

    date = parse_date(value)

    if not date:
        return str(value)

    return date.strftime(
        "%d.%m.%Y"
    )


def days_left(value):

    date = parse_date(value)

    if not date:
        return 0

    return max(
        0,
        (
            date.date()
            - datetime.now().date()
        ).days
    )


def subscription_status(value):

    if not value:

        return (
            "Неактивна",
            "expired"
        )

    date = parse_date(value)

    if not date:

        return (
            "Активна",
            "active"
        )

    if (
        date.date()
        >= datetime.now().date()
    ):

        return (
            "Активна",
            "active"
        )

    return (
        "Истекла",
        "expired"
    )


# ============================================================
# PAGE
# ============================================================

def render_page(user_id):

    # ========================================================
    # REAL USER
    # ========================================================

    user = get_real_user(
        user_id
    )

    if not user:
        abort(404)

    real_user_id = user_value(
        user,
        0,
        user_id
    )

    username = user_value(
        user,
        1,
        ""
    )

    first_name = user_value(
        user,
        2,
        ""
    )

    subscription = user_value(
        user,
        3,
        "none"
    )

    subscription_until = user_value(
        user,
        4,
        ""
    )

    subscription_link = user_value(
        user,
        5,
        ""
    )

    # ========================================================
    # NAME
    # ========================================================

    display_name = (
        first_name
        or username
        or f"ID {real_user_id}"
    )

    # ========================================================
    # TARIFF
    # ========================================================

    if subscription == "vip":

        tariff_name = "👑 ixxy VPN"

    elif subscription == "trial":

        tariff_name = "🎁 Пробный период"

    elif subscription in (
        "",
        "none",
        None,
    ):

        tariff_name = "Нет подписки"

    else:

        tariff_name = str(
            subscription
        )

    # ========================================================
    # STATUS
    # ========================================================

    status_text, status_class = (
        subscription_status(
            subscription_until
        )
    )

    remaining_days = days_left(
        subscription_until
    )

    # ========================================================
    # REAL SUBSCRIPTION
    #
    # Мы только проверяем наличие.
    #
    # Содержимое серверов здесь НИКОГДА
    # не выводится.
    # ========================================================

    real_content = (
        get_real_subscription(
            real_user_id
        )
    )

    subscription_ready = bool(
        real_content.strip()
    )

    # ========================================================
    # PERSONAL URL
    # ========================================================

    token = get_token(
        real_user_id
    )

    page_url = (
        f"{PUBLIC_SITE_URL}/s/{token}"
    )

    real_subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    # ========================================================
    # HAPP
    # ========================================================

    happ_url = build_happ_url(
        real_subscription_url
    )

    # ========================================================
    # INCY
    # ========================================================

    incy_url = build_incy_url(
        real_subscription_url
    )

    # ========================================================
    # PROGRESS
    # ========================================================

    if remaining_days <= 0:

        progress = 0

    elif remaining_days >= 30:

        progress = 100

    else:

        progress = round(
            (
                remaining_days
                / 30
            )
            * 100
        )

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
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1"
>

<meta
    name="theme-color"
    content="#08060e"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<title>
ixxy VPN — {esc(display_name)}
</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    background: #08060e;
}}

body {{
    margin: 0;
    min-height: 100vh;

    color: #fff;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(126,72,255,.25),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 15%,
            rgba(69,103,255,.18),
            transparent 30%
        ),
        #08060e;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        Arial,
        sans-serif;
}}

a {{
    color: inherit;
    text-decoration: none;
}}

button {{
    font: inherit;
}}

.page {{
    width: 100%;
    max-width: 760px;

    margin: auto;

    padding:
        22px
        18px
        50px;
}}

.top {{
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 18px;
}}

.brand {{
    display: flex;
    align-items: center;

    gap: 11px;
}}

.logo {{
    width: 46px;
    height: 46px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    background:
        linear-gradient(
            145deg,
            #ad76ff,
            #572dcc
        );

    font-size: 17px;
    font-weight: 950;

    box-shadow:
        0 12px 35px
        rgba(109,58,240,.4);
}}

.brand-title {{
    font-size: 18px;
    font-weight: 950;
}}

.brand-sub {{
    margin-top: 2px;

    color:
        rgba(255,255,255,.4);

    font-size: 10px;

    text-transform:
        uppercase;

    letter-spacing:
        1px;
}}

.status {{
    display: flex;
    align-items: center;

    gap: 7px;

    padding:
        9px 12px;

    border-radius: 999px;

    background:
        rgba(255,255,255,.055);

    border:
        1px solid
        rgba(255,255,255,.08);

    font-size: 11px;
    font-weight: 900;
}}

.dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background:
        #ff4d65;
}}

.active .dot {{
    background:
        #5cffaa;

    box-shadow:
        0 0 13px
        rgba(92,255,170,.8);
}}

.hero {{
    padding:
        30px 23px 24px;

    border-radius: 30px;

    border:
        1px solid
        rgba(255,255,255,.1);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.095),
            rgba(255,255,255,.035)
        );

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.35);

    backdrop-filter:
        blur(25px);
}}

.eyebrow {{
    color:
        #ae8bff;

    font-size: 10px;
    font-weight: 950;

    letter-spacing:
        2px;
}}

h1 {{
    margin:
        12px 0 0;

    font-size:
        clamp(
            36px,
            10vw,
            58px
        );

    line-height: .94;

    letter-spacing:
        -3px;
}}

.desc {{
    margin-top: 16px;

    color:
        rgba(255,255,255,.52);

    font-size: 13px;

    line-height: 1.55;
}}

.user {{
    display: flex;
    align-items: center;

    gap: 10px;

    margin-top: 22px;

    font-size: 13px;
}}

.avatar {{
    width: 35px;
    height: 35px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 50%;

    background:
        linear-gradient(
            145deg,
            #9060ff,
            #3d207d
        );

    font-weight: 950;
}}

.connect-main {{
    width: 100%;
    min-height: 68px;

    margin-top: 24px;

    border: 0;

    border-radius: 20px;

    color: white;

    background:
        linear-gradient(
            135deg,
            #a16eff,
            #693be2,
            #4b24ad
        );

    box-shadow:
        0 16px 42px
        rgba(103,57,227,.38);

    cursor: pointer;
}}

.connect-main strong {{
    display: block;

    font-size: 16px;
}}

.connect-main small {{
    display: block;

    margin-top: 4px;

    color:
        rgba(255,255,255,.65);

    font-size: 10px;
}}

.cards {{
    display: grid;

    grid-template-columns:
        repeat(2, 1fr);

    gap: 11px;

    margin-top: 12px;
}}

.card {{
    padding: 19px;

    min-height: 115px;

    border-radius: 21px;

    border:
        1px solid
        rgba(255,255,255,.07);

    background:
        rgba(255,255,255,.045);
}}

.icon {{
    margin-bottom: 14px;

    font-size: 19px;
}}

.label {{
    color:
        rgba(255,255,255,.38);

    font-size: 9px;
    font-weight: 800;

    letter-spacing: 1px;

    text-transform:
        uppercase;
}}

.value {{
    margin-top: 6px;

    font-size: 15px;
    font-weight: 950;

    word-break:
        break-word;
}}

.progress-card {{
    margin-top: 12px;

    padding: 20px;

    border-radius: 21px;

    border:
        1px solid
        rgba(255,255,255,.07);

    background:
        rgba(255,255,255,.045);
}}

.progress-top {{
    display: flex;

    justify-content:
        space-between;

    margin-bottom: 12px;
}}

.progress-title {{
    font-size: 13px;
    font-weight: 900;
}}

.progress-days {{
    color:
        #ad89ff;

    font-size: 11px;
    font-weight: 900;
}}

.progress {{
    height: 8px;

    overflow: hidden;

    border-radius: 999px;

    background:
        rgba(255,255,255,.07);
}}

.bar {{
    width: {progress}%;

    height: 100%;

    border-radius: inherit;

    background:
        linear-gradient(
            90deg,
            #6938dd,
            #ae80ff
        );
}}

.section {{
    margin-top: 25px;
}}

.section-title {{
    margin-bottom: 11px;

    font-size: 17px;
    font-weight: 950;
}}

.option {{
    display: flex;
    align-items: center;

    gap: 14px;

    min-height: 72px;

    margin-bottom: 10px;

    padding: 14px;

    border-radius: 20px;

    border:
        1px solid
        rgba(255,255,255,.07);

    background:
        rgba(255,255,255,.045);

    cursor: pointer;
}}

.option-icon {{
    width: 44px;
    height: 44px;

    flex: 0 0 auto;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 14px;

    background:
        rgba(255,255,255,.07);

    font-size: 20px;
}}

.option-main {{
    flex: 1;
}}

.option-title {{
    font-size: 13px;
    font-weight: 900;
}}

.option-desc {{
    margin-top: 4px;

    color:
        rgba(255,255,255,.4);

    font-size: 10px;
}}

.arrow {{
    color:
        rgba(255,255,255,.3);

    font-size: 21px;
}}

.subscription {{
    padding: 19px;

    border-radius: 22px;

    border:
        1px solid
        rgba(255,255,255,.08);

    background:
        linear-gradient(
            145deg,
            rgba(128,76,255,.11),
            rgba(255,255,255,.035)
        );
}}

.subscription-label {{
    color:
        rgba(255,255,255,.38);

    font-size: 9px;

    letter-spacing: 1px;

    font-weight: 900;

    text-transform:
        uppercase;
}}

.url {{
    display: flex;
    align-items: center;

    gap: 8px;

    margin-top: 10px;
}}

.url-text {{
    min-width: 0;
    flex: 1;

    padding: 13px;

    border-radius: 13px;

    background:
        rgba(0,0,0,.25);

    color:
        rgba(255,255,255,.67);

    font-size: 10px;

    overflow: hidden;

    white-space:
        nowrap;

    text-overflow:
        ellipsis;
}}

.copy {{
    width: 48px;
    height: 48px;

    border: 0;

    border-radius: 14px;

    background:
        rgba(255,255,255,.08);

    color: white;

    cursor: pointer;

    font-size: 17px;
}}

.security {{
    margin-top: 18px;

    padding: 16px;

    display: flex;

    gap: 12px;

    border-radius: 19px;

    border:
        1px solid
        rgba(92,255,170,.08);

    background:
        rgba(92,255,170,.03);
}}

.security-icon {{
    font-size: 18px;
}}

.security-title {{
    font-size: 11px;
    font-weight: 900;
}}

.security-text {{
    margin-top: 4px;

    color:
        rgba(255,255,255,.36);

    font-size: 9px;

    line-height: 1.5;
}}

.support {{
    display: flex;
    align-items: center;
    justify-content: center;

    min-height: 57px;

    margin-top: 12px;

    border-radius: 19px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        rgba(255,255,255,.07);

    font-size: 12px;
    font-weight: 900;
}}

.footer {{
    margin-top: 25px;

    text-align: center;

    color:
        rgba(255,255,255,.2);

    font-size: 9px;

    line-height: 1.7;
}}

.toast {{
    position: fixed;

    left: 50%;
    bottom: 25px;

    transform:
        translate(-50%, 20px);

    padding:
        12px 17px;

    border-radius: 999px;

    background:
        rgba(25,20,35,.9);

    border:
        1px solid
        rgba(255,255,255,.1);

    color: white;

    font-size: 11px;
    font-weight: 900;

    opacity: 0;

    pointer-events:
        none;

    transition: .25s;
}}

.toast.show {{
    opacity: 1;

    transform:
        translate(-50%, 0);
}}

@media (min-width: 700px) {{

    .page {{
        padding-top: 45px;
    }}

    .hero {{
        padding: 42px;
    }}

    .cards {{
        grid-template-columns:
            repeat(4, 1fr);
    }}

}}

</style>

</head>

<body>

<main class="page">

<header class="top">

    <div class="brand">

        <div class="logo">
            IX
        </div>

        <div>

            <div class="brand-title">
                ixxy VPN
            </div>

            <div class="brand-sub">
                Private access
            </div>

        </div>

    </div>

    <div class="status {status_class}">

        <span class="dot"></span>

        {esc(status_text)}

    </div>

</header>


<section class="hero">

    <div class="eyebrow">
        PERSONAL VPN
    </div>

    <h1>
        Твоя<br>
        подписка.
    </h1>

    <div class="desc">

        Всё управление подключением
        в одном месте. Конфигурация серверов
        не отображается в интерфейсе.

    </div>

    <div class="user">

        <div class="avatar">
            {esc(str(display_name)[:1]).upper()}
        </div>

        <div>
            {esc(display_name)}
        </div>

    </div>


    <button
        class="connect-main"
        onclick="openHapp()"
    >

        <strong>
            ⚡ Подключить в Happ
        </strong>

        <small>
            Персональный импорт подписки
        </small>

    </button>

</section>


<section class="cards">

    <div class="card">

        <div class="icon">
            👑
        </div>

        <div class="label">
            Тариф
        </div>

        <div class="value">
            {esc(tariff_name)}
        </div>

    </div>


    <div class="card">

        <div class="icon">
            📅
        </div>

        <div class="label">
            До
        </div>

        <div class="value">
            {esc(format_date(subscription_until))}
        </div>

    </div>


    <div class="card">

        <div class="icon">
            ⏳
        </div>

        <div class="label">
            Осталось
        </div>

        <div class="value">
            {remaining_days} дн.
        </div>

    </div>


    <div class="card">

        <div class="icon">
            🔐
        </div>

        <div class="label">
            Подписка
        </div>

        <div class="value">
            {"Готова" if subscription_ready else "Не готова"}
        </div>

    </div>

</section>


<section class="progress-card">

    <div class="progress-top">

        <div class="progress-title">
            Состояние подписки
        </div>

        <div class="progress-days">
            {remaining_days} дней
        </div>

    </div>

    <div class="progress">

        <div class="bar"></div>

    </div>

</section>


<section class="section">

    <div class="section-title">
        Подключение
    </div>


    <div
        class="option"
        onclick="openHapp()"
    >

        <div class="option-icon">
            ⚡
        </div>

        <div class="option-main">

            <div class="option-title">
                Happ
            </div>

            <div class="option-desc">
                Открыть персональный импорт
            </div>

        </div>

        <div class="arrow">
            ›
        </div>

    </div>


    <div
        class="option"
        onclick="openIncy()"
    >

        <div class="option-icon">
            🟣
        </div>

        <div class="option-main">

            <div class="option-title">
                INCY
            </div>

            <div class="option-desc">
                Добавить персональную подписку
            </div>

        </div>

        <div class="arrow">
            ›
        </div>

    </div>

</section>


<section class="section">

    <div class="section-title">
        Персональная подписка
    </div>

    <div class="subscription">

        <div class="subscription-label">
            Subscription URL
        </div>

        <div class="url">

            <div
                class="url-text"
                id="url"
            >
                {esc(real_subscription_url)}
            </div>

            <button
                class="copy"
                onclick="copySubscription()"
            >
                ⧉
            </button>

        </div>

    </div>

</section>


<section class="section">

    <div class="section-title">
        Как подключиться
    </div>


    <div class="option">

        <div class="option-icon">
            01
        </div>

        <div class="option-main">

            <div class="option-title">
                Открой Happ
            </div>

            <div class="option-desc">
                Нажми кнопку подключения выше.
            </div>

        </div>

    </div>


    <div class="option">

        <div class="option-icon">
            02
        </div>

        <div class="option-main">

            <div class="option-title">
                Импортируй подписку
            </div>

            <div class="option-desc">
                Подтверди добавление конфигурации.
            </div>

        </div>

    </div>


    <div class="option">

        <div class="option-icon">
            03
        </div>

        <div class="option-main">

            <div class="option-title">
                Подключись
            </div>

            <div class="option-desc">
                Выбери подключение и включи VPN.
            </div>

        </div>

    </div>

</section>


<a
    class="support"
    href="{esc(TELEGRAM_URL)}"
    target="_blank"
    rel="noopener"
>
    💬 Поддержка ixxy VPN
</a>


<div class="security">

    <div class="security-icon">
        🛡️
    </div>

    <div>

        <div class="security-title">
            Серверная конфигурация скрыта
        </div>

        <div class="security-text">
            Интерфейс не показывает содержимое
            подписки, UUID, адреса серверов или
            другие параметры конфигурации.
            Клиент получает подписку через
            персональный URL.
        </div>

    </div>

</div>


<footer class="footer">

    ixxy VPN · Private access<br>

    ID: {esc(real_user_id)} · {esc(APP_VERSION)}

</footer>

</main>


<div
    class="toast"
    id="toast"
>
    Готово
</div>


<script>

const HAPP_URL = {happ_url!r};

const INCY_URL = {incy_url!r};

const SUB_URL = {real_subscription_url!r};


function toast(text) {{

    const el =
        document.getElementById(
            "toast"
        );

    el.textContent = text;

    el.classList.add(
        "show"
    );

    clearTimeout(
        window.toastTimer
    );

    window.toastTimer =
        setTimeout(
            () => {{

                el.classList.remove(
                    "show"
                );

            }},
            1800
        );
}}


function openHapp() {{

    toast(
        "Открываем Happ…"
    );

    window.location.href =
        HAPP_URL;

}}


function openIncy() {{

    toast(
        "Открываем INCY…"
    );

    window.location.href =
        INCY_URL;

}}


async function copySubscription() {{

    try {{

        if (
            navigator.clipboard &&
            window.isSecureContext
        ) {{

            await navigator.clipboard.writeText(
                SUB_URL
            );

        }} else {{

            const input =
                document.createElement(
                    "textarea"
                );

            input.value =
                SUB_URL;

            input.style.position =
                "fixed";

            input.style.left =
                "-9999px";

            document.body.appendChild(
                input
            );

            input.focus();

            input.select();

            document.execCommand(
                "copy"
            );

            input.remove();

        }}

        toast(
            "Ссылка скопирована"
        );

    }} catch (error) {{

        toast(
            "Не удалось скопировать"
        );

    }}

}}

</script>

</body>

</html>
"""

    response = make_response(
        page
    )

    for key, value in NO_CACHE_HEADERS.items():

        response.headers[
            key
        ] = value

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    return response


# ============================================================
# /s/<TOKEN>
# ============================================================

@app.route(
    "/s/<token>"
)
def subscription_page(token):

    user_id = get_user_id_from_token(
        token
    )

    if not user_id:
        abort(404)

    user = get_real_user(
        user_id
    )

    if not user:
        abort(404)

    return render_page(
        user_id
    )


# ============================================================
# /sub/<TOKEN>
#
# РЕАЛЬНАЯ ПОДПИСКА ИЗ POSTGRESQL
#
# Серверные настройки здесь не
# отображаются на сайте.
# Они выдаются только клиенту,
# который использует subscription URL.
# ============================================================

@app.route(
    "/sub/<token>"
)
def subscription_endpoint(token):

    user_id = get_user_id_from_token(
        token
    )

    if not user_id:
        abort(404)

    user = get_real_user(
        user_id
    )

    if not user:
        abort(404)

    content = get_real_subscription(
        user_id
    )

    if not content:

        return Response(
            "Subscription unavailable",
            status=404,
            mimetype="text/plain",
            headers=NO_CACHE_HEADERS,
        )

    response = Response(
        content,
        status=200,
        mimetype="text/plain",
    )

    for key, value in NO_CACHE_HEADERS.items():

        response.headers[
            key
        ] = value

    return response


# ============================================================
# HAPP TEST
# ============================================================

@app.route(
    "/happ-test/<token>"
)
def happ_test(token):

    user_id = get_user_id_from_token(
        token
    )

    if not user_id:
        abort(404)

    user = get_real_user(
        user_id
    )

    if not user:
        abort(404)

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    happ_url = build_happ_url(
        subscription_url
    )

    response = Response(
        happ_url,
        status=200,
        mimetype="text/plain",
    )

    for key, value in NO_CACHE_HEADERS.items():

        response.headers[
            key
        ] = value

    return response


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    response = make_response({

        "service":
            "ixxy VPN",

        "status":
            "ok",

        "version":
            APP_VERSION,
    })

    for key, value in NO_CACHE_HEADERS.items():

        response.headers[
            key
        ] = value

    return response


# ============================================================
# ROOT
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
    content="width=device-width,
    initial-scale=1"
>

<meta
    name="theme-color"
    content="#08060e"
>

<title>
ixxy VPN
</title>

<style>

body {

    margin: 0;

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;

    color: white;

    background:

        radial-gradient(
            circle at 50% 0%,
            rgba(130,75,255,.25),
            transparent 40%
        ),

        #08060e;

    font-family:

        -apple-system,
        BlinkMacSystemFont,
        Arial,
        sans-serif;
}

.card {

    width: 100%;

    max-width: 470px;

    padding: 45px 28px;

    text-align: center;

    border-radius: 30px;

    border:
        1px solid
        rgba(255,255,255,.09);

    background:
        rgba(255,255,255,.05);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.4);
}

.logo {

    width: 70px;
    height: 70px;

    margin: auto;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 22px;

    background:

        linear-gradient(
            145deg,
            #ad76ff,
            #572dcc
        );

    font-size: 23px;

    font-weight: 950;
}

h1 {

    margin:
        22px 0 8px;

    font-size: 36px;
}

p {

    color:
        rgba(255,255,255,.42);

    line-height: 1.55;
}

</style>

</head>

<body>

<div class="card">

    <div class="logo">
        IX
    </div>

    <h1>
        ixxy VPN
    </h1>

    <p>
        Веб-сервис работает.
        Используй персональную ссылку
        подписки для входа.
    </p>

</div>

</body>

</html>
"""


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    response = make_response(
        """
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1"
>

<meta
    name="theme-color"
    content="#08060e"
>

<title>
ixxy VPN — 404
</title>

<style>

body {

    margin: 0;

    min-height: 100vh;

    display: flex;

    align-items: center;

    justify-content: center;

    background:
        #08060e;

    color: white;

    font-family:

        -apple-system,
        BlinkMacSystemFont,
        Arial,
        sans-serif;
}

.box {

    padding: 40px;

    text-align: center;

    border-radius: 30px;

    background:
        rgba(255,255,255,.05);

    border:
        1px solid
        rgba(255,255,255,.08);
}

.code {

    font-size: 70px;

    font-weight: 950;
}

p {

    color:
        rgba(255,255,255,.4);
}

</style>

</head>

<body>

<div class="box">

    <div class="code">
        404
    </div>

    <p>
        Страница не найдена.
    </p>

</div>

</body>

</html>
        """,
        404
    )

    for key, value in NO_CACHE_HEADERS.items():

        response.headers[
            key
        ] = value

    return response


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
        debug=False,
    )