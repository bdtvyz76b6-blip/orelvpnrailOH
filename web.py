import os
import html
import shutil
import subprocess
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

APP_VERSION = "ixxy-2026.09.02-premium"

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

HPWNR_PATH = os.getenv(
    "HPWNR_PATH",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "bin",
        "hpwnr"
    )
)

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
    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{quote(token, safe='')}"
    )


# ============================================================
# HPWNR / HAPP CRYPT4
# ============================================================

def find_hpwnr():
    """
    Ищем hpwnr:

    1. HPWNR_PATH
    2. ./bin/hpwnr
    3. PATH
    """

    candidates = [
        HPWNR_PATH,
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "bin",
            "hpwnr"
        ),
        shutil.which("hpwnr"),
    ]

    for path in candidates:
        if not path:
            continue

        try:
            if os.path.isfile(path) and os.access(path, os.X_OK):
                return path
        except Exception:
            continue

    return None


def encrypt_happ_crypt4(subscription_url: str):
    """
    Преобразует:

        https://site/sub/token

    в:

        happ://crypt4/...

    через hpwnr.
    """

    binary = find_hpwnr()

    if not binary:
        return None

    try:
        result = subprocess.run(
            [
                binary,
                subscription_url,
                "crypt4",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )

    except Exception:
        return None

    if result.returncode != 0:
        return None

    encrypted = (result.stdout or "").strip()

    if not encrypted.startswith("happ://crypt4/"):
        return None

    return encrypted


def build_happ_url(token: str):
    """
    Основная ссылка Happ.

    Формат:

    https://happ.vpnbypass.click/?RAW=happ://crypt4/...
    """

    subscription_url = build_subscription_url(token)

    encrypted = encrypt_happ_crypt4(
        subscription_url
    )

    if not encrypted:
        return None

    return (
        "https://happ.vpnbypass.click/?RAW="
        + quote(
            encrypted,
            safe=":/+="
        )
    )


def build_incy_url(token: str):
    subscription_url = build_subscription_url(token)

    return (
        "incy://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )


# ============================================================
# TEXT / DATE HELPERS
# ============================================================

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

            dt = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

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
            dt = datetime.fromisoformat(
                str(subscription_until).replace(
                    "Z",
                    "+00:00"
                )
            )

        now = (
            datetime.now(dt.tzinfo)
            if dt.tzinfo
            else datetime.now()
        )

        seconds = (
            dt - now
        ).total_seconds()

        if seconds <= 0:
            return 0

        return max(
            1,
            int(seconds / 86400)
        )

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
                str(subscription_until).replace(
                    "Z",
                    "+00:00"
                )
            )

        now = (
            datetime.now(dt.tzinfo)
            if dt.tzinfo
            else datetime.now()
        )

        return dt > now

    except Exception:
        return False


# ============================================================
# PREMIUM CABINET
# ============================================================

def render_page(
    token,
    user_id,
    first_name,
    subscription,
    subscription_until,
    subscription_link,
):

    active = is_subscription_active(
        subscription_until
    )

    days_left = get_days_left(
        subscription_until
    )

    name = safe_text(
        first_name,
        "Пользователь"
    )

    # Всегда показываем именно тариф ixxy.
    tariff = "ixxy"

    expiry = format_date(
        subscription_until
    )

    subscription_url = build_subscription_url(
        token
    )

    happ_url = build_happ_url(token)
    incy_url = build_incy_url(token)

    if active:
        status_text = "Подключение активно"
        status_class = "active"
        status_icon = "✓"
    else:
        status_text = "Подписка завершена"
        status_class = "inactive"
        status_icon = "!"
    
    if active:
        if days_left == 1:
            days_text = "1 день"
        elif 2 <= days_left <= 4:
            days_text = f"{days_left} дня"
        else:
            days_text = f"{days_left} дней"
    else:
        days_text = "Завершена"

    # Если подписка активна, показываем процент
    # визуально как состояние, а не как реальный
    # процент от фиксированного срока.
    progress = (
        min(100, max(8, days_left))
        if active
        else 0
    )

    # Кнопка Happ
    if happ_url:
        happ_button = f"""
        <a
            class="connect-button"
            href="{html.escape(happ_url)}"
        >
            <span class="connect-icon">⚡</span>
            <span>
                <strong>Подключить VPN</strong>
                <small>Открыть в Happ</small>
            </span>
            <span class="connect-arrow">→</span>
        </a>
        """
    else:
        happ_button = """
        <div class="connect-button disabled">
            <span class="connect-icon">⚡</span>
            <span>
                <strong>Happ временно недоступен</strong>
                <small>Попробуйте позже</small>
            </span>
        </div>
        """

    # INCY
    incy_card = f"""
    <a
        class="client-card"
        href="{html.escape(incy_url)}"
    >
        <div class="client-icon incy">
            ◉
        </div>

        <div class="client-info">
            <strong>INCY</strong>
            <span>Альтернативный клиент</span>
        </div>

        <div class="client-arrow">
            →
        </div>
    </a>
    """

    safe_subscription_url = html.escape(
        subscription_url
    )

    safe_telegram_url = html.escape(
        TELEGRAM_URL
    )

    return f"""<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
    initial-scale=1.0,
    maximum-scale=1.0,
    viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#07070b"
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

<title>
    ixxy VPN — Личный кабинет
</title>

<style>

:root {{
    --bg: #07070b;
    --bg2: #0d0d14;

    --card: rgba(255,255,255,.055);
    --card2: rgba(255,255,255,.075);

    --border: rgba(255,255,255,.09);

    --white: #ffffff;
    --text: rgba(255,255,255,.92);
    --muted: rgba(255,255,255,.52);
    --muted2: rgba(255,255,255,.32);

    --pink: #ff4f86;
    --purple: #9b5cff;

    --gradient:
        linear-gradient(
            135deg,
            #ff4f86 0%,
            #b052ff 100%
        );

    --shadow:
        0 30px 90px
        rgba(0,0,0,.48);
}}

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    min-height: 100%;
    background: var(--bg);
}}

body {{
    margin: 0;
    min-height: 100vh;

    color: var(--text);

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        Arial,
        sans-serif;

    background:
        radial-gradient(
            500px 300px at 50% -100px,
            rgba(255,79,134,.22),
            transparent 70%
        ),
        radial-gradient(
            500px 400px at 100% 30%,
            rgba(155,92,255,.13),
            transparent 70%
        ),
        var(--bg);

    overflow-x: hidden;
}}

body::before {{
    content: "";

    position: fixed;
    inset: 0;

    pointer-events: none;

    opacity: .035;

    background-image:
        url("data:image/svg+xml,%3Csvg viewBox='0 0 180 180' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.5'/%3E%3C/svg%3E");

    z-index: 0;
}}

a {{
    color: inherit;
}}

.page {{
    position: relative;
    z-index: 1;

    width: 100%;
    max-width: 620px;

    margin: 0 auto;

    padding:
        calc(20px + env(safe-area-inset-top))
        17px
        calc(30px + env(safe-area-inset-bottom));
}}


/* =========================================================
   HEADER
   ========================================================= */

.header {{
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 24px;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 11px;
}}

.logo {{
    position: relative;

    width: 45px;
    height: 45px;

    border-radius: 15px;

    display: flex;
    align-items: center;
    justify-content: center;

    background: var(--gradient);

    color: white;

    font-size: 21px;
    font-weight: 900;

    box-shadow:
        0 10px 35px
        rgba(255,79,134,.28);
}}

.logo::after {{
    content: "";

    position: absolute;
    inset: 1px;

    border-radius: 14px;

    border: 1px solid
        rgba(255,255,255,.25);
}}

.brand-name {{
    font-size: 18px;
    font-weight: 850;

    letter-spacing: -.5px;
}}

.brand-caption {{
    margin-top: 2px;

    color: var(--muted2);

    font-size: 9px;
    font-weight: 700;

    letter-spacing: 1.5px;
}}

.header-status {{
    display: flex;
    align-items: center;
    gap: 7px;

    padding: 9px 11px;

    border: 1px solid var(--border);

    border-radius: 999px;

    background:
        rgba(255,255,255,.035);

    font-size: 9px;
    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: .7px;
}}

.status-dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;

    background: var(--muted2);
}}

.header-status.active {{
    color: rgba(255,255,255,.78);
}}

.header-status.active .status-dot {{
    background: #54e39a;

    box-shadow:
        0 0 12px
        rgba(84,227,154,.8);
}}

.header-status.inactive {{
    color: rgba(255,255,255,.5);
}}


/* =========================================================
   HERO
   ========================================================= */

.hero {{
    position: relative;

    padding: 31px 20px 20px;

    border-radius: 30px;

    border: 1px solid
        rgba(255,255,255,.095);

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.075),
            rgba(255,255,255,.025)
        );

    box-shadow:
        var(--shadow),
        inset 0 1px 0
        rgba(255,255,255,.045);

    overflow: hidden;
}}

.hero-glow {{
    position: absolute;

    width: 300px;
    height: 300px;

    top: -200px;
    left: 50%;

    transform: translateX(-50%);

    background:
        radial-gradient(
            circle,
            rgba(255,79,134,.42),
            transparent 68%
        );

    filter: blur(15px);

    pointer-events: none;
}}

.hero-content {{
    position: relative;
    z-index: 2;
}}

.welcome {{
    text-align: center;

    color: var(--muted2);

    font-size: 10px;
    font-weight: 800;

    letter-spacing: 1.7px;

    text-transform: uppercase;
}}

.user-name {{
    margin-top: 10px;

    text-align: center;

    font-size: 30px;
    line-height: 1.08;

    font-weight: 900;

    letter-spacing: -1.4px;

    background:
        linear-gradient(
            135deg,
            #fff 15%,
            #ffb1c8 55%,
            #cda8ff 100%
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;

    word-break: break-word;
}}

.user-subtitle {{
    margin-top: 8px;

    text-align: center;

    color: var(--muted);

    font-size: 12px;
}}


/* =========================================================
   CONNECTION BUTTON
   ========================================================= */

.connect-button {{
    position: relative;

    display: flex;
    align-items: center;

    width: 100%;

    min-height: 72px;

    margin-top: 25px;

    padding: 11px 13px;

    border-radius: 21px;

    text-decoration: none;

    color: #fff;

    background:
        linear-gradient(
            135deg,
            #ff4f86,
            #a74eff
        );

    box-shadow:
        0 18px 45px
        rgba(255,79,134,.24);

    transition:
        transform .15s ease,
        box-shadow .15s ease;
}}

.connect-button::before {{
    content: "";

    position: absolute;
    inset: 1px;

    border-radius: 20px;

    border-top:
        1px solid
        rgba(255,255,255,.3);

    pointer-events: none;
}}

.connect-button:active {{
    transform: scale(.975);

    box-shadow:
        0 10px 25px
        rgba(255,79,134,.18);
}}

.connect-icon {{
    width: 48px;
    height: 48px;

    flex: 0 0 48px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 16px;

    background:
        rgba(255,255,255,.15);

    font-size: 20px;
}}

.connect-button strong {{
    display: block;

    margin-left: 12px;

    font-size: 15px;
    font-weight: 850;
}}

.connect-button small {{
    display: block;

    margin:
        3px 0 0 12px;

    color:
        rgba(255,255,255,.67);

    font-size: 10px;
    font-weight: 600;
}}

.connect-arrow {{
    margin-left: auto;
    margin-right: 7px;

    font-size: 22px;

    opacity: .75;
}}

.connect-button.disabled {{
    cursor: not-allowed;
    opacity: .55;
}}


/* =========================================================
   STATS
   ========================================================= */

.stats {{
    display: grid;

    grid-template-columns:
        repeat(2, minmax(0, 1fr));

    gap: 10px;

    margin-top: 11px;
}}

.stat {{
    min-width: 0;

    padding: 17px 16px;

    border-radius: 20px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        var(--border);
}}

.stat-label {{
    color: var(--muted2);

    font-size: 9px;
    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 1.2px;
}}

.stat-value {{
    margin-top: 8px;

    color: var(--white);

    font-size: 15px;
    font-weight: 800;

    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.stat-value.accent {{
    color: #ff7da3;
}}


/* =========================================================
   SUBSCRIPTION STATE
   ========================================================= */

.subscription-state {{
    margin-top: 11px;

    padding: 17px;

    border-radius: 21px;

    border:
        1px solid
        var(--border);

    background:
        rgba(255,255,255,.04);
}}

.state-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;

    margin-bottom: 12px;
}}

.state-title {{
    color: var(--muted);

    font-size: 11px;
    font-weight: 750;
}}

.state-value {{
    font-size: 10px;
    font-weight: 850;

    letter-spacing: 1px;
}}

.state-value.active {{
    color: #62e6a2;
}}

.state-value.inactive {{
    color: #ff708f;
}}

.progress {{
    width: 100%;
    height: 7px;

    border-radius: 999px;

    background:
        rgba(255,255,255,.07);

    overflow: hidden;
}}

.progress-bar {{
    width: {progress}%;

    height: 100%;

    border-radius: inherit;

    background:
        linear-gradient(
            90deg,
            #ff4f86,
            #a74eff
        );

    box-shadow:
        0 0 16px
        rgba(255,79,134,.55);
}}


/* =========================================================
   SECTION
   ========================================================= */

.section {{
    margin-top: 28px;
}}

.section-heading {{
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin:
        0 4px
        11px;
}}

.section-title {{
    color: var(--text);

    font-size: 13px;
    font-weight: 850;
}}

.section-caption {{
    color: var(--muted2);

    font-size: 9px;
    font-weight: 700;

    text-transform: uppercase;

    letter-spacing: .8px;
}}


/* =========================================================
   CLIENT CARDS
   ========================================================= */

.client-card {{
    display: flex;
    align-items: center;

    min-height: 70px;

    padding: 11px 14px;

    margin-bottom: 9px;

    border-radius: 20px;

    border:
        1px solid
        var(--border);

    background:
        rgba(255,255,255,.045);

    text-decoration: none;

    transition:
        transform .15s ease,
        background .15s ease;
}}

.client-card:active {{
    transform: scale(.985);
}}

.client-icon {{
    width: 46px;
    height: 46px;

    flex: 0 0 46px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    color: white;

    background:
        var(--gradient);

    font-size: 19px;

    box-shadow:
        0 8px 20px
        rgba(255,79,134,.2);
}}

.client-icon.incy {{
    background:
        linear-gradient(
            135deg,
            #6868ff,
            #9d55ff
        );
}}

.client-info {{
    min-width: 0;

    margin-left: 12px;
}}

.client-info strong {{
    display: block;

    font-size: 14px;
    font-weight: 850;
}}

.client-info span {{
    display: block;

    margin-top: 3px;

    color: var(--muted2);

    font-size: 10px;
}}

.client-arrow {{
    margin-left: auto;

    color: var(--muted2);

    font-size: 20px;
}}


/* =========================================================
   SUBSCRIPTION
   ========================================================= */

.subscription-box {{
    padding: 17px;

    border-radius: 21px;

    border:
        1px solid
        var(--border);

    background:
        rgba(255,255,255,.04);
}}

.subscription-caption {{
    color: var(--muted2);

    font-size: 9px;
    font-weight: 800;

    text-transform: uppercase;

    letter-spacing: 1.2px;
}}

.subscription-row {{
    display: flex;
    align-items: center;

    gap: 8px;

    margin-top: 10px;
}}

.subscription-url {{
    min-width: 0;
    flex: 1;

    padding: 12px;

    border-radius: 13px;

    border:
        1px solid
        rgba(255,255,255,.07);

    background:
        rgba(0,0,0,.22);

    color:
        rgba(255,255,255,.45);

    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        Monaco,
        Consolas,
        monospace;

    font-size: 9px;

    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.copy-button {{
    flex: 0 0 auto;

    border: 0;

    padding: 12px 13px;

    border-radius: 13px;

    background:
        var(--gradient);

    color: #fff;

    font-size: 9px;
    font-weight: 850;

    cursor: pointer;

    box-shadow:
        0 7px 18px
        rgba(255,79,134,.22);
}}

.copy-button:active {{
    transform: scale(.96);
}}


/* =========================================================
   HOW TO CONNECT
   ========================================================= */

.steps {{
    padding: 18px;

    border-radius: 21px;

    border:
        1px solid
        var(--border);

    background:
        rgba(255,255,255,.04);
}}

.step {{
    display: flex;
    align-items: flex-start;

    gap: 12px;

    margin-bottom: 15px;
}}

.step:last-child {{
    margin-bottom: 0;
}}

.step-number {{
    width: 26px;
    height: 26px;

    flex: 0 0 26px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 9px;

    color: #fff;

    background:
        var(--gradient);

    font-size: 10px;
    font-weight: 850;
}}

.step-text strong {{
    display: block;

    font-size: 11px;
    font-weight: 800;

    color: var(--text);
}}

.step-text span {{
    display: block;

    margin-top: 3px;

    color: var(--muted2);

    font-size: 10px;
    line-height: 1.4;
}}


/* =========================================================
   SUPPORT
   ========================================================= */

.support {{
    display: flex;
    align-items: center;
    justify-content: center;

    min-height: 54px;

    margin-top: 12px;

    border-radius: 17px;

    border:
        1px solid
        var(--border);

    background:
        rgba(255,255,255,.04);

    color:
        rgba(255,255,255,.72);

    text-decoration: none;

    font-size: 12px;
    font-weight: 800;
}}

.support:active {{
    transform: scale(.985);
}}


/* =========================================================
   SECURITY
   ========================================================= */

.security {{
    display: flex;
    align-items: center;
    gap: 9px;

    margin-top: 17px;

    padding: 13px 14px;

    border-radius: 15px;

    background:
        rgba(255,255,255,.025);

    border:
        1px solid
        rgba(255,255,255,.045);

    color: var(--muted2);

    font-size: 9px;
    line-height: 1.45;
}}

.security-icon {{
    flex: 0 0 auto;

    font-size: 13px;
}}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {{
    margin-top: 23px;

    text-align: center;

    color:
        rgba(255,255,255,.2);

    font-size: 9px;

    letter-spacing: .4px;
}}

.footer-brand {{
    color:
        rgba(255,255,255,.35);

    font-weight: 800;
}}


/* =========================================================
   SMALL DEVICES
   ========================================================= */

@media (max-width: 380px) {{

    .page {{
        padding-left: 12px;
        padding-right: 12px;
    }}

    .hero {{
        padding-left: 16px;
        padding-right: 16px;
    }}

    .user-name {{
        font-size: 27px;
    }}

    .header-status {{
        padding-left: 9px;
        padding-right: 9px;
    }}

    .stats {{
        gap: 8px;
    }}

    .stat {{
        padding: 15px 13px;
    }}
}}

</style>

</head>


<body>

<div class="page">


    <!-- =====================================================
         HEADER
    ====================================================== -->

    <header class="header">

        <div class="brand">

            <div class="logo">
                ⚡
            </div>

            <div>

                <div class="brand-name">
                    ixxy VPN
                </div>

                <div class="brand-caption">
                    PRIVATE NETWORK
                </div>

            </div>

        </div>


        <div
            class="header-status {status_class}"
        >

            <span class="status-dot"></span>

            {status_text}

        </div>

    </header>


    <!-- =====================================================
         HERO
    ====================================================== -->

    <section class="hero">

        <div class="hero-glow"></div>

        <div class="hero-content">

            <div class="welcome">
                Личный кабинет
            </div>

            <div class="user-name">
                {name}
            </div>

            <div class="user-subtitle">
                Ваше защищённое подключение к ixxy VPN
            </div>


            {happ_button}

        </div>

    </section>


    <!-- =====================================================
         STATS
    ====================================================== -->

    <section class="stats">


        <div class="stat">

            <div class="stat-label">
                Тариф
            </div>

            <div class="stat-value accent">
                ixxy
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Осталось
            </div>

            <div class="stat-value">
                {days_text}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Действует до
            </div>

            <div class="stat-value">
                {expiry}
            </div>

        </div>


        <div class="stat">

            <div class="stat-label">
                Состояние
            </div>

            <div class="stat-value">
                {"Активна" if active else "Завершена"}
            </div>

        </div>


    </section>


    <!-- =====================================================
         SUBSCRIPTION STATE
    ====================================================== -->

    <section class="subscription-state">

        <div class="state-top">

            <div class="state-title">
                Состояние подписки
            </div>

            <div
                class="state-value {status_class}"
            >
                {"ACTIVE" if active else "EXPIRED"}
            </div>

        </div>

        <div class="progress">

            <div class="progress-bar"></div>

        </div>

    </section>


    <!-- =====================================================
         CLIENTS
    ====================================================== -->

    <section class="section">

        <div class="section-heading">

            <div class="section-title">
                Подключение
            </div>

            <div class="section-caption">
                Clients
            </div>

        </div>


        {(
            f'''
            <a
                class="client-card"
                href="{html.escape(happ_url)}"
            >

                <div class="client-icon">
                    ⚡
                </div>

                <div class="client-info">

                    <strong>
                        Happ
                    </strong>

                    <span>
                        Защищённое подключение
                    </span>

                </div>

                <div class="client-arrow">
                    →
                </div>

            </a>
            '''
            if happ_url
            else
            '''
            <div class="client-card">

                <div class="client-icon">
                    ⚡
                </div>

                <div class="client-info">

                    <strong>
                        Happ
                    </strong>

                    <span>
                        Временно недоступен
                    </span>

                </div>

            </div>
            '''
        )}


        {incy_card}

    </section>


    <!-- =====================================================
         PERSONAL SUBSCRIPTION
    ====================================================== -->

    <section class="section">

        <div class="section-heading">

            <div class="section-title">
                Моя подписка
            </div>

            <div class="section-caption">
                Personal
            </div>

        </div>


        <div class="subscription-box">

            <div class="subscription-caption">
                Персональная ссылка
            </div>


            <div class="subscription-row">

                <div
                    class="subscription-url"
                    id="subscriptionUrl"
                >
                    {safe_subscription_url}
                </div>


                <button
                    class="copy-button"
                    id="copyButton"
                    onclick="copySubscription()"
                >
                    КОПИРОВАТЬ
                </button>

            </div>

        </div>

    </section>


    <!-- =====================================================
         HOW TO CONNECT
    ====================================================== -->

    <section class="section">

        <div class="section-heading">

            <div class="section-title">
                Как подключиться
            </div>

            <div class="section-caption">
                3 шага
            </div>

        </div>


        <div class="steps">


            <div class="step">

                <div class="step-number">
                    1
                </div>

                <div class="step-text">

                    <strong>
                        Нажмите «Подключить VPN»
                    </strong>

                    <span>
                        Откроется приложение Happ
                        с вашей подпиской.
                    </span>

                </div>

            </div>


            <div class="step">

                <div class="step-number">
                    2
                </div>

                <div class="step-text">

                    <strong>
                        Добавьте подписку
                    </strong>

                    <span>
                        Подтвердите добавление
                        конфигурации в приложении.
                    </span>

                </div>

            </div>


            <div class="step">

                <div class="step-number">
                    3
                </div>

                <div class="step-text">

                    <strong>
                        Включите VPN
                    </strong>

                    <span>
                        После подключения можно
                        пользоваться ixxy VPN.
                    </span>

                </div>

            </div>


        </div>

    </section>


    <!-- =====================================================
         SUPPORT
    ====================================================== -->

    <a
        class="support"
        href="{safe_telegram_url}"
        target="_blank"
        rel="noopener noreferrer"
    >
        💬 &nbsp; Поддержка ixxy VPN
    </a>


    <!-- =====================================================
         SECURITY
    ====================================================== -->

    <div class="security">

        <span class="security-icon">
            🔒
        </span>

        <span>
            Технические параметры серверов скрыты.
            Подключение и обновление конфигурации
            выполняются автоматически.
        </span>

    </div>


    <!-- =====================================================
         FOOTER
    ====================================================== -->

    <div class="footer">

        <span class="footer-brand">
            ixxy VPN
        </span>

        · Private Network

        · ID {user_id}

        · {APP_VERSION}

    </div>


</div>


<script>

const SUB_URL = {subscription_url!r};


// =========================================================
// COPY SUBSCRIPTION
// =========================================================

async function copySubscription() {{

    const button =
        document.getElementById(
            "copyButton"
        );

    try {{

        if (
            navigator.clipboard &&
            navigator.clipboard.writeText
        ) {{

            await navigator.clipboard.writeText(
                SUB_URL
            );

        }} else {{

            const textarea =
                document.createElement(
                    "textarea"
                );

            textarea.value = SUB_URL;

            textarea.style.position =
                "fixed";

            textarea.style.opacity = "0";

            document.body.appendChild(
                textarea
            );

            textarea.focus();
            textarea.select();

            document.execCommand(
                "copy"
            );

            textarea.remove();

        }}

        if (button) {{

            const old =
                button.textContent;

            button.textContent =
                "СКОПИРОВАНО";

            setTimeout(
                function() {{
                    button.textContent =
                        old;
                }},
                1800
            );

        }}

    }} catch (error) {{

        if (button) {{

            const old =
                button.textContent;

            button.textContent =
                "ОШИБКА";

            setTimeout(
                function() {{
                    button.textContent =
                        old;
                }},
                1800
            );

        }}

    }}

}}


// =========================================================
// PREVENT DOUBLE TAP / BUTTON FEEDBACK
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    function() {{

        const links =
            document.querySelectorAll(
                "a"
            );

        links.forEach(
            function(link) {{

                link.addEventListener(
                    "click",
                    function() {{

                        link.style.opacity =
                            "0.88";

                    }}
                );

            }}
        );

    }}
);

</script>


</body>
</html>
"""


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
>

<meta
    name="theme-color"
    content="#07070b"
>

<title>
    ixxy VPN
</title>

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

    background:
        radial-gradient(
            circle at 50% 0%,
            #24102f 0%,
            #0d0d14 55%,
            #07070b 100%
        );

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        Arial,
        sans-serif;
}

.box {
    width: 100%;
    max-width: 420px;

    padding: 35px;

    text-align: center;
}

.logo {
    width: 76px;
    height: 76px;

    margin: 0 auto 20px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 25px;

    background:
        linear-gradient(
            135deg,
            #ff4f86,
            #a74eff
        );

    font-size: 32px;

    box-shadow:
        0 25px 60px
        rgba(255,79,134,.3);
}

h1 {
    margin: 0;

    font-size: 35px;
    font-weight: 900;

    letter-spacing: -1.5px;

    background:
        linear-gradient(
            135deg,
            #fff,
            #ff8eae,
            #b890ff
        );

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

p {
    margin-top: 10px;

    color:
        rgba(255,255,255,.38);

    font-size: 12px;
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


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    response = Response(
        '{"service":"ixxy VPN","status":"ok"}',
        mimetype="application/json"
    )

    response.headers.update(
        NO_CACHE_HEADERS
    )

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
            "Database error: "
            + html.escape(str(e)),
            status=500,
            mimetype="text/plain"
        )

    if not user:
        abort(404)

    # ========================================================
    # DATABASE MAPPING
    #
    # 0  user_id
    # 1  username
    # 2  first_name
    # 3  subscription
    # 4  subscription_until
    # 5  subscription_link
    # 6  uuid
    # 7  trial_used
    # 8  pending_days
    # 9  notify
    # 10 accepted_terms
    # 11 created_at
    # ========================================================

    user_id_db = user[0]

    first_name = (
        user[2]
        or user[1]
        or "Пользователь"
    )

    subscription = user[3] or "ixxy"

    subscription_until = (
        user[4]
        or ""
    )

    subscription_link = (
        user[5]
        or ""
    )

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

    response.headers.update(
        NO_CACHE_HEADERS
    )

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
        content = get_subscription_content(
            user_id
        )

    except Exception:
        content = ""

    if not content:
        abort(404)

    response = Response(
        content,
        mimetype="text/plain"
    )

    response.headers.update(
        NO_CACHE_HEADERS
    )

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
        os.getenv(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )