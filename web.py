import os
import html
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
                content="width=device-width, initial-scale=1"
            >
            <meta name="theme-color" content="#08080d">
            <title>ixxy VPN</title>
        </head>

        <body style="
            margin:0;
            min-height:100vh;
            display:flex;
            align-items:center;
            justify-content:center;
            background:#08080d;
            color:white;
            font-family:Arial,sans-serif;
            text-align:center;
        ">

            <div>
                <div style="
                    font-size:60px;
                    margin-bottom:20px;
                ">
                    ⛔
                </div>

                <h2>
                    Подписка не найдена
                </h2>

                <p style="
                    color:#888;
                ">
                    Для этого пользователя
                    пока нет активной подписки.
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

    username = html.escape(username)
    first_name = html.escape(first_name)

    # --------------------------------------------------------
    # Безопасные JS-строки
    # --------------------------------------------------------

    js_subscription_url = (
        subscription_url
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )

    js_happ_url = (
        happ_url
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )

    js_incy_url = (
        incy_url
        .replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
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
    content="width=device-width,
    initial-scale=1.0,
    maximum-scale=1.0,
    user-scalable=no"
>

<meta
    name="theme-color"
    content="#08080d"
>

<meta
    name="mobile-web-app-capable"
    content="yes"
>

<title>☂️ ixxy VPN</title>

<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    min-height: 100%;
}}

body {{

    margin: 0;

    min-height: 100vh;

    padding:
        max(18px, env(safe-area-inset-top))
        18px
        max(25px, env(safe-area-inset-bottom));

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 5%,
            rgba(255,0,190,.28),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(0,190,255,.28),
            transparent 32%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(120,40,255,.28),
            transparent 42%
        ),
        #07070b;

    overscroll-behavior: none;
}}

.container {{

    width: 100%;

    max-width: 520px;

    margin: 0 auto;

}}

.logo {{

    width: 82px;

    height: 82px;

    margin:
        12px auto 16px;

    border-radius: 26px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 42px;

    background:
        linear-gradient(
            135deg,
            #ff28ce,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 18px 55px
        rgba(117,60,255,.42);

}}

h1 {{

    margin: 0;

    text-align: center;

    font-size: 30px;

    line-height: 1.1;

    font-weight: 850;

}}

.subtitle {{

    margin:
        8px 0 25px;

    text-align: center;

    color: #9696a3;

    font-size: 15px;

}}

.card {{

    padding: 18px;

    border-radius: 28px;

    background:
        rgba(18,18,27,.88);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 25px 80px
        rgba(0,0,0,.48);

    backdrop-filter:
        blur(24px);

    -webkit-backdrop-filter:
        blur(24px);

}}

.status {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 16px;

    border-radius: 20px;

    background:
        linear-gradient(
            135deg,
            rgba(0,255,165,.14),
            rgba(0,170,255,.08)
        );

    border:
        1px solid
        rgba(0,255,180,.14);

}}

.status-left {{

    display: flex;

    align-items: center;

    gap: 12px;

}}

.dot {{

    width: 12px;

    height: 12px;

    flex-shrink: 0;

    border-radius: 50%;

    background: #00f59b;

    box-shadow:
        0 0 18px
        rgba(0,245,155,.9);

}}

.status-title {{

    font-size: 15px;

    font-weight: 800;

}}

.status-info {{

    margin-top: 3px;

    color: #8d8d99;

    font-size: 12px;

}}

.profile {{

    margin-top: 12px;

    padding: 15px 16px;

    border-radius: 18px;

    background:
        rgba(255,255,255,.045);

}}

.profile-row {{

    display: flex;

    justify-content: space-between;

    gap: 15px;

    padding: 5px 0;

}}

.profile-label {{

    color: #858591;

    font-size: 13px;

}}

.profile-value {{

    color: white;

    font-size: 13px;

    font-weight: 700;

    text-align: right;

    word-break: break-word;

}}

.id {{

    margin-top: 12px;

    padding: 15px;

    border-radius: 17px;

    background:
        rgba(255,255,255,.055);

    color: #a8a8b3;

    font-size: 14px;

}}

.id code {{

    color: white;

    font-weight: 700;

}}

.button {{

    width: 100%;

    min-height: 56px;

    margin-top: 11px;

    padding: 0 18px;

    border: 0;

    border-radius: 17px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 9px;

    color: white;

    text-decoration: none;

    font-family: inherit;

    font-size: 16px;

    font-weight: 800;

    cursor: pointer;

    touch-action: manipulation;

    transition:
        transform .12s ease,
        opacity .12s ease;

}}

.button:active {{

    transform: scale(.97);

    opacity: .85;

}}

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff25b8,
            #ff5d78
        );

    box-shadow:
        0 10px 30px
        rgba(255,37,184,.25);

}}

.incy {{

    background:
        linear-gradient(
            135deg,
            #654cff,
            #00baff
        );

    box-shadow:
        0 10px 30px
        rgba(0,186,255,.22);

}}

.copy {{

    background:
        rgba(255,255,255,.08);

    border:
        1px solid
        rgba(255,255,255,.09);

}}

.subscription-title {{

    margin:
        20px 2px 8px;

    color: #858591;

    font-size: 12px;

    font-weight: 700;

}}

.subscription {{

    padding: 14px;

    border-radius: 16px;

    background:
        rgba(0,0,0,.25);

    color: #9696a2;

    font-size: 12px;

    line-height: 1.5;

    word-break: break-all;

    user-select: text;

    -webkit-user-select: text;

}}

.footer {{

    margin-top: 20px;

    padding-bottom: 10px;

    text-align: center;

    color: #70707c;

    font-size: 12px;

}}

.toast {{

    position: fixed;

    left: 50%;

    bottom: 25px;

    transform:
        translate(-50%, 20px);

    padding:
        13px 18px;

    border-radius: 15px;

    background:
        rgba(30,30,40,.95);

    border:
        1px solid
        rgba(255,255,255,.1);

    box-shadow:
        0 15px 45px
        rgba(0,0,0,.45);

    color: white;

    font-size: 14px;

    font-weight: 700;

    opacity: 0;

    pointer-events: none;

    transition:
        opacity .2s,
        transform .2s;

    z-index: 9999;

}}

.toast.show {{

    opacity: 1;

    transform:
        translate(-50%, 0);

}}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        ☂️
    </div>

    <h1>
        Моя подписка
    </h1>

    <div class="subtitle">
        ☂️ ixxy VPN
    </div>

    <div class="card">

        <div class="status">

            <div class="status-left">

                <div class="dot"></div>

                <div>

                    <div class="status-title">
                        Подписка доступна
                    </div>

                    <div class="status-info">
                        Ваш персональный VPN
                    </div>

                </div>

            </div>

            <div>
                🔐
            </div>

        </div>

        <div class="profile">

            <div class="profile-row">

                <div class="profile-label">
                    👤 Пользователь
                </div>

                <div class="profile-value">
                    {first_name}
                </div>

            </div>

            <div class="profile-row">

                <div class="profile-label">
                    @ Username
                </div>

                <div class="profile-value">
                    @{username}
                </div>

            </div>

        </div>

        <div class="id">

            🆔 Ваш ID:
            <code>{user_id}</code>

        </div>

        <!-- =================================================
             HAPP
             ================================================= -->

        <button
            type="button"
            class="button happ"
            onclick="openApp('happ')"
        >
            ⚡ Добавить в Happ
        </button>

        <!-- =================================================
             INCY
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
            class="button copy"
            onclick="copyLink()"
        >
            📋 Скопировать ссылку
        </button>

        <div class="subscription-title">
            🔗 Ссылка подписки
        </div>

        <div class="subscription">
            {html.escape(subscription_url)}
        </div>

    </div>

    <div class="footer">
        ixxy VPN • Моя подписка
    </div>

</div>

<div
    id="toast"
    class="toast"
>
</div>

<script>

const subscriptionLink =
    '{js_subscription_url}';

const happUrl =
    '{js_happ_url}';

const incyUrl =
    '{js_incy_url}';


// ============================================================
// TOAST
// ============================================================

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


// ============================================================
// ОТКРЫТИЕ VPN-ПРИЛОЖЕНИЯ
// ============================================================

function openApp(app) {{

    const url =
        app === "happ"
            ? happUrl
            : incyUrl;

    // --------------------------------------------------------
    // В Telegram WebView сначала пытаемся открыть приложение
    // --------------------------------------------------------

    let opened = false;

    const iframe =
        document.createElement("iframe");

    iframe.style.display = "none";

    iframe.src = url;

    document.body.appendChild(iframe);

    setTimeout(() => {{

        try {{
            document.body.removeChild(iframe);
        }} catch (e) {{}}

    }}, 1500);

    // --------------------------------------------------------
    // Дополнительная попытка через location
    // --------------------------------------------------------

    try {{

        window.location.href = url;

        opened = true;

    }} catch (e) {{

        opened = false;

    }}

    // --------------------------------------------------------
    // Если приложение не установлено
    // --------------------------------------------------------

    setTimeout(() => {{

        if (!document.hidden) {{

            if (app === "happ") {{

                showToast(
                    "⚠️ Happ не открылся. Скопируйте ссылку подписки."
                );

            }} else {{

                showToast(
                    "⚠️ INCY не открылся. Скопируйте ссылку подписки."
                );

            }}

        }}

    }}, 1200);

}}


// ============================================================
// КОПИРОВАНИЕ
// ============================================================

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

        // Продолжаем fallback
    }}

    try {{

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

        document.execCommand(
            "copy"
        );

        document.body.removeChild(
            textarea
        );

        showToast(
            "✅ Ссылка скопирована!"
        );

    }} catch (e) {{

        prompt(
            "Скопируйте ссылку:",
            subscriptionLink
        );

    }}

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

    content = get_subscription_content(user_id)

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
            content="width=device-width,
            initial-scale=1.0"
        >
        <meta
            name="theme-color"
            content="#08080d"
        >
        <title>ixxy VPN</title>
    </head>

    <body style="
        margin:0;
        min-height:100vh;
        display:flex;
        align-items:center;
        justify-content:center;
        background:#08080d;
        color:white;
        font-family:Arial,sans-serif;
        text-align:center;
    ">

        <div>

            <div style="
                font-size:60px;
                margin-bottom:15px;
            ">
                ☂️
            </div>

            <h1>
                ixxy VPN
            </h1>

            <p style="color:#888;">
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