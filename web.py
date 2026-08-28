import os
from urllib.parse import quote

from flask import Flask, Response, abort

from database import get_subscription_content


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

    if not token.startswith(
        SUBSCRIPTION_PREFIX
    ):
        return None

    user_id = token[
        len(SUBSCRIPTION_PREFIX):
    ]

    if not user_id.isdigit():
        return None

    return int(user_id)


# ============================================================
# ГЕНЕРАЦИЯ ССЫЛОК
# ============================================================

def make_links(user_id):

    token = (
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )

    page_url = (
        f"{PUBLIC_SITE_URL}/s/"
        f"{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{token}"
    )

    # Deep link Happ
    happ_url = (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    # Deep link INCY
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
# СТРАНИЦА "МОЯ ПОДПИСКА"
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    content = get_subscription_content(
        user_id
    )

    if not content:

        return (
            """
            <h2 style="
                color:white;
                background:#08080d;
                padding:40px;
                font-family:Arial;
            ">
                ⛔ Подписка не найдена
            </h2>
            """,
            404,
        )

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = make_links(user_id)

    html = f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<meta
    name="theme-color"
    content="#08080d"
>

<title>☂️ ixxy VPN — Моя подписка</title>

<style>

* {{
    box-sizing: border-box;
}}

html {{
    min-height: 100%;
}}

body {{

    margin: 0;

    min-height: 100vh;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    color: white;

    background:
        radial-gradient(
            circle at 15% 15%,
            rgba(255, 0, 153, .35),
            transparent 30%
        ),
        radial-gradient(
            circle at 85% 20%,
            rgba(0, 170, 255, .35),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(123, 47, 255, .35),
            transparent 35%
        ),
        #08080d;

    padding: 20px;

}}

.container {{

    width: 100%;

    max-width: 520px;

    margin:
        0 auto;

    padding-top: 30px;

}}

.logo {{

    width: 76px;

    height: 76px;

    margin:
        0 auto 18px;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 24px;

    font-size: 40px;

    background:
        linear-gradient(
            135deg,
            #ff2bd6,
            #7b2fff,
            #00c6ff
        );

    box-shadow:
        0 15px 45px
        rgba(123,47,255,.45);

}}

.title {{

    text-align: center;

    font-size: 31px;

    font-weight: 800;

    margin-bottom: 7px;

}}

.subtitle {{

    text-align: center;

    color: #a9a9b5;

    font-size: 15px;

    margin-bottom: 24px;

}}

.card {{

    padding: 22px;

    border-radius: 28px;

    background:
        rgba(20,20,29,.82);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 20px 70px
        rgba(0,0,0,.40);

    backdrop-filter:
        blur(20px);

}}

.status {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 17px;

    margin-bottom: 14px;

    border-radius: 19px;

    background:
        linear-gradient(
            135deg,
            rgba(0,255,153,.15),
            rgba(0,180,255,.10)
        );

    border:
        1px solid
        rgba(0,255,180,.16);

}}

.status-left {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.dot {{

    width: 12px;

    height: 12px;

    border-radius: 50%;

    background: #00f59b;

    box-shadow:
        0 0 18px
        rgba(0,245,155,.9);

}}

.status-text {{
    font-weight: 700;
}}

.status-small {{
    color: #8e8e99;
    font-size: 12px;
    margin-top: 3px;
}}

.id {{

    margin:
        14px 0;

    padding: 15px;

    border-radius: 17px;

    background:
        rgba(255,255,255,.055);

    color: #bdbdc7;

    font-size: 14px;

}}

.id code {{
    color: white;
}}

button,
a.button {{

    width: 100%;

    min-height: 55px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 10px;

    margin-top: 11px;

    border: 0;

    border-radius: 17px;

    font-size: 16px;

    font-weight: 800;

    text-decoration: none;

    cursor: pointer;

    transition:
        transform .15s,
        opacity .15s;

}}

button:active,
a.button:active {{
    transform: scale(.97);
}}

.happ {{

    color: white;

    background:
        linear-gradient(
            135deg,
            #ff2bb5,
            #ff5b7d
        );

    box-shadow:
        0 10px 30px
        rgba(255,43,181,.25);

}}

.incy {{

    color: white;

    background:
        linear-gradient(
            135deg,
            #5b5cff,
            #00b8ff
        );

    box-shadow:
        0 10px 30px
        rgba(0,184,255,.22);

}}

.copy {{

    color: white;

    background:
        rgba(255,255,255,.08);

    border:
        1px solid
        rgba(255,255,255,.08);

}}

.open {{

    color: #0b0b0f;

    background: white;

}}

.link-box {{

    margin-top: 18px;

    padding: 14px;

    border-radius: 16px;

    background:
        rgba(0,0,0,.25);

    word-break: break-all;

    color: #9e9eaa;

    font-size: 12px;

    line-height: 1.5;

}}

.footer {{

    text-align: center;

    margin-top: 20px;

    color: #777783;

    font-size: 12px;

}}

</style>

</head>

<body>

<div class="container">

    <div class="logo">
        ☂️
    </div>

    <div class="title">
        Моя подписка
    </div>

    <div class="subtitle">
        ☂️ ixxy VPN
    </div>

    <div class="card">

        <div class="status">

            <div class="status-left">

                <div class="dot"></div>

                <div>

                    <div class="status-text">
                        Подписка доступна
                    </div>

                    <div class="status-small">
                        ID пользователя: {user_id}
                    </div>

                </div>

            </div>

            <div>
                🔐
            </div>

        </div>

        <div class="id">

            🆔 Ваш ID:
            <code>{user_id}</code>

        </div>

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
            onclick="copySubscription()"
        >
            📋 Скопировать ссылку
        </button>

        <a
            class="button open"
            href="{subscription_url}"
        >
            🔗 Открыть подписку
        </a>

        <div class="link-box">
            {subscription_url}
        </div>

    </div>

    <div class="footer">
        ixxy VPN • Персональная подписка
    </div>

</div>

<script>

const subscriptionLink =
    {subscription_url!r};

async function copySubscription() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        alert(
            "✅ Ссылка скопирована!"
        );

    }} catch (error) {{

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

    return html


# ============================================================
# ЧИСТАЯ ПОДПИСКА
# ============================================================

@app.route("/sub/<token>")
def subscription_content(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    content = get_subscription_content(
        user_id
    )

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

    return (
        "☂️ ixxy VPN web server is running"
    )


# ============================================================
# HEALTH
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