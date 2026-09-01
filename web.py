import os
import html
import shutil
import subprocess
from datetime import datetime
from urllib.parse import quote

from flask import Flask, Response, abort

from database import (
    get_subscription_content,
    get_user,
)

app = Flask(__name__)

# ============================================================
# CONFIG
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

APP_VERSION = "ixxy-2026.09.01"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}

HPWNR_PATH = os.getenv("HPWNR_PATH", "hpwnr")


# ============================================================
# HELPERS
# ============================================================

def find_hpwnr():
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

        for line in stdout.splitlines():
            line = line.strip()

            if line.startswith("happ://crypt5/"):
                print("[HAPP] Crypt5 успешно создан")
                return line

        pos = stdout.find("happ://crypt5/")

        if pos >= 0:
            value = stdout[pos:].split()[0].strip()

            if value.startswith("happ://crypt5/"):
                print("[HAPP] Crypt5 найден")
                return value

    except subprocess.TimeoutExpired:
        print("[HAPP] hpwnr timeout")

    except Exception as e:
        print("[HAPP] ошибка:", repr(e))

    return ""


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
            username = str(user[1]) if user[1] else "нет"
        except Exception:
            pass

        try:
            first_name = str(user[2]) if user[2] else "Пользователь"
        except Exception:
            pass

        try:
            subscription = str(user[3]) if user[3] else "none"
        except Exception:
            pass

        try:
            until = str(user[4]) if user[4] else ""
        except Exception:
            pass

    return user, username, first_name, subscription, until


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
# COMMON HTML
# ============================================================

def page_shell(content, title="ixxy VPN"):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1,
      maximum-scale=1,user-scalable=no">

<meta name="theme-color" content="#08080c">
<meta name="apple-mobile-web-app-capable" content="yes">

<title>{html.escape(title)}</title>

<style>

* {{
    box-sizing: border-box;
}}

html {{
    background:#08080c;
}}

body {{
    margin:0;
    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(139,92,246,.18),
            transparent 28%
        ),
        radial-gradient(
            circle at 100% 20%,
            rgba(124,58,237,.12),
            transparent 30%
        ),
        #08080c;

    color:#f5f5f7;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Inter",
        Arial,
        sans-serif;

    min-height:100vh;
}}

button,
a {{
    -webkit-tap-highlight-color:transparent;
}}

a {{
    color:inherit;
    text-decoration:none;
}}

.app {{
    min-height:100vh;
    display:flex;
}}

.sidebar {{
    width:250px;
    min-height:100vh;
    position:fixed;
    left:0;
    top:0;
    bottom:0;

    background:rgba(12,12,17,.88);
    border-right:1px solid rgba(255,255,255,.07);

    backdrop-filter:blur(25px);
    -webkit-backdrop-filter:blur(25px);

    padding:25px 16px;
    z-index:20;
}}

.brand {{
    display:flex;
    align-items:center;
    gap:12px;
    padding:5px 10px 30px;
}}

.brand-logo {{
    width:40px;
    height:40px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:13px;

    background:
        linear-gradient(
            145deg,
            #a855f7,
            #6d28d9
        );

    box-shadow:
        0 0 35px rgba(139,92,246,.35);

    font-size:21px;
}}

.brand-name {{
    font-weight:800;
    font-size:19px;
    letter-spacing:-.5px;
}}

.brand-vpn {{
    color:#a78bfa;
    font-size:11px;
    font-weight:700;
    margin-left:3px;
}}

.menu-title {{
    padding:0 12px;
    color:#666673;
    font-size:10px;
    text-transform:uppercase;
    letter-spacing:1.3px;
    margin-bottom:8px;
}}

.nav {{
    display:flex;
    flex-direction:column;
    gap:4px;
}}

.nav-item {{
    display:flex;
    align-items:center;
    gap:12px;

    padding:12px 13px;
    border-radius:11px;

    color:#858590;
    font-size:13px;
    font-weight:600;

    transition:.2s;
}}

.nav-item:hover {{
    color:#fff;
    background:rgba(255,255,255,.045);
}}

