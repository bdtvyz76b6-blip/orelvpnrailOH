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

app = Flask(__name__)

# ============================================================
# НАСТРОЙКИ
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy"
).strip()

TELEGRAM_URL = "https://t.me/orelvpntopbot"

# Кэширование полностью отключаем.
# Это важно, чтобы Render/браузер не показывали старую страницу.
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# HAPP CRYPT5
# ============================================================

HPWNR_PATH = os.getenv("HPWNR_PATH", "hpwnr")


def find_hpwnr():
    """
    Ищем hpwnr:
    1. HPWNR_PATH
    2. PATH
    3. несколько стандартных мест
    """

    candidates = [
        HPWNR_PATH,
        "hpwnr",
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
    Превращает обычную HTTPS-ссылку подписки
    в happ://crypt5/...

    Использует hpwnr:
        hpwnr https://example.com/sub
    """

    if not subscription_url:
        return ""

    hpwnr = find_hpwnr()

    if not hpwnr:
        print("[HAPP] hpwnr не найден")
        return ""

    try:
        result = subprocess.run(
            [hpwnr, subscription_url],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            print("[HAPP] hpwnr error:", stderr)
            return ""

        # hpwnr должен вернуть:
        # happ://crypt5/...
        for line in stdout.splitlines():
            line = line.strip()

            if line.startswith("happ://crypt5/"):
                print("[HAPP] Crypt5 успешно создан")
                return line

        # Иногда результат может содержать лишний текст.
        pos = stdout.find("happ://crypt5/")

        if pos >= 0:
            value = stdout[pos:].split()[0].strip()

            if value.startswith("happ://crypt5/"):
                print("[HAPP] Crypt5 успешно найден")
                return value

    except subprocess.TimeoutExpired:
        print("[HAPP] hpwnr timeout")

    except Exception as e:
        print("[HAPP] ошибка:", repr(e))

    return ""


# ============================================================
# TOKEN
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

    # Сначала пытаемся сделать настоящий Crypt5.
    happ_url = generate_happ_crypt5(subscription_url)

    # Если hpwnr временно недоступен,
    # оставляем обычный Happ import.
    if not happ_url:
        happ_url = (
            "happ://add/"
            + quote(subscription_url, safe="")
        )

    incy_url = (
        "incy://add/"
        + quote(subscription_url, safe="")
    )

    return (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    )


# ============================================================
# JS ESCAPE
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
# ДНИ
# ============================================================

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
# ДАТА ПОДПИСКИ
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
            return datetime.strptime(value, fmt).date()
        except Exception:
            pass

    return None


# ============================================================
# ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_user_data(user_id):

    try:
        user = get_user(user_id)
    except Exception as e:
        print("[WEB] get_user error:", repr(e))
        user = None

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
            pass

        try:
            first_name = (
                str(user[2])
                if user[2]
                else "Пользователь"
            )
        except Exception:
            pass

        try:
            subscription = (
                str(user[3])
                if user[3]
                else "none"
            )
        except Exception:
            pass

        try:
            until = (
                str(user[4])
                if user[4]
                else ""
            )
        except Exception:
            pass

    return (
        user,
        username,
        first_name,
        subscription,
        until,
    )


# ============================================================
# NO SUBSCRIPTION
# ============================================================

def no_subscription_page(user_id):

    telegram = html.escape(TELEGRAM_URL)

    page = f"""<!DOCTYPE html>
<html lang="ru">
<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    user-scalable=no"
>

<meta
    name="theme-color"
    content="#09090f"
>

<meta
    name="robots"
    content="noindex,nofollow"
>

<title>ixxy VPN</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html,
body {{
    margin: 0;
    padding: 0;
    min-height: 100%;
    background: #07070b;
    color: #ffffff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}}

body {{
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
}}

.card {{
    width: 100%;
    max-width: 520px;
    padding: 34px 24px;
    border-radius: 30px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.08),
            rgba(255,255,255,.025)
        );
    border: 1px solid rgba(255,255,255,.08);
    box-shadow:
        0 30px 80px rgba(0,0,0,.55);
    text-align: center;
}}

.logo {{
    width: 76px;
    height: 76px;
    margin: 0 auto 22px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    box-shadow:
        0 15px 40px rgba(139,92,246,.35);
}}

h1 {{
    margin: 0;
    font-size: 34px;
    letter-spacing: -1px;
}}

p {{
    color: #a1a1aa;
    line-height: 1.6;
}}

.button {{
    display: block;
    margin-top: 24px;
    padding: 17px;
    border-radius: 18px;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    color: #fff;
    text-decoration: none;
    font-weight: 800;
}}

</style>

</head>

<body>

<div class="card">

<div class="logo">☂️</div>

<h1>ixxy VPN</h1>

<p>
    Подписка не найдена или ещё не активирована.
</p>

<a
    class="button"
    href="{telegram}"
>
    Открыть Telegram
</a>

</div>

</body>
</html>
"""

    response = make_response(page)

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# ГЛАВНАЯ СТРАНИЦА
# ============================================================

@app.route("/")
def index():

    # ВАЖНО:
    # Главная теперь тоже принадлежит этому web.py.
    # Старый index.html больше не используется Flask'ом.

    page = """<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    user-scalable=no"
>

<meta
    name="theme-color"
    content="#09090f"
>

<meta
    name="robots"
    content="noindex,nofollow"
>

<title>ixxy VPN</title>

<style>

* {
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}

html,
body {
    margin: 0;
    min-height: 100%;
    background: #07070b;
    color: #fff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}

body {
    min-height: 100vh;
    overflow-x: hidden;
}

.background {
    position: fixed;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
}

.glow {
    position: absolute;
    width: 360px;
    height: 360px;
    border-radius: 50%;
    filter: blur(100px);
    opacity: .20;
}

.glow.one {
    background: #9333ea;
    top: -120px;
    left: -100px;
}

.glow.two {
    background: #6366f1;
    bottom: -150px;
    right: -100px;
}

.wrap {
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 680px;
    margin: auto;
    padding: 28px 20px 50px;
}

.top {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 900;
    font-size: 21px;
    letter-spacing: -.5px;
}

.brand-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    box-shadow:
        0 10px 30px rgba(139,92,246,.35);
    font-size: 22px;
}

.status {
    padding: 9px 13px;
    border-radius: 999px;
    background: rgba(34,197,94,.10);
    border: 1px solid rgba(34,197,94,.18);
    color: #86efac;
    font-size: 12px;
    font-weight: 800;
}

.hero {
    margin-top: 55px;
}

.badge {
    display: inline-flex;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(168,85,247,.10);
    border: 1px solid rgba(168,85,247,.18);
    color: #d8b4fe;
    font-size: 12px;
    font-weight: 800;
}

h1 {
    margin: 18px 0 0;
    font-size: clamp(44px, 12vw, 76px);
    line-height: .95;
    letter-spacing: -4px;
}

.gradient {
    background:
        linear-gradient(
            135deg,
            #ffffff,
            #c4b5fd,
            #a855f7
        );
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.subtitle {
    margin-top: 22px;
    color: #a1a1aa;
    line-height: 1.7;
    font-size: 16px;
}

.main-card {
    margin-top: 30px;
    padding: 22px;
    border-radius: 28px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );
    border: 1px solid rgba(255,255,255,.08);
    box-shadow:
        0 30px 80px rgba(0,0,0,.40);
}

.big-button {
    width: 100%;
    border: 0;
    padding: 19px;
    border-radius: 20px;
    color: #fff;
    font-size: 16px;
    font-weight: 900;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    box-shadow:
        0 16px 35px rgba(124,58,237,.28);
    cursor: pointer;
}

.features {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 14px;
}

.feature {
    padding: 17px;
    border-radius: 18px;
    background: rgba(255,255,255,.035);
    border: 1px solid rgba(255,255,255,.06);
}

.feature-icon {
    font-size: 21px;
}

.feature-title {
    margin-top: 9px;
    font-weight: 800;
    font-size: 14px;
}

.feature-text {
    margin-top: 5px;
    color: #71717a;
    font-size: 12px;
}

.footer {
    margin-top: 35px;
    text-align: center;
    color: #52525b;
    font-size: 12px;
}

</style>

</head>

<body>

<div class="background">

    <div class="glow one"></div>
    <div class="glow two"></div>

</div>

<div class="wrap">

    <div class="top">

        <div class="brand">

            <div class="brand-icon">
                ☂️
            </div>

            ixxy VPN

        </div>

        <div class="status">
            ONLINE
        </div>

    </div>

    <section class="hero">

        <div class="badge">
            PREMIUM VPN
        </div>

        <h1>
            Ваш интернет.<br>
            <span class="gradient">
                Без ограничений.
            </span>
        </h1>

        <div class="subtitle">

            Быстрое и защищённое подключение
            с современными VPN-протоколами.

        </div>

    </section>

    <div class="main-card">

        <button
            class="big-button"
            onclick="location.href='https://t.me/orelvpntopbot'"
        >
            Открыть ixxy VPN
        </button>

        <div class="features">

            <div class="feature">

                <div class="feature-icon">
                    ⚡
                </div>

                <div class="feature-title">
                    Высокая скорость
                </div>

                <div class="feature-text">
                    Быстрое соединение
                </div>

            </div>

            <div class="feature">

                <div class="feature-icon">
                    🛡️
                </div>

                <div class="feature-title">
                    Защита
                </div>

                <div class="feature-text">
                    Безопасное подключение
                </div>

            </div>

            <div class="feature">

                <div class="feature-icon">
                    🌍
                </div>

                <div class="feature-title">
                    Серверы
                </div>

                <div class="feature-text">
                    Разные локации
                </div>

            </div>

            <div class="feature">

                <div class="feature-icon">
                    📱
                </div>

                <div class="feature-title">
                    Устройства
                </div>

                <div class="feature-text">
                    iPhone, Android и другие
                </div>

            </div>

        </div>

    </div>

    <div class="footer">
        ixxy VPN · 2026
    </div>

</div>

</body>

</html>
"""

    response = make_response(page)

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# PREMIUM SUBSCRIPTION PAGE
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    (
        user,
        username,
        first_name,
        subscription,
        until,
    ) = get_user_data(user_id)

    if not user:
        return no_subscription_page(user_id)

    try:
        subscription_content = (
            get_subscription_content(user_id)
            or ""
        )
    except Exception as e:
        print(
            "[WEB] subscription_content error:",
            repr(e)
        )
        subscription_content = ""

    if not subscription_content.strip():
        return no_subscription_page(user_id)

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    today = datetime.now().date()

    expiration_date = parse_subscription_date(until)

    days_left = 0
    active = False

    if expiration_date:

        delta = (
            expiration_date - today
        ).days

        if delta > 0:
            days_left = delta
            active = True

        elif delta == 0:
            days_left = 1
            active = True

        else:
            days_left = 0
            active = False

    expiration_text = (
        expiration_date.strftime("%d.%m.%Y")
        if expiration_date
        else "Без срока"
    )

    if active:
        status_text = "АКТИВНА"
        status_class = "active"
    else:
        status_text = "ИСТЕКЛА"
        status_class = "expired"

    if subscription == "none":
        tariff_text = "Нет подписки"
    else:
        tariff_text = subscription

    username_display = (
        "@" + username
        if username != "нет"
        and not username.startswith("@")
        else username
    )

    # ========================================================
    # HTML
    # ========================================================

    page = f"""<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1,
    maximum-scale=1,
    user-scalable=no"
>

<meta
    name="theme-color"
    content="#08080d"
>

<meta
    name="robots"
    content="noindex,nofollow"
>

<title>ixxy VPN — Личный кабинет</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    background: #08080d;
}}

body {{
    margin: 0;
    min-height: 100vh;
    background: #08080d;
    color: #fff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}}

button {{
    font: inherit;
}}

.page {{
    width: 100%;
    max-width: 720px;
    margin: auto;
    padding:
        22px
        18px
        45px;
}}

.topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 11px;
    font-size: 19px;
    font-weight: 900;
}}

.logo {{
    width: 43px;
    height: 43px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    box-shadow:
        0 12px 30px rgba(124,58,237,.30);
    font-size: 22px;
}}

.theme {{
    width: 42px;
    height: 42px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,.08);
    background: rgba(255,255,255,.04);
    color: #fff;
    cursor: pointer;
}}

.hero {{
    margin-top: 38px;
}}

.status {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 8px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
}}

.status.active {{
    color: #86efac;
    background: rgba(34,197,94,.09);
    border: 1px solid rgba(34,197,94,.16);
}}

.status.expired {{
    color: #fca5a5;
    background: rgba(239,68,68,.09);
    border: 1px solid rgba(239,68,68,.16);
}}

h1 {{
    margin:
        18px
        0
        0;

    font-size:
        clamp(
            42px,
            11vw,
            70px
        );

    line-height: .94;
    letter-spacing: -3.5px;
}}

.gradient {{
    background:
        linear-gradient(
            135deg,
            #ffffff,
            #c4b5fd,
            #a855f7
        );
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}}

.subtitle {{
    margin-top: 18px;
    color: #71717a;
    font-size: 14px;
    line-height: 1.6;
}}

.main-card {{
    margin-top: 28px;
    padding: 20px;
    border-radius: 28px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );
    border: 1px solid rgba(255,255,255,.08);
    box-shadow:
        0 25px 70px rgba(0,0,0,.40);
}}

.tariff {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
}}

.tariff-label {{
    color: #71717a;
    font-size: 12px;
}}

.tariff-name {{
    margin-top: 6px;
    font-size: 18px;
    font-weight: 900;
}}

.expire {{
    text-align: right;
}}

.expire-label {{
    color: #71717a;
    font-size: 12px;
}}

.expire-date {{
    margin-top: 6px;
    font-size: 16px;
    font-weight: 900;
}}

.days {{
    margin-top: 20px;
    padding: 18px;
    border-radius: 21px;
    background: rgba(255,255,255,.035);
}}

.days-number {{
    font-size: 42px;
    font-weight: 950;
    letter-spacing: -2px;
}}

.days-label {{
    color: #71717a;
    font-size: 12px;
}}

.progress {{
    margin-top: 14px;
    height: 7px;
    border-radius: 99px;
    background: rgba(255,255,255,.07);
    overflow: hidden;
}}

.progress-bar {{
    height: 100%;
    width: {100 if active else 0}%;
    max-width: 100%;
    border-radius: inherit;
    background:
        linear-gradient(
            90deg,
            #a855f7,
            #7c3aed
        );
}}

.buttons {{
    margin-top: 18px;
    display: grid;
    gap: 11px;
}}

.connect {{
    width: 100%;
    padding: 17px;
    border: 0;
    border-radius: 18px;
    color: #fff;
    font-weight: 900;
    background:
        linear-gradient(
            135deg,
            #a855f7,
            #7c3aed
        );
    box-shadow:
        0 13px 30px rgba(124,58,237,.25);
    cursor: pointer;
}}

.secondary {{
    width: 100%;
    padding: 16px;
    border-radius: 18px;
    border:
        1px solid
        rgba(255,255,255,.08);
    background:
        rgba(255,255,255,.035);
    color: #fff;
    font-weight: 800;
    cursor: pointer;
}}

.section {{
    margin-top: 15px;
    padding: 20px;
    border-radius: 25px;
    background:
        rgba(255,255,255,.035);
    border:
        1px solid
        rgba(255,255,255,.065);
}}

.section-title {{
    font-size: 13px;
    font-weight: 900;
}}

.info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 11px;
    margin-top: 13px;
}}

.info {{
    padding: 14px;
    border-radius: 17px;
    background:
        rgba(255,255,255,.035);
}}

.info-label {{
    color: #71717a;
    font-size: 11px;
}}

.info-value {{
    margin-top: 6px;
    font-size: 13px;
    font-weight: 800;
    word-break: break-word;
}}

.link-box {{
    margin-top: 13px;
    display: flex;
    gap: 8px;
    align-items: center;
}}

.link {{
    flex: 1;
    min-width: 0;
    padding: 14px;
    border-radius: 16px;
    background: rgba(0,0,0,.25);
    color: #a1a1aa;
    font-size: 11px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.copy {{
    width: 48px;
    height: 48px;
    flex-shrink: 0;
    border: 0;
    border-radius: 15px;
    background:
        rgba(168,85,247,.14);
    color: #d8b4fe;
    cursor: pointer;
}}

.footer {{
    margin-top: 28px;
    text-align: center;
    color: #3f3f46;
    font-size: 11px;
}}

.toast {{
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform:
        translate(-50%, 20px);
    opacity: 0;
    pointer-events: none;
    z-index: 100;
    padding: 13px 17px;
    border-radius: 15px;
    background: #18181b;
    border:
        1px solid
        rgba(255,255,255,.10);
    box-shadow:
        0 15px 40px rgba(0,0,0,.45);
    font-size: 13px;
    font-weight: 800;
    transition:
        .25s ease;
}}

.toast.show {{
    opacity: 1;
    transform:
        translate(-50%, 0);
}}

@media (max-width: 480px) {{

    .page {{
        padding-left: 15px;
        padding-right: 15px;
    }}

    .info-grid {{
        grid-template-columns: 1fr;
    }}

}}

</style>

</head>

<body>

<div class="page">

    <div class="topbar">

        <div class="brand">

            <div class="logo">
                ☂️
            </div>

            ixxy VPN

        </div>

        <button
            class="theme"
            onclick="toggleTheme()"
            aria-label="Тема"
        >
            ◐
        </button>

    </div>


    <section class="hero">

        <div class="status {status_class}">
            ● {status_text}
        </div>

        <h1>
            Привет,<br>
            <span class="gradient">
                {html.escape(first_name)}
            </span>
        </h1>

        <div class="subtitle">
            Личный кабинет вашей подписки ixxy VPN.
        </div>

    </section>


    <div class="main-card">

        <div class="tariff">

            <div>

                <div class="tariff-label">
                    ТАРИФ
                </div>

                <div class="tariff-name">
                    {html.escape(tariff_text)}
                </div>

            </div>

            <div class="expire">

                <div class="expire-label">
                    ДО
                </div>

                <div class="expire-date">
                    {expiration_text}
                </div>

            </div>

        </div>


        <div class="days">

            <div class="days-number">
                {days_left}
            </div>

            <div class="days-label">
                {days_word(days_left)} осталось
            </div>

            <div class="progress">
                <div class="progress-bar"></div>
            </div>

        </div>


        <div class="buttons">

            <button
                class="connect"
                onclick="openApp('happ')"
            >
                🚀 Подключить через Happ
            </button>

            <button
                class="secondary"
                onclick="openApp('incy')"
            >
                📱 Подключить через INCY
            </button>

        </div>

    </div>


    <div class="section">

        <div class="section-title">
            👤 Профиль
        </div>

        <div class="info-grid">

            <div class="info">

                <div class="info-label">
                    Имя
                </div>

                <div class="info-value">
                    {html.escape(first_name)}
                </div>

            </div>

            <div class="info">

                <div class="info-label">
                    Telegram
                </div>

                <div class="info-value">
                    {html.escape(username_display)}
                </div>

            </div>

            <div class="info">

                <div class="info-label">
                    Telegram ID
                </div>

                <div class="info-value">
                    {user_id}
                </div>

            </div>

            <div class="info">

                <div class="info-label">
                    Статус
                </div>

                <div class="info-value">
                    {status_text}
                </div>

            </div>

        </div>

    </div>


    <div class="section">

        <div class="section-title">
            🔐 Ссылка подписки
        </div>

        <div class="link-box">

            <div
                class="link"
                id="subscriptionLink"
            >
                {html.escape(subscription_url)}
            </div>

            <button
                class="copy"
                onclick="copyLink()"
            >
                ⧉
            </button>

        </div>

        <button
            class="secondary"
            style="margin-top:11px"
            onclick="refreshPage()"
        >
            ↻ Обновить
        </button>

    </div>


    <div class="section">

        <div class="section-title">
            🛡️ Защита
        </div>

        <div class="subtitle"
             style="margin-top:8px">

            Ваша ссылка подписки скрыта внутри
            защищённого Happ Crypt5 формата.

        </div>

    </div>


    <div class="footer">
        ixxy VPN · premium access
    </div>

</div>


<div
    class="toast"
    id="toast"
>
    Готово
</div>


<script>

const subscriptionLink =
    '{js_escape(subscription_url)}';

const happUrl =
    '{js_escape(happ_url)}';

const incyUrl =
    '{js_escape(incy_url)}';

const pageUrl =
    '{js_escape(page_url)}';


function showToast(text) {{

    const toast =
        document.getElementById("toast");

    toast.textContent = text;

    toast.classList.add("show");

    setTimeout(() => {{
        toast.classList.remove("show");
    }}, 2200);
}}


function openApp(type) {{

    let url = "";

    if (type === "happ") {{
        url = happUrl;
    }}

    if (type === "incy") {{
        url = incyUrl;
    }}

    if (!url) {{
        showToast("Ссылка недоступна");
        return;
    }}

    window.location.href = url;

    setTimeout(() => {{

        showToast(
            "Если приложение не открылось — установите VPN-клиент."
        );

    }}, 1300);
}}


async function copyLink() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        showToast(
            "Ссылка скопирована"
        );

    }} catch (error) {{

        fallbackCopy();

    }}
}}


function fallbackCopy() {{

    const textarea =
        document.createElement("textarea");

    textarea.value =
        subscriptionLink;

    textarea.style.position =
        "fixed";

    textarea.style.opacity =
        "0";

    document.body.appendChild(
        textarea
    );

    textarea.focus();

    textarea.select();

    try {{

        document.execCommand(
            "copy"
        );

        showToast(
            "Ссылка скопирована"
        );

    }} catch (error) {{

        showToast(
            "Не удалось скопировать"
        );

    }}

    textarea.remove();
}}


function refreshPage() {{

    const separator =
        pageUrl.includes("?")
            ? "&"
            : "?";

    window.location.href =
        pageUrl
        + separator
        + "refresh="
        + Date.now();
}}


function toggleTheme() {{

    const dark =
        document.body.dataset.theme !== "light";

    if (dark) {{

        document.body.dataset.theme =
            "light";

        document.body.style.background =
            "#f5f5f7";

        document.body.style.color =
            "#111";

        showToast(
            "Светлая тема"
        );

    }} else {{

        document.body.dataset.theme =
            "dark";

        document.body.style.background =
            "#08080d";

        document.body.style.color =
            "#fff";

        showToast(
            "Тёмная тема"
        );

    }}
}}


</script>

</body>
</html>
"""

    response = make_response(page)

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# RAW SUBSCRIPTION
# ============================================================

@app.route("/sub/<token>")
def raw_subscription(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    try:
        content = (
            get_subscription_content(user_id)
            or ""
        )
    except Exception as e:

        print(
            "[SUB] database error:",
            repr(e)
        )

        content = ""

    if not content.strip():
        abort(404)

    response = Response(
        content,
        mimetype="text/plain; charset=utf-8",
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    response = Response(
        "ixxy VPN OK",
        mimetype="text/plain",
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    return response


# ============================================================
# HAPP TEST
# ============================================================

@app.route("/happ-test/<token>")
def happ_test(token):

    user_id = get_user_id_from_token(token)

    if not user_id:
        abort(404)

    _, subscription_url, happ_url, incy_url = get_urls(
        user_id
    )

    return Response(
        (
            "SUBSCRIPTION:\n"
            + subscription_url
            + "\n\n"
            "HAPP:\n"
            + happ_url
            + "\n\n"
            "INCY:\n"
            + incy_url
        ),
        mimetype="text/plain; charset=utf-8",
        headers=NO_CACHE_HEADERS,
    )


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    response = Response(
        "404 — ixxy VPN",
        status=404,
        mimetype="text/plain",
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

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

    print(
        "=================================================="
    )

    print(
        "ixxy VPN WEB STARTED"
    )

    print(
        f"PORT: {port}"
    )

    print(
        f"PUBLIC_SITE_URL: {PUBLIC_SITE_URL}"
    )

    print(
        f"SUBSCRIPTION_PREFIX: {SUBSCRIPTION_PREFIX}"
    )

    hpwnr = find_hpwnr()

    if hpwnr:
        print(
            f"HAPP Crypt5: hpwnr найден -> {hpwnr}"
        )
    else:
        print(
            "HAPP Crypt5: hpwnr НЕ найден"
        )

    print(
        "=================================================="
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )