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
    content="#0d0d14"
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

:root {{
    --bg: #0d0d14;
    --bg-secondary: #13131f;
    --surface: rgba(255, 255, 255, 0.04);
    --surface-hover: rgba(255, 255, 255, 0.08);
    --border: rgba(255, 255, 255, 0.08);
    --text-primary: #f5f5f7;
    --text-secondary: rgba(245, 245, 247, 0.64);
    --text-tertiary: rgba(245, 245, 247, 0.4);
    --accent-pink: #ff5c8a;
    --accent-purple: #a45cff;
    --accent-gradient: linear-gradient(135deg, #ff5c8a, #a45cff);
    --shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
    --progress-bg: rgba(255, 255, 255, 0.08);
    --progress-fill: linear-gradient(90deg, #ff5c8a, #a45cff);
}}

body.light-theme {{
    --bg: #f7f7fb;
    --bg-secondary: #ffffff;
    --surface: rgba(0, 0, 0, 0.03);
    --surface-hover: rgba(0, 0, 0, 0.06);
    --border: rgba(0, 0, 0, 0.08);
    --text-primary: #1a1a2e;
    --text-secondary: rgba(26, 26, 46, 0.7);
    --text-tertiary: rgba(26, 26, 46, 0.45);
    --shadow: 0 20px 50px rgba(0, 0, 0, 0.08);
    --progress-bg: rgba(0, 0, 0, 0.08);
}}

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    background: var(--bg);
    transition: background 0.4s ease;
}}

body {{
    margin: 0;
    min-height: 100vh;

    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(255, 92, 138, 0.15),
            transparent 38%
        ),
        radial-gradient(
            circle at 100% 30%,
            rgba(164, 92, 255, 0.12),
            transparent 32%
        ),
        var(--bg);

    color: var(--text-primary);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        Arial,
        sans-serif;

    overflow-x: hidden;
    transition: background 0.4s ease, color 0.3s ease;
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
            rgba(255, 92, 138, 0.04) 50%,
            transparent 100%
        );

    opacity: 0.7;
    z-index: 0;
}}

.container {{
    width: 100%;
    max-width: 560px;

    margin: 0 auto;

    padding:
        calc(24px + env(safe-area-inset-top))
        18px
        calc(30px + env(safe-area-inset-bottom));

    position: relative;
    z-index: 1;
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
    width: 46px;
    height: 46px;

    border-radius: 14px;

    display: flex;
    align-items: center;
    justify-content: center;

    font-size: 22px;
    font-weight: 900;

    background: var(--accent-gradient);
    color: #fff;

    box-shadow: 0 10px 30px rgba(255, 92, 138, 0.3);
}}

.brand-text {{
    font-size: 19px;
    font-weight: 800;
    letter-spacing: -0.4px;
}}

.brand-sub {{
    margin-top: 2px;

    font-size: 11px;

    color: var(--text-tertiary);

    letter-spacing: 0.5px;
}}

.header-controls {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

.theme-toggle {{
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--surface);
    color: var(--text-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    transition: all 0.3s ease;
    outline: none;
}}

.theme-toggle:hover {{
    background: var(--surface-hover);
    transform: scale(1.05);
}}

.status {{
    display: flex;
    align-items: center;
    gap: 7px;

    padding: 9px 12px;

    border-radius: 999px;

    font-size: 10px;
    font-weight: 800;

    letter-spacing: 0.5px;

    border: 1px solid var(--border);

    background: var(--surface);

    color: var(--text-secondary);
}}

.status.active {{
    color: var(--text-primary);
    border-color: rgba(255, 92, 138, 0.3);
}}

.status-dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--text-tertiary);

    box-shadow: 0 0 10px rgba(0,0,0,0.2);
}}

.active .status-dot {{
    background: #ff5c8a;

    box-shadow:
        0 0 10px rgba(255, 92, 138, 0.8);
}}

.hero {{
    position: relative;

    padding: 30px 22px 24px;

    border-radius: 30px;

    background: var(--surface);

    border: 1px solid var(--border);

    box-shadow: var(--shadow),
                inset 0 1px 0 rgba(255,255,255,0.03);

    overflow: hidden;
    transition: background 0.3s ease, border 0.3s ease, box-shadow 0.3s ease;
}}

.hero::before {{
    content: "";

    position: absolute;

    width: 250px;
    height: 250px;

    top: -140px;
    left: 50%;

    transform: translateX(-50%);

    background: var(--accent-gradient);
    opacity: 0.2;

    filter: blur(70px);

    pointer-events: none;
}}

.hero-content {{
    position: relative;
    z-index: 2;

    text-align: center;
}}

.eyebrow {{
    color: var(--text-tertiary);

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
    background: var(--accent-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.user-description {{
    color: var(--text-secondary);

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

    color: #fff;

    background: var(--accent-gradient);

    font-size: 16px;

    font-weight: 850;

    letter-spacing: -0.2px;

    box-shadow: 0 15px 40px rgba(255, 92, 138, 0.3);

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease;
}}

.connect:active {{
    transform: scale(0.975);

    box-shadow: 0 8px 20px rgba(255, 92, 138, 0.2);
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

    background: var(--surface);

    border: 1px solid var(--border);

    min-width: 0;
    transition: background 0.3s ease, border 0.3s ease;
}}

.card-label {{
    color: var(--text-tertiary);

    font-size: 10px;

    text-transform: uppercase;

    letter-spacing: 1px;

    font-weight: 800;

    margin-bottom: 8px;
}}

.card-value {{
    font-size: 15px;

    font-weight: 750;

    color: var(--text-primary);

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
}}

.progress-card {{
    margin-top: 12px;

    padding: 19px;

    border-radius: 21px;

    background: var(--surface);

    border: 1px solid var(--border);
    transition: background 0.3s ease, border 0.3s ease;
}}

.progress-top {{
    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 11px;
}}

.progress-title {{
    font-size: 12px;

    color: var(--text-secondary);

    font-weight: 700;
}}

.progress-value {{
    font-size: 12px;

    color: var(--text-primary);

    font-weight: 800;
}}

.progress {{
    width: 100%;

    height: 6px;

    border-radius: 999px;

    overflow: hidden;

    background: var(--progress-bg);
}}

.progress-bar {{
    width: {min(100, max(3, days_left))}%;

    height: 100%;

    border-radius: inherit;

    background: var(--progress-fill);

    box-shadow: 0 0 14px rgba(255, 92, 138, 0.5);
}}

.section {{
    margin-top: 25px;
}}

.section-title {{
    margin: 0 0 11px 4px;

    font-size: 13px;

    font-weight: 800;

    color: var(--text-secondary);
}}

.app-card {{
    display: flex;

    align-items: center;

    justify-content: space-between;

    gap: 12px;

    padding: 17px;

    margin-bottom: 9px;

    border-radius: 20px;

    color: var(--text-primary);

    text-decoration: none;

    background: var(--surface);

    border: 1px solid var(--border);

    transition: all 0.3s ease;
}}

.app-card:hover {{
    background: var(--surface-hover);
    transform: translateY(-1px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}}

.app-card:active {{
    transform: scale(0.98);
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

    background: var(--accent-gradient);
    color: #fff;

    border: none;

    font-size: 20px;
    box-shadow: 0 5px 15px rgba(255, 92, 138, 0.3);
}}

.app-name {{
    font-size: 14px;

    font-weight: 800;

    margin-bottom: 3px;
}}

.app-description {{
    font-size: 11px;

    color: var(--text-tertiary);
}}

.arrow {{
    color: var(--text-tertiary);

    font-size: 20px;
}}

.subscription-box {{
    padding: 17px;

    border-radius: 20px;

    background: var(--surface);

    border: 1px solid var(--border);
    transition: background 0.3s ease, border 0.3s ease;
}}

.subscription-label {{
    font-size: 10px;

    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 1px;

    color: var(--text-tertiary);

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

    background: rgba(0, 0, 0, 0.2);

    border: 1px solid var(--border);

    color: var(--text-secondary);

    font-family: monospace;

    font-size: 10px;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;
    transition: background 0.3s ease;
}}

.light-theme .subscription-url {{
    background: rgba(255, 255, 255, 0.8);
}}

.copy {{
    border: 0;

    padding: 12px 14px;

    border-radius: 13px;

    background: var(--accent-gradient);

    color: #fff;

    font-size: 11px;

    font-weight: 850;

    cursor: pointer;

    transition: all 0.3s ease;
    box-shadow: 0 5px 15px rgba(255, 92, 138, 0.3);
}}

.copy:hover {{
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(255, 92, 138, 0.4);
}}

.info {{
    margin-top: 25px;

    padding: 18px;

    border-radius: 21px;

    background: var(--surface);

    border: 1px solid var(--border);
    transition: background 0.3s ease, border 0.3s ease;
}}

.info-title {{
    font-size: 13px;

    font-weight: 800;

    margin-bottom: 13px;
    color: var(--text-primary);
}}

.step {{
    display: flex;

    gap: 11px;

    margin-top: 11px;

    color: var(--text-secondary);

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

    background: var(--accent-gradient);
    color: #fff;

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

    background: var(--surface);

    border: 1px solid var(--border);

    color: var(--text-secondary);

    font-size: 13px;

    font-weight: 750;

    transition: all 0.3s ease;
}}

.support:hover {{
    background: var(--surface-hover);
    color: var(--text-primary);
}}

.security {{
    margin-top: 14px;

    text-align: center;

    color: var(--text-tertiary);

    font-size: 10px;

    line-height: 1.5;
}}

.footer {{
    text-align: center;

    margin-top: 27px;

    color: var(--text-tertiary);

    font-size: 10px;

    letter-spacing: 0.3px;
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

<body class="dark-theme">

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

        <div class="header-controls">
            <button
                class="theme-toggle"
                id="themeToggle"
                aria-label="Переключить тему"
                title="Переключить тему"
            >
                <span id="themeIcon">☀️</span>
            </button>

            <div class="status {status_class}">
                <span class="status-dot"></span>
                {status_text}
            </div>
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


// Переключение темы
function applyTheme(theme) {{
    if (theme === 'light') {{
        document.body.classList.add('light-theme');
        document.body.classList.remove('dark-theme');
        document.getElementById('themeIcon').textContent = '🌙';
    }} else {{
        document.body.classList.add('dark-theme');
        document.body.classList.remove('light-theme');
        document.getElementById('themeIcon').textContent = '☀️';
    }}

    localStorage.setItem('ixxy-theme', theme);
}}

document.addEventListener('DOMContentLoaded', function() {{
    const savedTheme = localStorage.getItem('ixxy-theme') || 'dark';
    applyTheme(savedTheme);

    document.getElementById('themeToggle').addEventListener('click', function() {{
        const current = document.body.classList.contains('light-theme') ? 'light' : 'dark';
        const next = current === 'light' ? 'dark' : 'light';
        applyTheme(next);
    }});
}});


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
        <meta name="theme-color" content="#0d0d14">
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

            background: radial-gradient(circle at 50% 0%, #1a0b2e 0%, #0d0d14 70%);
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
            filter: drop-shadow(0 0 20px rgba(255, 92, 138, 0.6));
        }

        h1 {
            margin: 0 0 8px;
            font-size: 30px;
            background: linear-gradient(135deg, #ff5c8a, #a45cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        p {
            color: rgba(255,255,255,.5);
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