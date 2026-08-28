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

def get_user_id_from_token(
    token
):

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
# URL
# ============================================================

def get_urls(user_id):

    token = (
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )

    page_url = (
        f"{PUBLIC_SITE_URL}"
        f"/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}"
        f"/sub/{token}"
    )

    # Happ
    happ_url = (
        "happ://add/"
        + quote(
            subscription_url,
            safe=""
        )
    )

    # INCY
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
# ВЕБ-ПРИЛОЖЕНИЕ
# ============================================================

@app.route(
    "/s/<token>"
)
def subscription_page(
    token
):

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
    ) = get_urls(
        user_id
    )

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

<title>
☂️ ixxy VPN — Моя подписка
</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;

    min-height: 100vh;

    padding: 20px;

    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 10%,
            rgba(255, 0, 180, .32),
            transparent 32%
        ),
        radial-gradient(
            circle at 90% 15%,
            rgba(0, 180, 255, .32),
            transparent 32%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(120, 40, 255, .30),
            transparent 40%
        ),
        #07070b;

}}

.container {{

    width: 100%;

    max-width: 520px;

    margin: auto;

    padding-top: 25px;

}}

.logo {{

    width: 78px;

    height: 78px;

    margin:
        0 auto 17px;

    border-radius: 25px;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 40px;

    background:
        linear-gradient(
            135deg,
            #ff28ce,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 18px 55px
        rgba(117,60,255,.40);

}}

h1 {{

    margin: 0;

    text-align: center;

    font-size: 30px;

    font-weight: 850;

}}

.subtitle {{

    margin:
        7px 0 25px;

    text-align: center;

    color: #9999a6;

    font-size: 15px;

}}

.card {{

    padding: 21px;

    border-radius: 28px;

    background:
        rgba(19,19,28,.82);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 25px 80px
        rgba(0,0,0,.48);

    backdrop-filter:
        blur(22px);

}}

.status {{

    display: flex;

    align-items: center;

    justify-content: space-between;

    padding: 17px;

    border-radius: 19px;

    background:
        linear-gradient(
            135deg,
            rgba(0,255,165,.14),
            rgba(0,170,255,.08)
        );

    border:
        1px solid
        rgba(0,255,180,.13);

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

.status-title {{

    font-size: 15px;

    font-weight: 800;

}}

.status-info {{

    margin-top: 3px;

    color: #8d8d99;

    font-size: 12px;

}}

.id {{

    margin-top: 13px;

    padding: 15px;

    border-radius: 17px;

    background:
        rgba(255,255,255,.055);

    color: #a8a8b3;

    font-size: 14px;

}}

.id code {{
    color: white;
}}

.button {{

    width: 100%;

    min-height: 56px;

    margin-top: 11px;

    border: 0;

    border-radius: 17px;

    display: flex;

    align-items: center;

    justify-content: center;

    gap: 9px;

    color: white;

    text-decoration: none;

    font-size: 16px;

    font-weight: 800;

    cursor: pointer;

    transition:
        transform .15s,
        opacity .15s;

}}

.button:active {{

    transform:
        scale(.97);

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
        rgba(255,37,184,.24);

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
        rgba(255,255,255,.08);

}}

.subscription {{

    margin-top: 18px;

    padding: 14px;

    border-radius: 16px;

    background:
        rgba(0,0,0,.25);

    color: #9696a2;

    font-size: 12px;

    line-height: 1.5;

    word-break: break-all;

}}

.footer {{

    margin-top: 20px;

    text-align: center;

    color: #70707c;

    font-size: 12px;

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
            onclick="copyLink()"
        >
            📋 Скопировать ссылку
        </button>

        <div class="subscription">
            🔗 {subscription_url}
        </div>

    </div>

    <div class="footer">
        ixxy VPN • Моя подписка
    </div>

</div>

<script>

const subscriptionLink =
    {subscription_url!r};

async function copyLink() {{

    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );

        alert(
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

    return html


# ============================================================
# ЧИСТАЯ ПОДПИСКА
# ============================================================

@app.route(
    "/sub/<token>"
)
def subscription_content(
    token
):

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