.nav-item.active {{
    color:#fff;
    background:
        linear-gradient(
            90deg,
            rgba(139,92,246,.22),
            rgba(139,92,246,.06)
        );

    border:1px solid rgba(139,92,246,.16);
}}

.nav-icon {{
    width:18px;
    text-align:center;
    font-size:16px;
}}

.sidebar-bottom {{
    position:absolute;
    left:16px;
    right:16px;
    bottom:18px;
}}

.version {{
    color:#4e4e58;
    text-align:center;
    font-size:10px;
}}

.main {{
    margin-left:250px;
    width:calc(100% - 250px);
    padding:32px;
}}

.topbar {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:30px;
}}

.page-title {{
    font-size:27px;
    font-weight:800;
    letter-spacing:-1px;
}}

.page-subtitle {{
    color:#71717c;
    font-size:12px;
    margin-top:5px;
}}

.status {{
    display:flex;
    align-items:center;
    gap:8px;

    padding:8px 12px;
    border-radius:999px;

    background:rgba(34,197,94,.07);
    border:1px solid rgba(34,197,94,.18);

    color:#86efac;
    font-size:11px;
    font-weight:700;
}}

.dot {{
    width:7px;
    height:7px;
    border-radius:50%;
    background:#4ade80;
    box-shadow:0 0 12px #4ade80;
}}

.grid {{
    display:grid;
    grid-template-columns:
        repeat(12,minmax(0,1fr));
    gap:16px;
}}

.card {{
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.055),
            rgba(255,255,255,.018)
        );

    border:1px solid rgba(255,255,255,.075);
    border-radius:17px;

    padding:21px;

    box-shadow:
        0 20px 60px rgba(0,0,0,.22);

    backdrop-filter:blur(20px);
    -webkit-backdrop-filter:blur(20px);
}}

.card-title {{
    color:#777782;
    font-size:11px;
    text-transform:uppercase;
    letter-spacing:1px;
    margin-bottom:12px;
}}

.big {{
    font-size:26px;
    font-weight:800;
    letter-spacing:-1px;
}}

.muted {{
    color:#777782;
}}

.accent {{
    color:#a78bfa;
}}

.hero {{
    grid-column:span 8;

    min-height:245px;

    background:
        radial-gradient(
            circle at 80% 20%,
            rgba(139,92,246,.25),
            transparent 35%
        ),
        linear-gradient(
            145deg,
            rgba(139,92,246,.10),
            rgba(255,255,255,.025)
        );

    position:relative;
    overflow:hidden;
}}

.hero::after {{
    content:"";
    position:absolute;
    width:180px;
    height:180px;
    right:-80px;
    bottom:-80px;

    border-radius:50%;

    border:1px solid rgba(167,139,250,.2);
    box-shadow:
        0 0 80px rgba(139,92,246,.15);
}}

.hero-icon {{
    font-size:35px;
    margin-bottom:20px;
}}

.hero h2 {{
    margin:0;
    font-size:29px;
    letter-spacing:-1.2px;
}}

.hero p {{
    color:#777782;
    font-size:12px;
    margin:9px 0 0;
}}

.hero-name {{
    color:#c4b5fd;
}}

.side-stat {{
    grid-column:span 4;
}}

.stat-row {{
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:13px 0;
    border-bottom:1px solid rgba(255,255,255,.055);
}}

.stat-row:last-child {{
    border-bottom:0;
}}

.stat-label {{
    color:#777782;
    font-size:12px;
}}

.stat-value {{
    font-size:12px;
    font-weight:700;
}}

.progress {{
    margin-top:15px;
    height:7px;
    background:#17171e;
    border-radius:99px;
    overflow:hidden;
}}

.progress-bar {{
    height:100%;
    width:100%;

    background:
        linear-gradient(
            90deg,
            #7c3aed,
            #c084fc
        );

    border-radius:99px;

    box-shadow:
        0 0 18px rgba(168,85,247,.4);
}}

.half {{
    grid-column:span 6;
}}

.full {{
    grid-column:span 12;
}}

.connect-grid {{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
    margin-top:18px;
}}

.connect {{
    display:flex;
    align-items:center;
    justify-content:center;
    gap:9px;

    min-height:52px;

    border-radius:12px;

    font-size:12px;
    font-weight:800;

    transition:.2s;
}}

.connect:hover {{
    transform:translateY(-1px);
}}

.happ {{
    background:
        linear-gradient(
            135deg,
            #8b5cf6,
            #6d28d9
        );

    box-shadow:
        0 12px 30px rgba(109,40,217,.25);
}}

.incy {{
    background:rgba(255,255,255,.045);
    border:1px solid rgba(255,255,255,.08);
}}

.link-box {{
    display:flex;
    gap:9px;
    margin-top:15px;
}}

.link-input {{
    flex:1;
    min-width:0;

    border:1px solid rgba(255,255,255,.07);
    background:#0b0b10;
    color:#777782;

    border-radius:10px;
    padding:12px;

    font-size:10px;
    outline:none;
}}

.copy {{
    border:0;
    background:#17131f;
    border:1px solid rgba(139,92,246,.2);
    color:#c4b5fd;

    padding:0 15px;
    border-radius:10px;

    font-weight:700;
    cursor:pointer;
}}

.profile {{
    display:flex;
    align-items:center;
    gap:13px;
}}

.avatar {{
    width:43px;
    height:43px;

    border-radius:13px;

    display:flex;
    align-items:center;
    justify-content:center;

    background:
        linear-gradient(
            145deg,
            #8b5cf6,
            #4c1d95
        );

    font-size:17px;
    font-weight:800;
}}

.profile-name {{
    font-weight:750;
    font-size:13px;
}}

.profile-id {{
    color:#656570;
    font-size:10px;
    margin-top:3px;
}}

.info-grid {{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:10px;
}}

.info {{
    background:#0c0c11;
    border:1px solid rgba(255,255,255,.05);
    padding:12px;
    border-radius:11px;
}}

.info-label {{
    color:#5f5f69;
    font-size:9px;
    text-transform:uppercase;
    letter-spacing:.8px;
}}

.info-value {{
    margin-top:5px;
    font-size:12px;
    font-weight:700;
    word-break:break-word;
}}

.footer {{
    color:#3f3f48;
    text-align:center;
    font-size:10px;
    padding:25px 0 10px;
}}

.mobile-menu {{
    display:none;
}}

@media(max-width:900px) {{

    .sidebar {{
        display:none;
    }}

    .mobile-menu {{
        display:flex;
        align-items:center;
        justify-content:space-between;
        margin-bottom:24px;
    }}

    .main {{
        margin-left:0;
        width:100%;
        padding:18px;
    }}

    .grid {{
        display:grid;
        grid-template-columns:1fr;
    }}

    .hero,
    .side-stat,
    .half,
    .full {{
        grid-column:span 1;
    }}

    .topbar {{
        margin-bottom:20px;
    }}

    .page-title {{
        font-size:23px;
    }}

}}

</style>
</head>

<body>

<div class="app">

<aside class="sidebar">

    <div class="brand">
        <div class="brand-logo">☂</div>

        <div>
            <div class="brand-name">
                ixxy <span class="brand-vpn">VPN</span>
            </div>
        </div>
    </div>

    <div class="menu-title">
        Управление
    </div>

    <nav class="nav">

        <a class="nav-item active" href="#">
            <span class="nav-icon">⌂</span>
            Обзор
        </a>

        <a class="nav-item" href="#connection">
            <span class="nav-icon">⚡</span>
            Подключение
        </a>

        <a class="nav-item" href="#profile">
            <span class="nav-icon">♙</span>
            Профиль
        </a>

        <a class="nav-item" href="#subscription">
            <span class="nav-icon">◈</span>
            Подписка
        </a>

    </nav>

    <div class="sidebar-bottom">
        <div class="version">
            ixxy panel · {APP_VERSION}
        </div>
    </div>

</aside>


