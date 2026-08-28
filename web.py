import os
from urllib.parse import quote

from flask import Flask, Response, abort

from database import get_subscription_content, get_user


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
# ПОЛУЧЕНИЕ USER ID
# ============================================================

def get_user_id_from_token(token):

    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None

    user_id = token[len(SUBSCRIPTION_PREFIX):]

    if not user_id.isdigit():
        return None

    return int(user_id)


# ============================================================
# URL
# ============================================================

def get_urls(user_id):

    token = f"{SUBSCRIPTION_PREFIX}{user_id}"

    page_url = f"{PUBLIC_SITE_URL}/s/{token}"

    subscription_url = f"{PUBLIC_SITE_URL}/sub/{token}"

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
# СТРАНИЦА «МОЯ ПОДПИСКА»
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(token)

    if user_id is None:
        abort(404)

    content = get_subscription_content(user_id)

    if not content:
        return """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">
            <title>ixxy VPN</title>
            <style>
                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #07070b;
                    color: white;
                    font-family: -apple-system,
                        BlinkMacSystemFont,
                        "Segoe UI",
                        Arial;
                }

                .box {
                    margin: 20px;
                    padding: 30px;
                    max-width: 400px;
                    text-align: center;
                    border-radius: 28px;
                    background: #15151d;
                    border: 1px solid rgba(255,255,255,.08);
                }
            </style>
        </head>

        <body>
            <div class="box">
                <div style="font-size:50px">☂️</div>
                <h2>Подписка не найдена</h2>
                <p style="color:#8f8f9c">
                    Проверьте ссылку или обратитесь в поддержку.
                </p>
            </div>
        </body>
        </html>
        """, 404

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    # ========================================================
    # ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    # ========================================================

    user = get_user(user_id)

    username = ""
    first_name = ""
    until = ""

    if user:

        try:
            username = user[1] or ""
        except Exception:
            pass

        try:
            first_name = user[2] or ""
        except Exception:
            pass

        try:
            until = user[4] or ""
        except Exception:
            pass

    # ========================================================
    # СТАТУС
    # ========================================================

    status_text = "🟢 Подписка активна"
    status_class = "active"

    expire_text = "Без ограничения"

    if until:

        try:
            from datetime import datetime

            date = datetime.strptime(
                str(until),
                "%Y-%m-%d"
            )

            expire_text = date.strftime("%d.%m.%Y")

            if date.date() < datetime.now().date():

                status_text = "🔴 Подписка истекла"
                status_class = "expired"

        except Exception:

            expire_text = str(until)

    # ========================================================
    # ИМЯ
    # ========================================================

    display_name = first_name.strip()

    if not display_name:
        display_name = "Пользователь"

    # ========================================================
    # HTML
    # ========================================================

    html = f"""
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
    name="apple-mobile-web-app-capable"
    content="yes"
>

<title>ixxy VPN — Моя подписка</title>


<style>

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color: transparent;
}}

html {{
    background: #07070b;
}}

body {{

    margin: 0;

    min-height: 100vh;

    color: #ffffff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        Arial,
        sans-serif;

    background:

        radial-gradient(
            circle at 0% 0%,
            rgba(255, 35, 190, .20),
            transparent 32%
        ),

        radial-gradient(
            circle at 100% 10%,
            rgba(0, 185, 255, .18),
            transparent 32%
        ),

        radial-gradient(
            circle at 50% 100%,
            rgba(110, 55, 255, .20),
            transparent 40%
        ),

        #07070b;

    overflow-x: hidden;

}}

body::before {{

    content: "";

    position: fixed;

    inset: 0;

    pointer-events: none;

    background:
        linear-gradient(
            120deg,
            transparent,
            rgba(255,255,255,.025),
            transparent
        );

}}

.container {{

    width: 100%;

    max-width: 520px;

    margin: 0 auto;

    padding:
        28px
        18px
        40px;

}}

.topbar {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    margin-bottom: 28px;

}}

.brand {{

    display: flex;

    align-items: center;

    gap: 11px;

    font-size: 17px;

    font-weight: 850;

}}

.brand-icon {{

    width: 38px;

    height: 38px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 13px;

    font-size: 20px;

    background:
        linear-gradient(
            135deg,
            #ff28c8,
            #713cff,
            #00c8ff
        );

    box-shadow:
        0 8px 28px
        rgba(116,60,255,.35);

}}

.online {{

    padding:
        8px 11px;

    border-radius: 100px;

    color: #00f3a0;

    background:
        rgba(0,245,160,.08);

    border:
        1px solid
        rgba(0,245,160,.14);

    font-size: 11px;

    font-weight: 750;

}}

.hero {{

    text-align: center;

    margin-bottom: 25px;

}}

.logo {{

    width: 88px;

    height: 88px;

    margin:
        0 auto 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 27px;

    font-size: 44px;

    background:
        linear-gradient(
            135deg,
            #ff25c8,
            #723dff,
            #00c8ff
        );

    box-shadow:
        0 20px 70px
        rgba(115,60,255,.38);

}}

h1 {{

    margin: 0;

    font-size: 31px;

    line-height: 1.1;

    letter-spacing: -.7px;

}}

.hero-text {{

    margin-top: 9px;

    color: #898995;

    font-size: 14px;

}}

.card {{

    padding: 18px;

    border-radius: 27px;

    background:
        rgba(18,18,27,.84);

    border:
        1px solid
        rgba(255,255,255,.085);

    box-shadow:
        0 25px 80px
        rgba(0,0,0,.42);

    backdrop-filter:
        blur(25px);

    -webkit-backdrop-filter:
        blur(25px);

}}

.status {{

    padding: 18px;

    border-radius: 21px;

    background:
        linear-gradient(
            135deg,
            rgba(0,245,160,.11),
            rgba(0,170,255,.055)
        );

    border:
        1px solid
        rgba(0,245,160,.12);

}}

.status.expired {{

    background:
        rgba(255,55,80,.08);

    border-color:
        rgba(255,55,80,.14);

}}

.status-row {{

    display: flex;

    align-items: center;

    gap: 13px;

}}

.status-icon {{

    width: 42px;

    height: 42px;

    flex-shrink: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 14px;

    background:
        rgba(0,245,160,.12);

    font-size: 20px;

}}

.expired .status-icon {{

    background:
        rgba(255,55,80,.12);

}}

.status-title {{

    font-size: 15px;

    font-weight: 850;

}}

.status-description {{

    margin-top: 4px;

    color: #888894;

    font-size: 12px;

}}

.info-grid {{

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 10px;

    margin-top: 12px;

}}

.info {{

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(255,255,255,.045);

    border:
        1px solid
        rgba(255,255,255,.055);

}}

.info-label {{

    color: #777783;

    font-size: 11px;

    margin-bottom: 6px;

}}

.info-value {{

    font-size: 14px;

    font-weight: 750;

    word-break: break-word;

}}

.buttons {{

    margin-top: 16px;

}}

.button {{

    width: 100%;

    min-height: 58px;

    margin-top: 10px;

    padding:
        0 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 10px;

    border: 0;

    border-radius: 18px;

    color: #ffffff;

    text-decoration: none;

    font-family: inherit;

    font-size: 15px;

    font-weight: 850;

    cursor: pointer;

    transition:
        transform .15s ease,
        opacity .15s ease;

}}

.button:active {{

    transform: scale(.965);

    opacity: .88;

}}

.happ {{

    background:
        linear-gradient(
            135deg,
            #ff22b8,
            #ff587b
        );

    box-shadow:
        0 12px 32px
        rgba(255,35,180,.20);

}}

.incy {{

    background:
        linear-gradient(
            135deg,
            #7048ff,
            #00b9ff
        );

    box-shadow:
        0 12px 32px
        rgba(40,150,255,.18);

}}

.copy {{

    background:
        rgba(255,255,255,.065);

    border:
        1px solid
        rgba(255,255,255,.08);

}}

.link-box {{

    margin-top: 15px;

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(0,0,0,.22);

    border:
        1px solid
        rgba(255,255,255,.055);

}}

.link-label {{

    color: #777783;

    font-size: 11px;

    margin-bottom: 7px;

}}

.link {{

    color: #bdbdc8;

    font-size: 12px;

    line-height: 1.55;

    word-break: break-all;

}}

.tip {{

    margin-top: 14px;

    padding: 15px;

    border-radius: 18px;

    background:
        rgba(255,255,255,.035);

    color: #898995;

    font-size: 12px;

    line-height: 1.55;

}}

.tip b {{

    color: #ffffff;

}}

.footer {{

    padding-top: 25px;

    text-align: center;

    color: #555560;

    font-size: 11px;

}}

.back {{

    margin-top: 14px;

    text-align: center;

}}

.back a {{

    color: #777783;

    text-decoration: none;

    font-size: 12px;

}}

.toast {{

    position: fixed;

    left: 50%;

    bottom: 25px;

    transform:
        translate(-50%, 20px);

    padding:
        12px 17px;

    border-radius: 14px;

    background:
        rgba(25,25,35,.95);

    border:
        1px solid
        rgba(255,255,255,.1);

    box-shadow:
        0 15px 40px
        rgba(0,0,0,.45);

    color: white;

    font-size: 13px;

    font-weight: 700;

    opacity: 0;

    pointer-events: none;

    transition:
        .25s ease;

    z-index: 100;

}}

.toast.show {{

    opacity: 1;

    transform:
        translate(-50%, 0);

}}

@media (max-width: 380px) {{

    .container {{
        padding-left: 14px;
        padding-right: 14px;
    }}

    h1 {{
        font-size: 28px;
    }}

    .card {{
        padding: 14px;
    }}

}}

</style>

</head>


<body>

<div class="container">


    <!-- TOP -->

    <div class="topbar">

        <div class="brand">

            <div class="brand-icon">
                ☂️
            </div>

            ixxy VPN

        </div>

        <div class="online">
            ● ONLINE
        </div>

    </div>


    <!-- HERO -->

    <div class="hero">

        <div class="logo">
            ☂️
        </div>

        <h1>
            Моя подписка
        </h1>

        <div class="hero-text">
            Всё необходимое для подключения VPN
        </div>

    </div>


    <!-- CARD -->

    <div class="card">


        <!-- STATUS -->

        <div class="status {status_class}">

            <div class="status-row">

                <div class="status-icon">
                    {"🔒" if status_class == "active" else "⚠️"}
                </div>

                <div>

                    <div class="status-title">
                        {status_text}
                    </div>

                    <div class="status-description">
                        {display_name}, ваша персональная подписка
                    </div>

                </div>

            </div>

        </div>


        <!-- INFO -->

        <div class="info-grid">

            <div class="info">

                <div class="info-label">
                    Срок действия
                </div>

                <div class="info-value">
                    📅 {expire_text}
                </div>

            </div>


            <div class="info">

                <div class="info-label">
                    ID пользователя
                </div>

                <div class="info-value">
                    🆔 {user_id}
                </div>

            </div>

        </div>


        <!-- BUTTONS -->

        <div class="buttons">


            <a
                class="button happ"
                href="{happ_url}"
            >
                ⚡ Добавить в Happ
            </a>


            <a
                class="button incy"
                href="{incy_url}"
            >
                🚀 Добавить в INCY
            </a>


            <button
                class="button copy"
                onclick="copyLink()"
            >
                📋 Скопировать ссылку
            </button>


        </div>


        <!-- SUBSCRIPTION LINK -->

        <div class="link-box">

            <div class="link-label">
                Ваша персональная ссылка
            </div>

            <div class="link">
                {subscription_url}
            </div>

        </div>


        <!-- TIP -->

        <div class="tip">

            💡 <b>Как подключить?</b><br>

            Нажмите «Добавить в Happ» или
            «Добавить в INCY».
            Если приложение не открылось,
            скопируйте ссылку вручную.

        </div>


    </div>


    <!-- BACK -->

    <div class="back">

        <a
            href="https://t.me/"
        >
            ← Вернуться в Telegram
        </a>

    </div>


    <!-- FOOTER -->

    <div class="footer">

        ixxy VPN • Персональная подписка

    </div>


</div>


<!-- TOAST -->

<div
    id="toast"
    class="toast"
>
    ✅ Ссылка скопирована
</div>


<script>

const subscriptionLink =
    {subscription_url!r};


async function copyLink() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        showToast();

    }} catch (error) {{

        const input =
            document.createElement("textarea");

        input.value =
            subscriptionLink;

        document.body.appendChild(input);

        input.select();

        document.execCommand("copy");

        input.remove();

        showToast();

    }}

}}


function showToast() {{

    const toast =
        document.getElementById("toast");

    toast.classList.add("show");

    setTimeout(
        () => toast.classList.remove("show"),
        1800
    );

}}

</script>


</body>

</html>
"""

    return html


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
            "#profile-title: ⛔ ixxy vpn\n\n"
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
            content="width=device-width, initial-scale=1.0"
        >

        <title>ixxy VPN</title>

        <style>

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #07070b;
            color: white;
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial;
        }

        .box {
            text-align: center;
        }

        .logo {
            font-size: 65px;
        }

        h1 {
            margin-bottom: 8px;
        }

        p {
            color: #777783;
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
            "10000",
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )