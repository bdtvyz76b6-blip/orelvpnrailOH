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
<meta name="viewport" content="width=device-width,initial-scale=1">
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
    padding:25px;
    background:#07070b;
    color:white;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
    text-align:center;
}

.box {
    width:100%;
    max-width:430px;
    padding:35px 25px;
    border-radius:30px;
    background:#15151d;
    border:1px solid rgba(255,255,255,.08);
}

.icon {
    font-size:60px;
    margin-bottom:15px;
}

h1 {
    margin:0 0 10px;
}

p {
    color:#90909c;
    line-height:1.5;
}
</style>
</head>

<body>

<div class="box">

    <div class="icon">⛔</div>

    <h1>Подписка не найдена</h1>

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
    tariff = "Нет подписки"
    days_left = 0
    until_text = "—"

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    if until:

        try:

            from datetime import datetime

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

                status = "🟢 Активна"
                status_class = "active"

            else:

                status = "🔴 Истекла"
                status_class = "inactive"
                days_left = 0

        except Exception:

            pass

    # --------------------------------------------------------
    # Текст дней
    # --------------------------------------------------------

    if days_left == 1:
        days_text = "1 день"
    elif 2 <= days_left <= 4:
        days_text = f"{days_left} дня"
    else:
        days_text = f"{days_left} дней"

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

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<title>☂️ ixxy VPN</title>

<style>

* {{
    box-sizing:border-box;
    -webkit-tap-highlight-color:transparent;
}}

:root {{

    --bg:#07070b;
    --card:rgba(18,18,27,.88);
    --card2:rgba(255,255,255,.045);
    --text:#ffffff;
    --muted:#91919d;
    --border:rgba(255,255,255,.09);
    --shadow:rgba(0,0,0,.48);

}}

body.light {{

    --bg:#f3f4f8;
    --card:rgba(255,255,255,.88);
    --card2:rgba(0,0,0,.045);
    --text:#111118;
    --muted:#696974;
    --border:rgba(0,0,0,.08);
    --shadow:rgba(0,0,0,.12);

}}

html {{
    min-height:100%;
}}

body {{

    margin:0;

    min-height:100vh;

    padding:
        max(16px, env(safe-area-inset-top))
        16px
        max(25px, env(safe-area-inset-bottom));

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
            circle at 5% 0%,
            rgba(255,0,190,.23),
            transparent 31%
        ),
        radial-gradient(
            circle at 95% 5%,
            rgba(0,190,255,.23),
            transparent 31%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(115,50,255,.20),
            transparent 43%
        ),
        var(--bg);

    transition:
        background .3s ease,
        color .3s ease;

    overscroll-behavior:none;

}}

.container {{

    width:100%;

    max-width:520px;

    margin:0 auto;

}}

.topbar {{

    display:flex;

    justify-content:flex-end;

    margin-bottom:4px;

}}

.theme-toggle {{

    width:47px;

    height:47px;

    border:1px solid var(--border);

    border-radius:15px;

    display:flex;

    align-items:center;

    justify-content:center;

    background:var(--card2);

    color:var(--text);

    font-size:20px;

    cursor:pointer;

    backdrop-filter:blur(15px);

    -webkit-backdrop-filter:blur(15px);

    transition:
        transform .15s ease,
        background .3s ease;

}}

.theme-toggle:active {{

    transform:scale(.92);

}}

.logo {{

    width:88px;

    height:88px;

    margin:2px auto 17px;

    border-radius:28px;

    display:flex;

    align-items:center;

    justify-content:center;

    font-size:45px;

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

    text-align:center;

    font-size:30px;

    line-height:1.1;

    font-weight:850;

    letter-spacing:-.6px;

}}

.subtitle {{

    margin:
        8px 0 22px;

    text-align:center;

    color:var(--muted);

    font-size:14px;

}}

.card {{

    padding:17px;

    border-radius:29px;

    background:var(--card);

    border:1px solid var(--border);

    box-shadow:
        0 25px 80px var(--shadow);

    backdrop-filter:blur(25px);

    -webkit-backdrop-filter:blur(25px);

    animation:
        cardIn .45s ease;

}}

@keyframes cardIn {{

    from {{
        opacity:0;
        transform:translateY(10px);
    }}

    to {{
        opacity:1;
        transform:translateY(0);
    }}

}}

.status {{

    padding:17px;

    border-radius:21px;

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

    background:#00f59b;

    box-shadow:
        0 0 18px
        rgba(0,245,155,.9);

}}

.inactive .dot {{

    background:#ff4d61;

    box-shadow:
        0 0 15px
        rgba(255,77,97,.65);

}}

.status-title {{

    font-size:15px;

    font-weight:850;

}}

.status-info {{

    margin-top:3px;

    color:var(--muted);

    font-size:12px;

}}

.lock-icon {{

    font-size:21px;

}}

.info-grid {{

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:10px;

    margin-top:11px;

}}

.info-box {{

    padding:15px;

    border-radius:19px;

    background:var(--card2);

    border:1px solid var(--border);

}}

.info-label {{

    color:var(--muted);

    font-size:11px;

    margin-bottom:5px;

}}

.info-value {{

    color:var(--text);

    font-size:14px;

    font-weight:800;

    word-break:break-word;

}}

.profile {{

    margin-top:10px;

    padding:15px;

    border-radius:19px;

    background:var(--card2);

    border:1px solid var(--border);

}}

.profile-row {{

    display:flex;

    justify-content:space-between;

    gap:15px;

    padding:5px 0;

}}

.profile-label {{

    color:var(--muted);

    font-size:12px;

}}

.profile-value {{

    color:var(--text);

    font-size:12px;

    font-weight:750;

    text-align:right;

    word-break:break-word;

}}

.connect-title {{

    margin:
        21px 2px 8px;

    font-size:14px;

    font-weight:850;

}}

.connect-subtitle {{

    margin:
        0 2px 10px;

    color:var(--muted);

    font-size:12px;

    line-height:1.4;

}}

.button {{

    width:100%;

    min-height:56px;

    margin-top:10px;

    padding:0 17px;

    border:0;

    border-radius:17px;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:9px;

    color:white;

    text-decoration:none;

    font-family:inherit;

    font-size:15px;

    font-weight:850;

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

.main-connect {{

    min-height:62px;

    font-size:17px;

    background:
        linear-gradient(
            135deg,
            #ff25b9,
            #783cff,
            #00bfff
        );

    box-shadow:
        0 13px 35px
        rgba(120,60,255,.28);

}}

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff25b8,
            #ff5d78
        );

}}

.incy {{

    background:
        linear-gradient(
            135deg,
            #654cff,
            #00baff
        );

}}

.copy {{

    background:var(--card2);

    color:var(--text);

    border:1px solid var(--border);

}}

.refresh {{

    background:transparent;

    color:var(--muted);

    border:1px solid var(--border);

}}

.subscription-title {{

    margin:
        20px 2px 8px;

    color:var(--muted);

    font-size:11px;

    font-weight:750;

}}

.subscription {{

    padding:14px;

    border-radius:16px;

    background:
        rgba(0,0,0,.18);

    border:1px solid var(--border);

    color:var(--muted);

    font-size:11px;

    line-height:1.5;

    word-break:break-all;

    user-select:text;

    -webkit-user-select:text;

}}

.light .subscription {{

    background:rgba(0,0,0,.035);

}}

.id {{

    margin-top:10px;

    padding:14px;

    border-radius:17px;

    background:var(--card2);

    border:1px solid var(--border);

    color:var(--muted);

    font-size:12px;

}}

.id code {{

    color:var(--text);

    font-weight:800;

}}

.telegram {{

    margin-top:10px;

    min-height:48px;

    display:flex;

    align-items:center;

    justify-content:center;

    text-decoration:none;

    color:var(--muted);

    font-size:12px;

    font-weight:700;

    border-radius:15px;

    border:1px solid var(--border);

    background:var(--card2);

}}

.footer {{

    margin-top:18px;

    text-align:center;

    color:var(--muted);

    opacity:.7;

    font-size:11px;

}}

.toast {{

    position:fixed;

    left:50%;

    bottom:
        max(22px, env(safe-area-inset-bottom));

    transform:
        translate(-50%,20px);

    width:max-content;

    max-width:calc(100% - 30px);

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

    font-weight:750;

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

@media (max-width:380px) {{

    body {{
        padding-left:12px;
        padding-right:12px;
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

    <div class="logo">
        ☂️
    </div>

    <h1>
        Моя подписка
    </h1>

    <div class="subtitle">
        ixxy VPN • безопасное подключение
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

            <div class="lock-icon">
                🔐
            </div>

        </div>

        <!-- =================================================
             INFO
             ================================================= -->

        <div class="info-grid">

            <div class="info-box">

                <div class="info-label">
                    🎫 Тариф
                </div>

                <div class="info-value">
                    {html.escape(tariff)}
                </div>

            </div>

            <div class="info-box">

                <div class="info-label">
                    📅 Активна до
                </div>

                <div class="info-value">
                    {until_text}
                </div>

            </div>

        </div>

        <div class="info-box" style="margin-top:10px;">

            <div class="info-label">
                ⏳ Осталось
            </div>

            <div class="info-value">
                {days_text}
            </div>

        </div>

        <!-- =================================================
             PROFILE
             ================================================= -->

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

            🆔 Telegram ID:
            <code>{user_id}</code>

        </div>

        <!-- =================================================
             CONNECTION
             ================================================= -->

        <div class="connect-title">
            ⚡ Подключение
        </div>

        <div class="connect-subtitle">
            Выберите приложение для подключения VPN.
        </div>

        <button
            type="button"
            class="button main-connect"
            onclick="openApp('happ')"
        >
            ⚡ Подключить через Happ
        </button>

        <button
            type="button"
            class="button happ"
            onclick="openApp('happ')"
        >
            📲 Добавить в Happ
        </button>

        <button
            type="button"
            class="button incy"
            onclick="openApp('incy')"
        >
            🚀 Добавить в INCY
        </button>

        <button
            type="button"
            class="button copy"
            onclick="copyLink()"
        >
            📋 Скопировать ссылку
        </button>

        <button
            type="button"
            class="button refresh"
            onclick="refreshPage()"
        >
            🔄 Обновить страницу
        </button>

        <!-- =================================================
             LINK
             ================================================= -->

        <div class="subscription-title">
            🔗 ССЫЛКА ПОДПИСКИ
        </div>

        <div class="subscription">
            {safe_subscription_url}
        </div>

        <!-- =================================================
             TELEGRAM
             ================================================= -->

        <a
            class="telegram"
            href="https://t.me/"
        >
            ← Вернуться в Telegram
        </a>

    </div>

    <div class="footer">
        ☂️ ixxy VPN • Ваш персональный VPN
    </div>

</div>

<div
    id="toast"
    class="toast"
></div>

<script>

const subscriptionLink =
    '{js_subscription_url}';

const happUrl =
    '{js_happ_url}';

const incyUrl =
    '{js_incy_url}';

const pageUrl =
    '{js_page_url}';


// ============================================================
// THEME
// ============================================================

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
// OPEN APP
// ============================================================

function openApp(app) {{

    const url =
        app === "happ"
            ? happUrl
            : incyUrl;

    showToast(
        app === "happ"
            ? "⚡ Открываем Happ..."
            : "🚀 Открываем INCY..."
    );

    // --------------------------------------------------------
    // Основная попытка
    // --------------------------------------------------------

    try {{

        window.location.href = url;

    }} catch (e) {{

        console.log(e);

    }}

    // --------------------------------------------------------
    // Дополнительная попытка через iframe
    // --------------------------------------------------------

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

    // --------------------------------------------------------
    // Если приложение не открылось
    // --------------------------------------------------------

    setTimeout(() => {{

        if (!document.hidden) {{

            showToast(
                "⚠️ Приложение не открылось. Скопируйте ссылку."
            );

        }}

    }}, 1600);

}}


// ============================================================
// COPY
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


// ============================================================
// REFRESH
// ============================================================

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
    background:rgba(18,18,27,.88);
    border:1px solid rgba(255,255,255,.08);
    box-shadow:0 25px 80px rgba(0,0,0,.45);
}

.logo {
    width:80px;
    height:80px;
    margin:0 auto 18px;
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