<main class="main">

    <div class="mobile-menu">
        <div class="brand">
            <div class="brand-logo">☂</div>
            <div class="brand-name">
                ixxy <span class="brand-vpn">VPN</span>
            </div>
        </div>

        <div class="status">
            <span class="dot"></span>
            ONLINE
        </div>
    </div>


    {content}


    <div class="footer">
        ixxy VPN · secure connection · {APP_VERSION}
    </div>

</main>

</div>


<script>

function copyText(value) {{

    if (!value) return;

    navigator.clipboard.writeText(value)
        .then(() => {{
            alert("Ссылка скопирована");
        }})
        .catch(() => {{

            const input = document.createElement("textarea");

            input.value = value;

            document.body.appendChild(input);

            input.select();

            document.execCommand("copy");

            input.remove();

            alert("Ссылка скопирована");
        }});
}}

</script>

</body>
</html>
"""


# ============================================================
# NO SUBSCRIPTION
# ============================================================

def no_subscription_page(user_id):

    content = f"""

<div class="topbar">

    <div>
        <div class="page-title">
            Панель управления
        </div>

        <div class="page-subtitle">
            Ваш личный кабинет ixxy VPN
        </div>
    </div>

    <div class="status">
        <span class="dot"></span>
        ONLINE
    </div>

</div>


<div class="grid">

    <section class="card hero">

        <div class="hero-icon">
            ☂️
        </div>

        <h2>
            Добро пожаловать в
            <span class="hero-name">
                ixxy VPN
            </span>
        </h2>

        <p>
            У вас пока нет активной подписки.
        </p>

    </section>


    <section class="card side-stat">

        <div class="card-title">
            Состояние
        </div>

        <div class="big">
            Неактивна
        </div>

        <div class="muted" style="font-size:11px;margin-top:6px">
            Подписка отсутствует
        </div>

        <div style="margin-top:25px">

            <a
                class="connect happ"
                href="{html.escape(TELEGRAM_URL)}"
            >
                ✦ Получить подписку
            </a>

        </div>

    </section>


    <section class="card full">

        <div class="card-title">
            Telegram
        </div>

        <div class="info-grid">

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
                    Сервис
                </div>

                <div class="info-value">
                    ixxy VPN
                </div>

            </div>

        </div>

    </section>

</div>
"""

    return page_shell(
        content,
        "ixxy VPN — Кабинет"
    )


# ============================================================
# SUBSCRIPTION PAGE
# ============================================================

def subscription_page(user_id):

    user, username, first_name, subscription, until = get_user_data(user_id)

    page_url, subscription_url, happ_url, incy_url = get_urls(user_id)

    today = datetime.now().date()

    expiry = parse_subscription_date(until)

    active = False
    days_left = 0

    if expiry:

        days_left = (
            expiry - today
        ).days

        if days_left >= 0:
            active = True

    status_text = "Активна" if active else "Истекла"

    status_color = "#4ade80" if active else "#fb7185"

    if expiry:
        expiry_text = expiry.strftime("%d.%m.%Y")
    else:
        expiry_text = "Не указана"

    if active and days_left > 30:
        progress = 100
    elif active:
        progress = max(
            5,
            min(100, days_left * 100 / 30)
        )
    else:
        progress = 0

    tariff = (
        subscription
        if subscription != "none"
        else "Без подписки"
    )

    safe_name = html.escape(first_name)
    safe_username = html.escape(username)
    safe_tariff = html.escape(tariff)

    content = f"""

<div class="topbar">

    <div>
        <div class="page-title">
            Обзор
        </div>

        <div class="page-subtitle">
            Добро пожаловать, {safe_name}
        </div>
    </div>

    <div class="status"
         style="
         color:{status_color};
         border-color:{status_color}33;
         background:{status_color}0d;
         ">

        <span class="dot"
              style="
              background:{status_color};
              box-shadow:0 0 12px {status_color};
              "></span>

        {status_text.upper()}

    </div>

</div>


<div class="grid">


<!-- HERO -->

<section class="card hero">

    <div class="hero-icon">
        ☂️
    </div>

    <h2>
        ixxy VPN
    </h2>

    <p>
        Быстрое и защищённое подключение
        без лишних настроек.
    </p>

    <div style="
        display:inline-flex;
        margin-top:25px;
        padding:7px 11px;
        border-radius:8px;
        background:rgba(139,92,246,.1);
        border:1px solid rgba(139,92,246,.15);
        color:#c4b5fd;
        font-size:10px;
        font-weight:700;
    ">
        {safe_tariff}
    </div>

</section>


<!-- EXPIRATION -->

<section class="card side-stat">

    <div class="card-title">
        Подписка
    </div>

    <div class="big">
        {days_left if active else 0}
    </div>

    <div class="muted"
         style="font-size:11px;margin-top:5px">

        {days_word(days_left)}
        осталось

    </div>

    <div class="progress">

        <div
            class="progress-bar"
            style="width:{progress}%"
        ></div>

    </div>

    <div style="
        margin-top:16px;
        color:#777782;
        font-size:10px;
    ">
        До {expiry_text}
    </div>

</section>


<!-- CONNECTION -->

<section
    class="card full"
    id="connection"
>

    <div class="card-title">
        Подключение
    </div>

    <div style="
        font-size:18px;
        font-weight:800;
    ">
        Подключите ixxy VPN
    </div>

    <div style="
        color:#666671;
        font-size:11px;
        margin-top:5px;
    ">
        Выберите приложение для подключения.
    </div>


    <div class="connect-grid">

        <a
            class="connect happ"
            href="{html.escape(happ_url)}"
        >
            ☂️ Подключить через Happ
        </a>

        <a
            class="connect incy"
            href="{html.escape(incy_url)}"
        >
            ⚡ Подключить через INCY
        </a>

    </div>

</section>


<!-- SUBSCRIPTION -->

<section
    class="card half"
    id="subscription"
>

    <div class="card-title">
        Подписка
    </div>

    <div class="big"
         style="font-size:20px">

        {safe_tariff}

    </div>

    <div class="stat-row">

        <span class="stat-label">
            Статус
        </span>

        <span
            class="stat-value"
            style="color:{status_color}"
        >
            {status_text}
        </span>

    </div>

    <div class="stat-row">

        <span class="stat-label">
            Окончание
        </span>

        <span class="stat-value">
            {expiry_text}
        </span>

    </div>

</section>


<!-- PROFILE -->

<section
    class="card half"
    id="profile"
>

    <div class="card-title">
        Профиль
    </div>

    <div class="profile">

        <div class="avatar">
            {html.escape(
                (first_name[:1] if first_name else "U")
            )}
        </div>

        <div>

            <div class="profile-name">
                {safe_name}
            </div>

            <div class="profile-id">
                @{safe_username}
            </div>

        </div>

    </div>

    <div class="info-grid"
         style="margin-top:15px">

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
                Тариф
            </div>

            <div class="info-value">
                {safe_tariff}
            </div>

        </div>

    </div>

</section>


<!-- LINK -->

<section class="card full">

    <div class="card-title">
        Ваша подписка
    </div>

    <div style="
        font-size:13px;
        font-weight:700;
    ">
        Ссылка подписки
    </div>

    <div class="link-box">

        <input
            class="link-input"
            readonly
            value="{html.escape(subscription_url)}"
            id="subscriptionLink"
        >

        <button
            class="copy"
            onclick="copyText(
                document.getElementById(
                    'subscriptionLink'
                ).value
            )"
        >
            Копировать
        </button>

    </div>

    <div style="
        margin-top:10px;
        color:#555560;
        font-size:9px;
    ">
        Не передавайте эту ссылку другим людям.
    </div>

</section>


<!-- SECURITY -->

<section class="card full">

    <div style="
        display:flex;
        align-items:center;
        gap:13px;
    ">

        <div style="
            width:42px;
            height:42px;
            border-radius:12px;
            display:flex;
            align-items:center;
            justify-content:center;
            background:rgba(139,92,246,.1);
            border:1px solid rgba(139,92,246,.14);
            font-size:18px;
        ">
            🔐
        </div>

        <div>

            <div style="
                font-weight:800;
                font-size:12px;
            ">
                Защита подключения
            </div>

            <div style="
                color:#62626d;
                font-size:10px;
                margin-top:4px;
            ">
                Конфигурация доступна только
                через вашу персональную подписку.
            </div>

        </div>

    </div>

</section>


</div>
"""

    return page_shell(
        content,
        "ixxy VPN — Панель"
    )


# ============================================================
# ROUTES
# ============================================================

@app.after_request
def add_headers(response):

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers["X-Ixxy-Version"] = APP_VERSION

    return response


@app.route("/")
def index():

    content = f"""

<div class="topbar">

    <div>
        <div class="page-title">
            ixxy VPN
        </div>

        <div class="page-subtitle">
            Private VPN infrastructure
        </div>
    </div>

    <div class="status">
        <span class="dot"></span>
        ONLINE
    </div>

</div>


<div class="grid">

<section class="card hero">

    <div class="hero-icon">
        ☂️
    </div>

    <h2>
        Добро пожаловать в ixxy VPN
    </h2>

    <p>
        Ваше быстрое и защищённое подключение.
    </p>

    <div style="margin-top:24px">

        <a
            class="connect happ"
            style="
            display:inline-flex;
            padding:0 22px;
            "
            href="{html.escape(TELEGRAM_URL)}"
        >
            ✦ Открыть Telegram
        </a>

    </div>

</section>


<section class="card side-stat">

    <div class="card-title">
        Система
    </div>

    <div class="big">
        Online
    </div>

    <div class="muted"
         style="font-size:11px;margin-top:6px">
        ixxy VPN infrastructure
    </div>

    <div class="stat-row"
         style="margin-top:15px">

        <span class="stat-label">
            Version
        </span>

        <span class="stat-value">
            {APP_VERSION}
        </span>

    </div>

</section>


<section class="card half">

    <div class="card-title">
        Безопасность
    </div>

    <div class="big"
         style="font-size:20px">
        Protected
    </div>

    <div class="muted"
         style="font-size:11px;margin-top:6px">
        Защищённое VPN-соединение
    </div>

</section>


<section class="card half">

    <div class="card-title">
        Подключение
    </div>

    <div class="big"
         style="font-size:20px">
        Happ / INCY
    </div>

    <div class="muted"
         style="font-size:11px;margin-top:6px">
        Поддерживаемые клиенты
    </div>

</section>

</div>
"""

    return page_shell(
        content,
        "ixxy VPN"
    )


@app.route("/s/<token>")
def subscription(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    try:
        user = get_user(user_id)
    except Exception:
        user = None

    if not user:
        return no_subscription_page(user_id)

    return subscription_page(user_id)


@app.route("/sub/<token>")
def raw_subscription(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    try:
        content = get_subscription_content(user_id)
    except Exception as e:
        print(
            "[WEB] subscription error:",
            repr(e)
        )
        content = ""

    if not content:
        return Response(
            "# ixxy VPN\n"
            "# Subscription unavailable\n",
            status=404,
            mimetype="text/plain",
        )

    response = Response(
        content,
        mimetype="text/plain"
    )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Content-Disposition"] = "inline"

    return response


@app.route("/health")
def health():

    response = Response(
        "ixxy VPN OK\n"
        f"VERSION: {APP_VERSION}\n",
        mimetype="text/plain"
    )

    return response


@app.route("/happ-test/<token>")
def happ_test(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    page_url, subscription_url, happ_url, incy_url = get_urls(
        user_id
    )

    return Response(
        "IXXY VPN\n\n"
        f"PAGE:\n{page_url}\n\n"
        f"SUBSCRIPTION:\n{subscription_url}\n\n"
        f"HAPP:\n{happ_url}\n\n"
        f"INCY:\n{incy_url}\n\n"
        f"VERSION:\n{APP_VERSION}\n",
        mimetype="text/plain"
    )


@app.errorhandler(404)
def not_found(error):

    return Response(
        "404 — ixxy VPN",
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

    print(
        f"[WEB] ixxy VPN starting "
        f"VERSION={APP_VERSION}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )