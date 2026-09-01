import os
import html
import shutil
import subprocess
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, abort, make_response

from database import (
    get_subscription_content,
    get_user,
)

# ============================================================
# IXXY VPN — WEB
# ============================================================

app = Flask(__name__)

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

# ============================================================
# CACHE
# ============================================================

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

# ============================================================
# HAPP / CRYPT5
# ============================================================

HPWNR_PATH = os.getenv("HPWNR_PATH", "bin/hpwnr")


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
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
        except Exception:
            pass

        try:
            found = shutil.which(candidate)
            if found:
                return found
        except Exception:
            pass

    return None


def generate_happ_crypt5(subscription_url):
    """
    Создаёт happ://crypt5/... через hpwnr.

    Если hpwnr отсутствует или не работает,
    используется безопасный fallback happ://add/...
    """

    if not subscription_url:
        return ""

    hpwnr = find_hpwnr()

    if not hpwnr:
        print("[HAPP] hpwnr НЕ НАЙДЕН")
        return ""

    try:
        print("[HAPP] Используется:", hpwnr)
        print("[HAPP] Генерация Crypt5...")

        result = subprocess.run(
            [hpwnr, subscription_url],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        print("[HAPP] returncode:", result.returncode)

        if stdout:
            print("[HAPP] stdout:", stdout[:500])

        if stderr:
            print("[HAPP] stderr:", stderr[:500])

        if result.returncode != 0:
            return ""

        for line in stdout.splitlines():
            line = line.strip()

            if line.startswith("happ://crypt5/"):
                print("[HAPP] Crypt5 успешно создан")
                return line

        pos = stdout.find("happ://crypt5/")

        if pos >= 0:
            value = stdout[pos:].split()[0].strip()

            if value.startswith("happ://crypt5/"):
                return value

        return ""

    except subprocess.TimeoutExpired:
        print("[HAPP] hpwnr timeout")
        return ""

    except Exception as e:
        print("[HAPP] ошибка:", repr(e))
        return ""


# ============================================================
# TOKENS
# ============================================================

def get_user_id_from_token(token):
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


# ============================================================
# URLS
# ============================================================

def get_urls(user_id):
    token = get_token(user_id)

    page_url = f"{PUBLIC_SITE_URL}/s/{token}"

    subscription_url = f"{PUBLIC_SITE_URL}/sub/{token}"

    happ_url = generate_happ_crypt5(subscription_url)

    if not happ_url:
        happ_url = "happ://add/" + quote(
            subscription_url,
            safe=""
        )

    incy_url = "incy://add/" + quote(
        subscription_url,
        safe=""
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

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass

    try:
        return datetime.fromisoformat(
            value.replace("Z", "")
        )
    except Exception:
        return None


def format_date(value):
    if not value:
        return "Не указана"

    date = parse_subscription_date(value)

    if not date:
        return str(value)

    return date.strftime("%d.%m.%Y")


def get_subscription_status(user):
    if not user:
        return "Неактивна", "expired"

    until = None

    if isinstance(user, dict):
        until = user.get("subscription_until")

    if not until:
        return "Неактивна", "expired"

    date = parse_subscription_date(until)

    if not date:
        return "Активна", "active"

    if date > datetime.now():
        return "Активна", "active"

    return "Истекла", "expired"


def get_days_left(user):
    if not user or not isinstance(user, dict):
        return 0

    until = user.get("subscription_until")

    if not until:
        return 0

    date = parse_subscription_date(until)

    if not date:
        return 0

    delta = date - datetime.now()

    return max(0, delta.days)


# ============================================================
# DATABASE
# ============================================================

def load_user_data(user_id):
    user = get_user(user_id)

    content = ""

    try:
        content = get_subscription_content(user_id) or ""
    except Exception as e:
        print(
            "[SUB] Ошибка получения subscription_content:",
            repr(e)
        )

    return user, content


# ============================================================
# HELPERS
# ============================================================

def esc(value):
    return html.escape(str(value or ""))


def get_subscription_name(user):
    if not isinstance(user, dict):
        return "ixxy VPN"

    value = (
        user.get("subscription")
        or user.get("tariff")
        or "ixxy VPN"
    )

    if str(value).strip().lower() in (
        "none",
        "free",
        "default",
        ""
    ):
        return "ixxy VPN"

    return str(value)


def get_username(user):
    if not isinstance(user, dict):
        return ""

    first_name = user.get("first_name") or ""
    username = user.get("username") or ""

    if first_name:
        return str(first_name)

    if username:
        return "@" + str(username).lstrip("@")

    return ""


def get_subscription_content_clean(content):
    """
    Возвращает содержимое подписки как текст.
    Никаких серверов в HTML страницы не выводится.
    """

    if content is None:
        return ""

    if isinstance(content, bytes):
        try:
            return content.decode("utf-8")
        except Exception:
            return content.decode(
                "utf-8",
                errors="ignore"
            )

    return str(content)


# ============================================================
# PREMIUM PAGE
# ============================================================

def render_subscription_page(user_id):

    user, subscription_content = load_user_data(user_id)

    token = get_token(user_id)

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    status_text, status_class = get_subscription_status(user)

    days_left = get_days_left(user)

    subscription_name = get_subscription_name(user)

    username = get_username(user)

    if not username:
        username = "Пользователь"

    if isinstance(user, dict):
        until_raw = user.get(
            "subscription_until",
            ""
        )
    else:
        until_raw = ""

    until = format_date(until_raw)

    active = status_class == "active"

    # Прогресс визуально ограничиваем.
    # Он нужен только для интерфейса и не меняет подписку.
    progress = min(
        100,
        max(
            5 if active else 0,
            min(days_left, 30) / 30 * 100
        )
    )

    progress = round(progress)

    # Важно:
    # subscription_content НЕ вставляется в HTML.
    # Серверы и конфигурация остаются скрыты.
    has_subscription = bool(
        get_subscription_content_clean(
            subscription_content
        ).strip()
    )

    subscription_ready_text = (
        "Подписка готова"
        if has_subscription
        else "Подписка ожидает настройки"
    )

    html_page = f"""
<!DOCTYPE html>
<html lang="ru">
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#09060f"
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

<title>ixxy VPN — Личный кабинет</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    min-height: 100%;
    background: #07050b;
}}

body {{
    margin: 0;
    min-height: 100vh;
    color: #fff;
    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(133, 67, 255, .24),
            transparent 32%
        ),
        radial-gradient(
            circle at 85% 15%,
            rgba(69, 103, 255, .16),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 90%,
            rgba(153, 44, 255, .12),
            transparent 34%
        ),
        #07050b;
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
    opacity: .18;
    background-image:
        linear-gradient(
            rgba(255,255,255,.025) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,.025) 1px,
            transparent 1px
        );
    background-size: 38px 38px;
    mask-image:
        linear-gradient(
            to bottom,
            black,
            transparent
        );
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
    margin: 0 auto;
    padding:
        calc(20px + env(safe-area-inset-top))
        18px
        calc(38px + env(safe-area-inset-bottom));
}}

.topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.logo {{
    width: 46px;
    height: 46px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 18px;
    letter-spacing: -1px;
    color: white;
    background:
        linear-gradient(
            145deg,
            #a46cff,
            #6134e7 48%,
            #29135f
        );
    box-shadow:
        0 10px 35px rgba(117, 65, 255, .35),
        inset 0 1px 0 rgba(255,255,255,.3);
}}

.brand-text {{
    display: flex;
    flex-direction: column;
    gap: 2px;
}}

.brand-title {{
    font-size: 18px;
    font-weight: 900;
    letter-spacing: -.5px;
}}

.brand-sub {{
    font-size: 11px;
    color: rgba(255,255,255,.45);
    letter-spacing: .8px;
    text-transform: uppercase;
}}

.status {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.09);
    background: rgba(255,255,255,.055);
    backdrop-filter: blur(16px);
    font-size: 12px;
    font-weight: 800;
}}

.status-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #ff4d67;
    box-shadow: 0 0 12px rgba(255,77,103,.8);
}}

.status.active .status-dot {{
    background: #58f7a3;
    box-shadow: 0 0 14px rgba(88,247,163,.9);
}}

.hero {{
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.10);
    border-radius: 32px;
    padding: 30px 24px 24px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.095),
            rgba(255,255,255,.035)
        );
    box-shadow:
        0 30px 100px rgba(0,0,0,.35),
        inset 0 1px 0 rgba(255,255,255,.08);
    backdrop-filter: blur(28px);
}}

.hero::before {{
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    right: -100px;
    top: -100px;
    border-radius: 50%;
    background: rgba(132,79,255,.22);
    filter: blur(25px);
}}

.hero::after {{
    content: "";
    position: absolute;
    width: 180px;
    height: 180px;
    left: -100px;
    bottom: -100px;
    border-radius: 50%;
    background: rgba(70,103,255,.12);
    filter: blur(30px);
}}

.hero-content {{
    position: relative;
    z-index: 2;
}}

.eyebrow {{
    color: #ad8aff;
    font-size: 11px;
    font-weight: 900;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin-bottom: 12px;
}}

h1 {{
    margin: 0;
    font-size: clamp(34px, 10vw, 58px);
    line-height: .95;
    letter-spacing: -3px;
    font-weight: 950;
}}

.hero-description {{
    margin-top: 16px;
    max-width: 570px;
    color: rgba(255,255,255,.58);
    line-height: 1.55;
    font-size: 14px;
}}

.user-line {{
    margin-top: 22px;
    display: flex;
    align-items: center;
    gap: 10px;
    color: rgba(255,255,255,.72);
    font-size: 13px;
}}

.avatar {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(
            145deg,
            #8e62ff,
            #39217f
        );
    font-size: 13px;
    font-weight: 900;
}}

.main-button {{
    position: relative;
    width: 100%;
    min-height: 66px;
    margin-top: 25px;
    border: 0;
    border-radius: 21px;
    color: white;
    cursor: pointer;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: -.2px;
    background:
        linear-gradient(
            135deg,
            #9d6cff,
            #7042ed 45%,
            #4b25b9
        );
    box-shadow:
        0 15px 40px rgba(111,62,240,.35),
        inset 0 1px 0 rgba(255,255,255,.3);
    transition:
        transform .18s ease,
        filter .18s ease;
}}

.main-button:active {{
    transform: scale(.985);
}}

.main-button:hover {{
    filter: brightness(1.08);
}}

.button-title {{
    display: block;
    font-size: 16px;
}}

.button-sub {{
    display: block;
    margin-top: 4px;
    font-size: 10px;
    font-weight: 700;
    color: rgba(255,255,255,.65);
}}

.grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 12px;
}}

.info {{
    padding: 20px;
    min-height: 118px;
    border: 1px solid rgba(255,255,255,.075);
    border-radius: 23px;
    background: rgba(255,255,255,.045);
    backdrop-filter: blur(20px);
}}

.info-icon {{
    font-size: 18px;
    margin-bottom: 16px;
}}

.info-label {{
    color: rgba(255,255,255,.42);
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
}}

.info-value {{
    margin-top: 6px;
    font-size: 16px;
    font-weight: 900;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.progress-card {{
    margin-top: 12px;
    padding: 21px;
    border: 1px solid rgba(255,255,255,.075);
    border-radius: 23px;
    background: rgba(255,255,255,.045);
}}

.progress-head {{
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin-bottom: 13px;
}}

.progress-title {{
    font-size: 14px;
    font-weight: 850;
}}

.progress-percent {{
    color: #ad8aff;
    font-size: 12px;
    font-weight: 900;
}}

.progress {{
    width: 100%;
    height: 9px;
    overflow: hidden;
    border-radius: 99px;
    background: rgba(255,255,255,.07);
}}

.progress-bar {{
    height: 100%;
    width: {progress}%;
    border-radius: inherit;
    background:
        linear-gradient(
            90deg,
            #7041ef,
            #a97cff
        );
    box-shadow:
        0 0 20px rgba(137,91,255,.6);
}}

.section {{
    margin-top: 25px;
}}

.section-title {{
    margin-bottom: 11px;
    padding-left: 3px;
    font-size: 17px;
    font-weight: 950;
    letter-spacing: -.4px;
}}

.connect-grid {{
    display: grid;
    gap: 11px;
}}

.connect {{
    display: flex;
    align-items: center;
    gap: 15px;
    min-height: 74px;
    padding: 15px;
    border: 1px solid rgba(255,255,255,.075);
    border-radius: 22px;
    background: rgba(255,255,255,.045);
    cursor: pointer;
    transition:
        transform .18s ease,
        background .18s ease;
}}

.connect:active {{
    transform: scale(.985);
}}

.connect-icon {{
    flex: 0 0 auto;
    width: 45px;
    height: 45px;
    border-radius: 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,.075);
    font-size: 21px;
}}

.connect-main {{
    flex: 1;
    min-width: 0;
}}

.connect-title {{
    font-size: 14px;
    font-weight: 900;
}}

.connect-description {{
    margin-top: 4px;
    color: rgba(255,255,255,.42);
    font-size: 11px;
    line-height: 1.35;
}}

.arrow {{
    color: rgba(255,255,255,.3);
    font-size: 20px;
}}

.link-card {{
    position: relative;
    overflow: hidden;
    padding: 20px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,.08);
    background:
        linear-gradient(
            145deg,
            rgba(127,78,255,.10),
            rgba(255,255,255,.035)
        );
}}

.link-label {{
    color: rgba(255,255,255,.4);
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-weight: 900;
}}

.link-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 11px;
}}

.link-value {{
    flex: 1;
    min-width: 0;
    padding: 13px;
    border-radius: 14px;
    background: rgba(0,0,0,.25);
    color: rgba(255,255,255,.72);
    font-size: 11px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}}

.copy {{
    flex: 0 0 auto;
    width: 48px;
    height: 48px;
    border: 0;
    border-radius: 14px;
    background: rgba(255,255,255,.09);
    color: white;
    cursor: pointer;
    font-size: 18px;
}}

.steps {{
    display: grid;
    gap: 10px;
}}

.step {{
    display: flex;
    gap: 13px;
    padding: 16px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.06);
    background: rgba(255,255,255,.035);
}}

.step-number {{
    flex: 0 0 auto;
    width: 32px;
    height: 32px;
    border-radius: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(132,91,255,.17);
    color: #b79aff;
    font-size: 12px;
    font-weight: 950;
}}

.step-title {{
    font-size: 13px;
    font-weight: 900;
}}

.step-text {{
    margin-top: 4px;
    color: rgba(255,255,255,.42);
    font-size: 11px;
    line-height: 1.45;
}}

.telegram {{
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 58px;
    margin-top: 12px;
    border-radius: 19px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.045);
    font-size: 13px;
    font-weight: 900;
}}

.security {{
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-top: 18px;
    padding: 16px;
    border-radius: 19px;
    border: 1px solid rgba(100,255,180,.08);
    background: rgba(100,255,180,.035);
}}

.security-icon {{
    font-size: 18px;
}}

.security-title {{
    font-size: 12px;
    font-weight: 900;
}}

.security-text {{
    margin-top: 4px;
    color: rgba(255,255,255,.38);
    font-size: 10px;
    line-height: 1.45;
}}

.footer {{
    text-align: center;
    margin-top: 28px;
    color: rgba(255,255,255,.22);
    font-size: 10px;
    line-height: 1.6;
}}

.toast {{
    position: fixed;
    z-index: 1000;
    left: 50%;
    bottom: calc(25px + env(safe-area-inset-bottom));
    transform: translate(-50%, 25px);
    padding: 12px 17px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.1);
    background: rgba(20,16,28,.88);
    backdrop-filter: blur(22px);
    box-shadow: 0 15px 45px rgba(0,0,0,.35);
    color: white;
    font-size: 12px;
    font-weight: 850;
    opacity: 0;
    pointer-events: none;
    transition: .25s ease;
}}

.toast.show {{
    opacity: 1;
    transform: translate(-50%, 0);
}}

.loader {{
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #07050b;
    transition: opacity .35s ease;
}}

.loader.hide {{
    opacity: 0;
    pointer-events: none;
}}

.loader-logo {{
    width: 72px;
    height: 72px;
    border-radius: 23px;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(
            145deg,
            #a46cff,
            #5530d4
        );
    box-shadow:
        0 0 70px rgba(118,69,255,.45);
    font-size: 24px;
    font-weight: 950;
    animation: pulse 1.15s ease-in-out infinite;
}}

@keyframes pulse {{
    0%,100% {{
        transform: scale(1);
        opacity: .8;
    }}
    50% {{
        transform: scale(1.08);
        opacity: 1;
    }}
}}

@media (min-width: 700px) {{
    .page {{
        padding-top: 42px;
    }}

    .hero {{
        padding: 42px;
    }}

    .grid {{
        grid-template-columns: repeat(4, 1fr);
    }}

    .info {{
        min-height: 135px;
    }}
}}

</style>
</head>

<body>

<div class="loader" id="loader">
    <div class="loader-logo">IX</div>
</div>

<main class="page">

    <header class="topbar">

        <div class="brand">

            <div class="logo">
                IX
            </div>

            <div class="brand-text">
                <div class="brand-title">
                    ixxy VPN
                </div>

                <div class="brand-sub">
                    Private connection
                </div>
            </div>

        </div>

        <div class="status {status_class}">

            <span class="status-dot"></span>

            {esc(status_text)}

        </div>

    </header>


    <section class="hero">

        <div class="hero-content">

            <div class="eyebrow">
                PERSONAL ACCESS
            </div>

            <h1>
                Добро пожаловать<br>
                в ixxy VPN
            </h1>

            <div class="hero-description">
                Твоя персональная VPN-подписка уже здесь.
                Подключай приложение в одно нажатие —
                конфигурация останется скрытой.
            </div>

            <div class="user-line">

                <div class="avatar">
                    {esc(str(username)[:1]).upper()}
                </div>

                <span>
                    {esc(username)}
                </span>

            </div>

            <button
                class="main-button"
                onclick="openHapp()"
            >

                <span class="button-title">
                    ⚡ Подключить в Happ
                </span>

                <span class="button-sub">
                    Быстрый импорт персональной подписки
                </span>

            </button>

        </div>

    </section>


    <section class="grid">

        <div class="info">

            <div class="info-icon">
                👑
            </div>

            <div class="info-label">
                Тариф
            </div>

            <div class="info-value">
                {esc(subscription_name)}
            </div>

        </div>


        <div class="info">

            <div class="info-icon">
                📅
            </div>

            <div class="info-label">
                До
            </div>

            <div class="info-value">
                {esc(until)}
            </div>

        </div>


        <div class="info">

            <div class="info-icon">
                ⏳
            </div>

            <div class="info-label">
                Осталось
            </div>

            <div class="info-value">
                {days_left} дн.
            </div>

        </div>


        <div class="info">

            <div class="info-icon">
                🛡️
            </div>

            <div class="info-label">
                Система
            </div>

            <div class="info-value">
                Защищена
            </div>

        </div>

    </section>


    <section class="progress-card">

        <div class="progress-head">

            <div class="progress-title">
                Состояние подписки
            </div>

            <div class="progress-percent">
                {progress}%
            </div>

        </div>

        <div class="progress">
            <div class="progress-bar"></div>
        </div>

    </section>


    <section class="section">

        <div class="section-title">
            Подключение
        </div>

        <div class="connect-grid">

            <div
                class="connect"
                onclick="openHapp()"
            >

                <div class="connect-icon">
                    ⚡
                </div>

                <div class="connect-main">

                    <div class="connect-title">
                        Подключить через Happ
                    </div>

                    <div class="connect-description">
                        Импорт персональной конфигурации
                        в Happ
                    </div>

                </div>

                <div class="arrow">
                    ›
                </div>

            </div>


            <div
                class="connect"
                onclick="openIncy()"
            >

                <div class="connect-icon">
                    🟣
                </div>

                <div class="connect-main">

                    <div class="connect-title">
                        Добавить в INCY
                    </div>

                    <div class="connect-description">
                        Быстрый импорт подписки
                    </div>

                </div>

                <div class="arrow">
                    ›
                </div>

            </div>

        </div>

    </section>


    <section class="section">

        <div class="section-title">
            Твоя подписка
        </div>

        <div class="link-card">

            <div class="link-label">
                Персональный URL
            </div>

            <div class="link-row">

                <div
                    class="link-value"
                    id="subscriptionUrl"
                >
                    {esc(subscription_url)}
                </div>

                <button
                    class="copy"
                    onclick="copySubscription()"
                    aria-label="Скопировать"
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

        <div class="steps">

            <div class="step">

                <div class="step-number">
                    01
                </div>

                <div>

                    <div class="step-title">
                        Открой Happ
                    </div>

                    <div class="step-text">
                        Нажми «Подключить в Happ».
                        Приложение должно автоматически
                        открыть импорт.
                    </div>

                </div>

            </div>


            <div class="step">

                <div class="step-number">
                    02
                </div>

                <div>

                    <div class="step-title">
                        Импортируй подписку
                    </div>

                    <div class="step-text">
                        Подтверди добавление персональной
                        подписки в приложение.
                    </div>

                </div>

            </div>


            <div class="step">

                <div class="step-number">
                    03
                </div>

                <div>

                    <div class="step-title">
                        Подключись
                    </div>

                    <div class="step-text">
                        Выбери нужную конфигурацию
                        внутри VPN-клиента и подключись.
                    </div>

                </div>

            </div>

        </div>

    </section>


    <section class="section">

        <a
            class="telegram"
            href="{esc(TELEGRAM_URL)}"
            target="_blank"
            rel="noopener"
        >
            💬 Поддержка ixxy VPN
        </a>

    </section>


    <div class="security">

        <div class="security-icon">
            🔐
        </div>

        <div>

            <div class="security-title">
                Конфигурация скрыта
            </div>

            <div class="security-text">
                Данные серверов не отображаются
                на этой странице. Клиент получает
                персональную подписку через защищённый
                URL.
            </div>

        </div>

    </div>


    <footer class="footer">

        ixxy VPN · Private access<br>

        {esc(APP_VERSION)}

    </footer>

</main>


<div
    class="toast"
    id="toast"
>
    Ссылка скопирована
</div>


<script>

const HAPP_URL = {happ_url!r};

const INCY_URL = {incy_url!r};

const SUBSCRIPTION_URL = {subscription_url!r};


function showToast(text) {{

    const toast =
        document.getElementById("toast");

    toast.textContent = text;

    toast.classList.add("show");

    clearTimeout(
        window.__toastTimer
    );

    window.__toastTimer =
        setTimeout(() => {{

            toast.classList.remove("show");

        }}, 1800);
}}


function openHapp() {{

    showToast("Открываем Happ…");

    window.location.href = HAPP_URL;

}}


function openIncy() {{

    showToast("Открываем INCY…");

    window.location.href = INCY_URL;

}}


async function copyText(text) {{

    if (
        navigator.clipboard &&
        window.isSecureContext
    ) {{

        await navigator.clipboard.writeText(text);

        return true;

    }}

    const textarea =
        document.createElement("textarea");

    textarea.value = text;

    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";

    document.body.appendChild(textarea);

    textarea.focus();
    textarea.select();

    let success = false;

    try {{

        success =
            document.execCommand("copy");

    }} catch (e) {{

        success = false;

    }}

    textarea.remove();

    return success;

}}


async function copySubscription() {{

    const success =
        await copyText(
            SUBSCRIPTION_URL
        );

    if (success) {{

        showToast(
            "Персональная ссылка скопирована"
        );

    }} else {{

        showToast(
            "Не удалось скопировать"
        );

    }}

}}


window.addEventListener(
    "load",
    () => {{

        setTimeout(
            () => {{

                const loader =
                    document.getElementById(
                        "loader"
                    );

                loader.classList.add("hide");

                setTimeout(
                    () => {{
                        loader.remove();
                    }},
                    400
                );

            }},
            350
        );

    }}
);

</script>

</body>
</html>
"""

    response = make_response(html_page)

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"

    return response


# ============================================================
# SUBSCRIPTION ENDPOINT
# ============================================================

@app.route("/sub/<token>")
def subscription(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    user, content = load_user_data(user_id)

    if not user:
        abort(404)

    content = get_subscription_content_clean(
        content
    ).strip()

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
        response.headers[key] = value

    response.headers[
        "Content-Disposition"
    ] = "inline"

    return response


# ============================================================
# SUBSCRIPTION PAGE
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    user = get_user(user_id)

    if not user:
        abort(404)

    return render_subscription_page(user_id)


# ============================================================
# HAPP TEST
# ============================================================

@app.route("/happ-test/<token>")
def happ_test(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/{token}"
    )

    happ_url = generate_happ_crypt5(
        subscription_url
    )

    if not happ_url:
        happ_url = (
            "happ://add/"
            + quote(
                subscription_url,
                safe=""
            )
        )

    response = Response(
        happ_url,
        status=200,
        mimetype="text/plain",
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    response = make_response(
        {
            "service": "ixxy VPN",
            "status": "ok",
            "version": APP_VERSION,
        }
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

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
    content="width=device-width,initial-scale=1"
>

<meta
    name="theme-color"
    content="#08060d"
>

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
    padding: 25px;
    color: white;
    background:
        radial-gradient(
            circle at 50% 0%,
            rgba(124,75,255,.25),
            transparent 40%
        ),
        #08060d;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        Arial,
        sans-serif;
}

.card {
    width: 100%;
    max-width: 500px;
    padding: 45px 28px;
    text-align: center;
    border-radius: 32px;
    border: 1px solid rgba(255,255,255,.1);
    background: rgba(255,255,255,.055);
    backdrop-filter: blur(25px);
    box-shadow:
        0 30px 100px rgba(0,0,0,.4);
}

.logo {
    width: 74px;
    height: 74px;
    margin: 0 auto 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 23px;
    background:
        linear-gradient(
            145deg,
            #a56cff,
            #512dc8
        );
    font-size: 24px;
    font-weight: 950;
    box-shadow:
        0 0 60px rgba(120,70,255,.35);
}

h1 {
    margin: 0;
    font-size: 38px;
    letter-spacing: -2px;
}

p {
    color: rgba(255,255,255,.45);
    line-height: 1.6;
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
        Сервис работает.
        Открой персональную ссылку подписки,
        чтобы перейти в личный кабинет.
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
    content="width=device-width,initial-scale=1"
>

<title>ixxy VPN — 404</title>

<style>

body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 25px;
    background: #08060d;
    color: white;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        Arial,
        sans-serif;
}

.card {
    max-width: 430px;
    width: 100%;
    padding: 40px 25px;
    text-align: center;
    border-radius: 30px;
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.08);
}

.code {
    font-size: 70px;
    font-weight: 950;
    letter-spacing: -5px;
}

.text {
    color: rgba(255,255,255,.45);
}

</style>

</head>

<body>

<div class="card">

    <div class="code">
        404
    </div>

    <div class="text">
        Страница ixxy VPN не найдена.
    </div>

</div>

</body>
</html>
        """,
        404
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# RUN
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