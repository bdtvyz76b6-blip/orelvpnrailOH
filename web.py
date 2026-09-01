import os
import html
import json
import base64
from datetime import datetime
from urllib.parse import quote

import requests
from flask import Flask, Response, abort


from database import (
    get_subscription_content,
    get_user,
)


# ============================================================
# IXXY VPN
# PREMIUM WEB SUBSCRIPTION SERVER
# ============================================================

app = Flask(__name__)


# ============================================================
# CONFIG
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")


SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()


TELEGRAM_URL = os.getenv(
    "TELEGRAM_URL",
    "https://t.me/orelvpntopbot",
).strip()


# ============================================================
# HAPP CRYPT5
# ============================================================
#
# ВАЖНО:
#
# HAPP_CRYPT5_API_URL должен указывать на сервис/API,
# который принимает обычную HTTPS-ссылку подписки
# и возвращает готовую:
#
#     happ://crypt5/....
#
# Сам алгоритм Crypt5 здесь не реализован вручную.
#
# Пример переменной Render:
#
# HAPP_CRYPT5_API_URL=https://....../encrypt
#
# Если API отсутствует или временно недоступен,
# сайт автоматически использует happ://add/ как fallback.
#
# ============================================================

HAPP_CRYPT5_API_URL = os.getenv(
    "HAPP_CRYPT5_API_URL",
    "",
).strip()


HAPP_CRYPT5_TIMEOUT = int(
    os.getenv(
        "HAPP_CRYPT5_TIMEOUT",
        "8",
    )
)


# ============================================================
# TOKEN
# ============================================================

def get_user_id_from_token(token):

    if not token:
        return None

    token = str(token).strip()

    if not token.startswith(
        SUBSCRIPTION_PREFIX
    ):
        return None

    user_id = token[
        len(SUBSCRIPTION_PREFIX):
    ]

    if not user_id.isdigit():
        return None

    try:
        return int(user_id)

    except Exception:
        return None


def get_token(user_id):

    return (
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )


# ============================================================
# CRYPT5 API RESPONSE PARSER
# ============================================================

def extract_crypt5_response(data):

    if data is None:
        return ""

    # --------------------------------------------------------
    # Plain string
    # --------------------------------------------------------

    if isinstance(data, str):

        value = data.strip()

        if value.startswith(
            "happ://crypt5/"
        ):
            return value

        # Иногда API может вернуть JSON
        # в виде строки.

        try:

            decoded = json.loads(value)

            result = extract_crypt5_response(
                decoded
            )

            if result:
                return result

        except Exception:
            pass

        return ""


    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(data, dict):

        possible_keys = (
            "url",
            "link",
            "result",
            "data",
            "encrypted",
            "encrypted_url",
            "crypt5",
            "happ",
        )

        for key in possible_keys:

            value = data.get(key)

            result = extract_crypt5_response(
                value
            )

            if result:
                return result

        return ""


    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    if isinstance(data, list):

        for item in data:

            result = extract_crypt5_response(
                item
            )

            if result:
                return result

    return ""


# ============================================================
# GENERATE HAPP CRYPT5
# ============================================================

def generate_happ_crypt5(
    subscription_url
):

    if not subscription_url:
        return ""


    # --------------------------------------------------------
    # Без API Crypt5 создать корректно невозможно.
    # --------------------------------------------------------

    if not HAPP_CRYPT5_API_URL:

        return ""


    try:

        # ----------------------------------------------------
        # Основной формат запроса.
        #
        # Большинство подобных API принимают:
        #
        # {
        #     "url": "https://..."
        # }
        #
        # ----------------------------------------------------

        response = requests.post(

            HAPP_CRYPT5_API_URL,

            json={
                "url": subscription_url,
            },

            timeout=HAPP_CRYPT5_TIMEOUT,

        )


        if response.status_code != 200:

            return ""


        content_type = (
            response.headers
            .get(
                "Content-Type",
                ""
            )
            .lower()
        )


        # ----------------------------------------------------
        # JSON
        # ----------------------------------------------------

        if "json" in content_type:

            try:

                data = response.json()

            except Exception:

                return ""

            return extract_crypt5_response(
                data
            )


        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        text = (
            response.text
            .strip()
        )

        return extract_crypt5_response(
            text
        )


    except Exception:

        return ""


# ============================================================
# URLS
# ============================================================

def get_urls(user_id):

    token = get_token(
        user_id
    )


    page_url = (
        f"{PUBLIC_SITE_URL}"
        f"/s/{token}"
    )


    subscription_url = (
        f"{PUBLIC_SITE_URL}"
        f"/sub/{token}"
    )


    # --------------------------------------------------------
    # HAPP CRYPT5
    # --------------------------------------------------------

    crypt5_url = generate_happ_crypt5(
        subscription_url
    )


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not crypt5_url:

        happ_url = (
            "happ://add/"
            + quote(
                subscription_url,
                safe=""
            )
        )

    else:

        happ_url = crypt5_url


    # --------------------------------------------------------
    # INCY
    # --------------------------------------------------------

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
# JS ESCAPE
# ============================================================

def js_escape(value):

    return (
        str(value)
        .replace(
            "\\",
            "\\\\"
        )
        .replace(
            "'",
            "\\'"
        )
        .replace(
            '"',
            '\\"'
        )
        .replace(
            "\n",
            "\\n"
        )
        .replace(
            "\r",
            "\\r"
        )
        .replace(
            "</",
            "<\\/"
        )
    )


# ============================================================
# DAYS
# ============================================================

def days_word(days):

    try:

        days = abs(
            int(days)
        )

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
# DATE
# ============================================================

def parse_subscription_date(value):

    if not value:

        return None


    value = str(
        value
    ).strip()


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

            return datetime.strptime(
                value,
                fmt
            ).date()

        except Exception:

            pass


    return None


# ============================================================
# USER DATA
# ============================================================

def get_user_data(user_id):

    try:

        user = get_user(
            user_id
        )

    except Exception:

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

def no_subscription_page():

    telegram = html.escape(
        TELEGRAM_URL
    )


    return f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="
        width=device-width,
        initial-scale=1.0
    "
>

<meta
    name="theme-color"
    content="#07070b"
>

<title>
    ixxy VPN
</title>

<style>

* {{
    box-sizing:
        border-box;
}}

html,
body {{
    margin:
        0;

    min-height:
        100%;
}}

body {{

    min-height:
        100vh;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    padding:
        20px;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255,0,190,.22),
            transparent 35%
        ),
        radial-gradient(
            circle at 90% 10%,
            rgba(0,180,255,.18),
            transparent 35%
        ),
        #07070b;

    color:
        white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}}

.card {{

    width:
        100%;

    max-width:
        430px;

    padding:
        35px 25px;

    border-radius:
        32px;

    text-align:
        center;

    background:
        rgba(17,18,27,.82);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.5);

    backdrop-filter:
        blur(30px);

    -webkit-backdrop-filter:
        blur(30px);
}}

.logo {{

    width:
        88px;

    height:
        88px;

    margin:
        0 auto 22px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        28px;

    font-size:
        44px;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #743cff,
            #00c8ff
        );

    box-shadow:
        0 20px 65px
        rgba(120,60,255,.38);
}}

h1 {{

    margin:
        0;

    font-size:
        29px;

    font-weight:
        900;
}}

p {{

    margin:
        10px 0 0;

    color:
        #9295a4;

    line-height:
        1.55;
}}

.button {{

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    min-height:
        55px;

    margin-top:
        24px;

    border-radius:
        18px;

    color:
        white;

    text-decoration:
        none;

    font-weight:
        900;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #743cff
        );
}}

</style>

</head>

<body>

<div class="card">

    <div class="logo">
        ☂️
    </div>

    <h1>
        Подписка не найдена
    </h1>

    <p>
        Для этого Telegram ID пока
        нет активной подписки ixxy VPN.
    </p>

    <a
        class="button"
        href="{telegram}"
    >
        🤖 Открыть Telegram-бота
    </a>

</div>

</body>

</html>
"""


# ============================================================
# PREMIUM PAGE
# ============================================================

@app.route(
    "/s/<token>"
)
def subscription_page(token):

    # --------------------------------------------------------
    # TOKEN
    # --------------------------------------------------------

    user_id = get_user_id_from_token(
        token
    )


    if user_id is None:

        abort(404)


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    try:

        content = (
            get_subscription_content(
                user_id
            )
        )

    except Exception:

        content = ""


    if not content:

        return Response(

            no_subscription_page(),

            status=404,

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


    (
        user,
        username,
        first_name,
        subscription,
        until,
    ) = get_user_data(
        user_id
    )


    # ========================================================
    # TARIFF
    # ========================================================

    subscription_lower = (
        subscription.lower()
        if subscription
        else ""
    )


    if subscription_lower in (

        "vip",
        "ixxy vip",
        "premium vip",

    ):

        tariff = "ixxy VIP"

        tariff_icon = "👑"


    elif subscription_lower in (

        "trial",
        "пробный",
        "пробный период",

    ):

        tariff = "Пробный период"

        tariff_icon = "🎁"


    elif subscription_lower in (

        "active",
        "premium",
        "standard",
        "wifi",
        "👑 орёл vpn",
        "☂️ ixxy vpn",
        "ixxy vpn",

    ):

        tariff = "ixxy VPN"

        tariff_icon = "☂️"


    else:

        if (
            subscription
            and
            subscription != "none"
        ):

            tariff = subscription

        else:

            tariff = "ixxy VPN"


        tariff_icon = "☂️"


    # ========================================================
    # EXPIRATION
    # ========================================================

    expire_date = (
        parse_subscription_date(
            until
        )
    )


    today = datetime.now().date()


    days_left = 0


    if expire_date:

        days_left = (
            expire_date
            - today
        ).days


    if (
        days_left >= 0
        and expire_date
    ):

        active = True

        status_text = (
            "Подписка активна"
        )

        status_description = (
            "Защищённое VPN-подключение"
        )

        status_class = "active"

        status_icon = "✓"


    else:

        active = False

        status_text = (
            "Подписка истекла"
        )

        status_description = (
            "Продлите подписку для подключения"
        )

        status_class = "inactive"

        status_icon = "!"

        days_left = 0


    # ========================================================
    # DATE
    # ========================================================

    if expire_date:

        until_text = (
            expire_date.strftime(
                "%d.%m.%Y"
            )
        )

    else:

        until_text = "—"


    days_text = (
        f"{days_left} "
        f"{days_word(days_left)}"
    )


    # ========================================================
    # URLS
    # ========================================================

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(
        user_id
    )


    # ========================================================
    # SAFE VALUES
    # ========================================================

    safe_username = html.escape(
        username
    )

    safe_first_name = html.escape(
        first_name
    )

    safe_tariff = html.escape(
        tariff
    )

    safe_until = html.escape(
        until_text
    )

    safe_subscription_url = html.escape(
        happ_url
    )


    # ========================================================
    # JS
    # ========================================================

    js_subscription_url = js_escape(
        happ_url
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

    js_telegram_url = js_escape(
        TELEGRAM_URL
    )


    # ========================================================
    # PROGRESS
    # ========================================================

    if days_left <= 0:

        progress = 0

    elif days_left >= 365:

        progress = 100

    else:

        progress = min(

            100,

            max(

                15,

                int(
                    days_left
                    / 365
                    * 100
                )

            )

        )


    # ========================================================
    # HTML
    # ========================================================

    page = f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="
        width=device-width,
        initial-scale=1.0,
        maximum-scale=1.0,
        user-scalable=no,
        viewport-fit=cover
"
/>

<meta
    name="theme-color"
    content="#07070c"
/>

<meta
    name="mobile-web-app-capable"
    content="yes"
/>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
/>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
/>

<meta
    name="description"
    content="ixxy VPN — персональная подписка"
/>

<title>
☂️ ixxy VPN — Моя подписка
</title>

<style>

/* ============================================================
   ROOT
============================================================ */

* {{

    box-sizing:
        border-box;

    -webkit-tap-highlight-color:
        transparent;
}}

html {{

    min-height:
        100%;

    scroll-behavior:
        smooth;
}}

body {{

    margin:
        0;

    min-height:
        100vh;

    min-height:
        100dvh;

    color:
        #ffffff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        #06070b;

    overflow-x:
        hidden;

    -webkit-font-smoothing:
        antialiased;
}}


/* ============================================================
   VARIABLES
============================================================ */

:root {{

    --bg:
        #06070b;

    --surface:
        rgba(16,17,24,.76);

    --surface-2:
        rgba(255,255,255,.045);

    --surface-3:
        rgba(255,255,255,.065);

    --border:
        rgba(255,255,255,.09);

    --border-light:
        rgba(255,255,255,.13);

    --text:
        #ffffff;

    --muted:
        #9295a4;

    --purple:
        #7c5cff;

    --purple-2:
        #9c7cff;

    --pink:
        #ff35bd;

    --blue:
        #22b8ff;

    --green:
        #4bea9b;

    --red:
        #ff536d;
}}

body.light {{

    --bg:
        #f2f3f7;

    --surface:
        rgba(255,255,255,.82);

    --surface-2:
        rgba(0,0,0,.045);

    --surface-3:
        rgba(0,0,0,.065);

    --border:
        rgba(0,0,0,.08);

    --border-light:
        rgba(0,0,0,.12);

    --text:
        #101116;

    --muted:
        #6d707b;
}}


/* ============================================================
   BACKGROUND
============================================================ */

.background {{

    position:
        fixed;

    inset:
        0;

    overflow:
        hidden;

    pointer-events:
        none;

    z-index:
        0;

    background:
        radial-gradient(
            circle at 15% -5%,
            rgba(255,30,190,.17),
            transparent 31%
        ),
        radial-gradient(
            circle at 100% 5%,
            rgba(20,185,255,.15),
            transparent 30%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(110,70,255,.13),
            transparent 42%
        ),
        var(--bg);
}}

.orb {{

    position:
        absolute;

    border-radius:
        50%;

    filter:
        blur(90px);

    opacity:
        .42;

    animation:
        orbFloat
        12s
        ease-in-out
        infinite;
}}

.orb-one {{

    width:
        330px;

    height:
        330px;

    top:
        -180px;

    left:
        -100px;

    background:
        #a328ff;
}}

.orb-two {{

    width:
        280px;

    height:
        280px;

    right:
        -150px;

    top:
        240px;

    background:
        #007dff;

    animation-delay:
        -4s;
}}

.orb-three {{

    width:
        260px;

    height:
        260px;

    bottom:
        -170px;

    left:
        25%;

    background:
        #ff1ba8;

    animation-delay:
        -7s;
}}

@keyframes orbFloat {{

    0%,
    100% {{
        transform:
            translate3d(0,0,0)
            scale(1);
    }}

    50% {{
        transform:
            translate3d(20px,-18px,0)
            scale(1.08);
    }}
}}


/* ============================================================
   GRID
============================================================ */

.grid-overlay {{

    position:
        absolute;

    inset:
        0;

    opacity:
        .17;

    background-image:
        linear-gradient(
            rgba(255,255,255,.025)
            1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,.025)
            1px,
            transparent 1px
        );

    background-size:
        45px 45px;

    mask-image:
        linear-gradient(
            to bottom,
            black,
            transparent 75%
        );
}}


/* ============================================================
   APP
============================================================ */

.app {{

    position:
        relative;

    z-index:
        1;

    width:
        100%;

    max-width:
        560px;

    margin:
        0 auto;

    padding:
        max(
            16px,
            env(safe-area-inset-top)
        )
        15px
        max(
            30px,
            env(safe-area-inset-bottom)
        );
}}


/* ============================================================
   TOPBAR
============================================================ */

.topbar {{

    height:
        54px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    margin-bottom:
        7px;
}}

.top-brand {{

    display:
        flex;

    align-items:
        center;

    gap:
        9px;
}}

.mini-logo {{

    width:
        38px;

    height:
        38px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        13px;

    background:
        linear-gradient(
            135deg,
            #ff27be,
            #7841ff,
            #00c8ff
        );

    box-shadow:
        0 8px 25px
        rgba(120,60,255,.25);

    font-size:
        19px;
}}

.top-brand strong {{

    font-size:
        15px;

    font-weight:
        850;

    letter-spacing:
        -.3px;
}}

.top-brand small {{

    display:
        block;

    margin-top:
        2px;

    color:
        var(--muted);

    font-size:
        9px;

    font-weight:
        600;
}}

.theme {{

    width:
        43px;

    height:
        43px;

    border:
        1px solid
        var(--border);

    border-radius:
        14px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    color:
        var(--text);

    background:
        var(--surface-2);

    backdrop-filter:
        blur(20px);

    -webkit-backdrop-filter:
        blur(20px);

    font-size:
        18px;

    cursor:
        pointer;

    transition:
        transform .15s ease;
}}

.theme:active {{

    transform:
        scale(.9);
}}


/* ============================================================
   HERO
============================================================ */

.hero {{

    position:
        relative;

    padding:
        27px 18px 23px;

    text-align:
        center;

    border:
        1px solid
        var(--border);

    border-radius:
        32px;

    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.065),
            rgba(255,255,255,.025)
        );

    backdrop-filter:
        blur(30px);

    -webkit-backdrop-filter:
        blur(30px);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.38),
        inset
        0 1px 0
        rgba(255,255,255,.06);

    overflow:
        hidden;

    animation:
        heroIn
        .55s
        ease
        both;
}}

.hero::before {{

    content:
        "";

    position:
        absolute;

    width:
        170px;

    height:
        170px;

    top:
        -90px;

    left:
        50%;

    transform:
        translateX(-50%);

    border-radius:
        50%;

    background:
        #7a4cff;

    filter:
        blur(70px);

    opacity:
        .28;

    pointer-events:
        none;
}}

@keyframes heroIn {{

    from {{
        opacity:
            0;

        transform:
            translateY(16px)
            scale(.985);
    }}

    to {{
        opacity:
            1;

        transform:
            translateY(0)
            scale(1);
    }}
}}

.hero-logo {{

    position:
        relative;

    width:
        82px;

    height:
        82px;

    margin:
        0 auto 17px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        27px;

    background:
        linear-gradient(
            145deg,
            #ff25bd,
            #743cff 52%,
            #00c9ff
        );

    box-shadow:
        0 20px 60px
        rgba(112,61,255,.38);

    font-size:
        39px;

    animation:
        logoPulse
        5s
        ease-in-out
        infinite;
}}

@keyframes logoPulse {{

    0%,
    100% {{
        transform:
            translateY(0);
    }}

    50% {{
        transform:
            translateY(-4px);
    }}
}}

.hero h1 {{

    position:
        relative;

    margin:
        0;

    font-size:
        31px;

    line-height:
        1;

    letter-spacing:
        -1px;

    font-weight:
        900;
}}

.hero-subtitle {{

    position:
        relative;

    margin:
        9px 0 17px;

    color:
        var(--muted);

    font-size:
        13px;

    line-height:
        1.5;
}}

.status-pill {{

    position:
        relative;

    width:
        fit-content;

    margin:
        0 auto;

    padding:
        8px 13px;

    display:
        flex;

    align-items:
        center;

    gap:
        7px;

    border-radius:
        999px;

    font-size:
        11px;

    font-weight:
        800;

    border:
        1px solid
        rgba(74,234,155,.18);

    background:
        rgba(74,234,155,.08);

    color:
        #89f2bb;
}}

.status-pill.inactive {{

    border-color:
        rgba(255,83,109,.2);

    background:
        rgba(255,83,109,.08);

    color:
        #ff8798;
}}

.status-dot {{

    width:
        7px;

    height:
        7px;

    border-radius:
        50%;

    background:
        var(--green);

    box-shadow:
        0 0 14px
        rgba(74,234,155,.9);
}}

.status-pill.inactive
.status-dot {{

    background:
        var(--red);

    box-shadow:
        0 0 14px
        rgba(255,83,109,.8);
}}


/* ============================================================
   MAIN CARD
============================================================ */

.panel {{

    margin-top:
        12px;

    padding:
        14px;

    border:
        1px solid
        var(--border);

    border-radius:
        30px;

    background:
        var(--surface);

    backdrop-filter:
        blur(30px);

    -webkit-backdrop-filter:
        blur(30px);

    box-shadow:
        0 25px 90px
        rgba(0,0,0,.34);

    animation:
        panelIn
        .6s
        .08s
        ease
        both;
}}

@keyframes panelIn {{

    from {{
        opacity:
            0;

        transform:
            translateY(15px);
    }}

    to {{
        opacity:
            1;

        transform:
            translateY(0);
    }}
}}


/* ============================================================
   HEADER
============================================================ */

.panel-header {{

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    padding:
        7px 5px 12px;
}}

.panel-title strong {{

    display:
        block;

    font-size:
        16px;

    font-weight:
        900;
}}

.panel-title span {{

    display:
        block;

    margin-top:
        4px;

    color:
        var(--muted);

    font-size:
        10px;
}}

.secure-badge {{

    padding:
        7px 9px;

    border-radius:
        11px;

    color:
        #b7adff;

    background:
        rgba(124,92,255,.1);

    border:
        1px solid
        rgba(124,92,255,.16);

    font-size:
        10px;

    font-weight:
        800;
}}


/* ============================================================
   STATS
============================================================ */

.stats {{

    display:
        grid;

    grid-template-columns:
        1fr 1fr;

    gap:
        9px;
}}

.stat {{

    position:
        relative;

    min-height:
        96px;

    padding:
        14px;

    border-radius:
        21px;

    background:
        var(--surface-2);

    border:
        1px solid
        var(--border);

    overflow:
        hidden;
}}

.stat::after {{

    content:
        "";

    position:
        absolute;

    width:
        70px;

    height:
        70px;

    right:
        -35px;

    bottom:
        -35px;

    border-radius:
        50%;

    background:
        rgba(124,92,255,.12);

    filter:
        blur(15px);
}}

.stat-label {{

    color:
        var(--muted);

    font-size:
        10px;

    font-weight:
        700;
}}

.stat-value {{

    margin-top:
        9px;

    color:
        var(--text);

    font-size:
        15px;

    line-height:
        1.25;

    font-weight:
        900;

    word-break:
        break-word;
}}

.stat-value.purple {{

    color:
        #b7aaff;
}}


/* ============================================================
   REMAINING
============================================================ */

.remaining {{

    margin-top:
        9px;

    padding:
        16px;

    border-radius:
        21px;

    border:
        1px solid
        var(--border);

    background:
        linear-gradient(
            135deg,
            rgba(124,92,255,.09),
            rgba(0,190,255,.045)
        );
}}

.remaining-top {{

    display:
        flex;

    align-items:
        flex-start;

    justify-content:
        space-between;

    gap:
        10px;
}}

.remaining-label {{

    color:
        var(--muted);

    font-size:
        10px;

    font-weight:
        750;
}}

.remaining-number {{

    margin-top:
        4px;

    font-size:
        24px;

    font-weight:
        950;

    letter-spacing:
        -.7px;
}}

.remaining-number span {{

    color:
        var(--muted);

    font-size:
        12px;

    font-weight:
        700;
}}

.remaining-icon {{

    width:
        42px;

    height:
        42px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        14px;

    background:
        rgba(124,92,255,.13);

    font-size:
        19px;
}}

.progress {{

    height:
        7px;

    margin-top:
        14px;

    border-radius:
        999px;

    overflow:
        hidden;

    background:
        rgba(255,255,255,.07);
}}

.progress-inner {{

    width:
        {progress}%;

    height:
        100%;

    border-radius:
        inherit;

    background:
        linear-gradient(
            90deg,
            #ff25bd,
            #7c5cff,
            #00c8ff
        );

    box-shadow:
        0 0 18px
        rgba(124,92,255,.4);

    transition:
        width
        1s
        ease;
}}


/* ============================================================
   PROFILE
============================================================ */

.profile {{

    margin-top:
        9px;

    padding:
        16px;

    border-radius:
        21px;

    background:
        var(--surface-2);

    border:
        1px solid
        var(--border);
}}

.profile-head {{

    display:
        flex;

    align-items:
        center;

    gap:
        11px;

    padding-bottom:
        10px;

    margin-bottom:
        3px;

    border-bottom:
        1px solid
        var(--border);
}}

.avatar {{

    width:
        39px;

    height:
        39px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        13px;

    background:
        linear-gradient(
            135deg,
            rgba(255,37,189,.18),
            rgba(124,92,255,.18)
        );

    border:
        1px solid
        rgba(255,255,255,.07);

    font-size:
        18px;
}}

.profile-head strong {{

    display:
        block;

    font-size:
        13px;

    font-weight:
        850;
}}

.profile-head span {{

    display:
        block;

    margin-top:
        2px;

    color:
        var(--muted);

    font-size:
        9px;
}}

.profile-row {{

    min-height:
        36px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        15px;
}}

.profile-label {{

    color:
        var(--muted);

    font-size:
        10px;
}}

.profile-value {{

    max-width:
        60%;

    text-align:
        right;

    color:
        var(--text);

    font-size:
        11px;

    font-weight:
        800;

    word-break:
        break-word;
}}


/* ============================================================
   TELEGRAM ID
============================================================ */

.telegram-id {{

    margin-top:
        9px;

    padding:
        13px 15px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    gap:
        10px;

    border-radius:
        17px;

    background:
        rgba(0,0,0,.13);

    border:
        1px solid
        var(--border);
}}

.telegram-id span {{

    color:
        var(--muted);

    font-size:
        10px;
}}

.telegram-id code {{

    color:
        var(--text);

    font-size:
        11px;

    font-weight:
        850;
}}


/* ============================================================
   SECTION
============================================================ */

.section {{

    margin-top:
        20px;
}}

.section-head {{

    padding:
        0 4px;

    display:
        flex;

    align-items:
        flex-end;

    justify-content:
        space-between;
}}

.section-head strong {{

    font-size:
        16px;

    font-weight:
        900;
}}

.section-head span {{

    color:
        var(--muted);

    font-size:
        9px;

    font-weight:
        700;
}}

.section-description {{

    margin:
        6px 4px 11px;

    color:
        var(--muted);

    font-size:
        10px;

    line-height:
        1.5;
}}


/* ============================================================
   CONNECT BUTTON
============================================================ */

.connect-button {{

    position:
        relative;

    width:
        100%;

    min-height:
        70px;

    margin-top:
        9px;

    padding:
        10px 13px;

    display:
        flex;

    align-items:
        center;

    gap:
        12px;

    border:
        1px solid
        rgba(255,255,255,.1);

    border-radius:
        21px;

    color:
        white;

    text-align:
        left;

    cursor:
        pointer;

    overflow:
        hidden;

    transition:
        transform .14s ease,
        border-color .14s ease;
}}

.connect-button::before {{

    content:
        "";

    position:
        absolute;

    inset:
        0;

    background:
        linear-gradient(
            105deg,
            transparent 10%,
            rgba(255,255,255,.12) 50%,
            transparent 90%
        );

    transform:
        translateX(-120%);

    transition:
        transform .6s ease;
}}

.connect-button:hover::before {{

    transform:
        translateX(120%);
}}

.connect-button:active {{

    transform:
        scale(.975);
}}

.connect-icon {{

    width:
        47px;

    height:
        47px;

    flex-shrink:
        0;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        15px;

    background:
        rgba(255,255,255,.09);

    font-size:
        22px;
}}

.connect-content {{

    flex:
        1;

    min-width:
        0;
}}

.connect-content strong {{

    display:
        block;

    font-size:
        14px;

    font-weight:
        900;
}}

.connect-content small {{

    display:
        block;

    margin-top:
        4px;

    color:
        rgba(255,255,255,.58);

    font-size:
        9px;
}}

.connect-arrow {{

    font-size:
        25px;

    color:
        rgba(255,255,255,.55);
}}

.happ-button {{

    background:
        linear-gradient(
            135deg,
            rgba(255,39,185,.28),
            rgba(124,92,255,.16)
        );

    box-shadow:
        0 12px 35px
        rgba(255,39,185,.08);
}}

.incy-button {{

    background:
        linear-gradient(
            135deg,
            rgba(54,129,255,.25),
            rgba(0,200,255,.11)
        );

    box-shadow:
        0 12px 35px
        rgba(0,150,255,.08);
}}


/* ============================================================
   COPY
============================================================ */

.copy-card {{

    margin-top:
        9px;

    padding:
        14px;

    border-radius:
        21px;

    background:
        var(--surface-2);

    border:
        1px solid
        var(--border);
}}

.copy-head {{

    display:
        flex;

    align-items:
        center;

    justify-content:
        space-between;

    margin-bottom:
        9px;
}}

.copy-head strong {{

    display:
        flex;

    align-items:
        center;

    gap:
        7px;

    font-size:
        11px;

    font-weight:
        850;
}}

.copy-head span {{

    color:
        var(--muted);

    font-size:
        9px;
}}

.link {{

    width:
        100%;

    padding:
        12px;

    border-radius:
        14px;

    background:
        rgba(0,0,0,.18);

    border:
        1px solid
        var(--border);

    color:
        var(--muted);

    font-size:
        9px;

    line-height:
        1.45;

    word-break:
        break-all;

    user-select:
        text;

    -webkit-user-select:
        text;
}}

.copy {{

    width:
        100%;

    min-height:
        48px;

    margin-top:
        8px;

    border:
        1px solid
        var(--border);

    border-radius:
        15px;

    color:
        var(--text);

    background:
        var(--surface-3);

    font-family:
        inherit;

    font-size:
        11px;

    font-weight:
        850;

    cursor:
        pointer;

    transition:
        transform .13s ease,
        background .13s ease;
}}

.copy:active {{

    transform:
        scale(.98);
}}

.copy:hover {{

    background:
        rgba(255,255,255,.09);
}}


/* ============================================================
   REFRESH
============================================================ */

.refresh {{

    width:
        100%;

    min-height:
        46px;

    margin-top:
        8px;

    border:
        1px solid
        var(--border);

    border-radius:
        15px;

    background:
        transparent;

    color:
        var(--muted);

    font-family:
        inherit;

    font-size:
        10px;

    font-weight:
        750;

    cursor:
        pointer;
}}

.refresh:active {{

    transform:
        scale(.98);
}}


/* ============================================================
   HELP
============================================================ */

.help {{

    margin-top:
        9px;

    padding:
        14px;

    border-radius:
        20px;

    background:
        linear-gradient(
            135deg,
            rgba(255,255,255,.04),
            rgba(124,92,255,.05)
        );

    border:
        1px solid
        var(--border);
}}

.help-title {{

    display:
        flex;

    align-items:
        center;

    gap:
        7px;

    font-size:
        11px;

    font-weight:
        850;
}}

.help-text {{

    margin-top:
        6px;

    color:
        var(--muted);

    font-size:
        9px;

    line-height:
        1.55;
}}


/* ============================================================
   TELEGRAM
============================================================ */

.telegram {{

    width:
        100%;

    min-height:
        48px;

    margin-top:
        9px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    gap:
        7px;

    border-radius:
        16px;

    border:
        1px solid
        var(--border);

    color:
        var(--text);

    background:
        var(--surface-2);

    text-decoration:
        none;

    font-size:
        10px;

    font-weight:
        800;
}}

.telegram:active {{

    transform:
        scale(.98);
}}


/* ============================================================
   FOOTER
============================================================ */

.footer {{

    padding:
        17px 0 3px;

    text-align:
        center;

    color:
        var(--muted);

    opacity:
        .65;

    font-size:
        9px;
}}

.footer strong {{

    color:
        var(--text);

    opacity:
        .8;
}}


/* ============================================================
   TOAST
============================================================ */

.toast {{

    position:
        fixed;

    z-index:
        9999;

    left:
        50%;

    bottom:
        max(
            22px,
            env(safe-area-inset-bottom)
        );

    transform:
        translate(-50%, 25px);

    opacity:
        0;

    pointer-events:
        none;

    min-width:
        180px;

    max-width:
        calc(100% - 30px);

    padding:
        12px 16px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    gap:
        7px;

    border-radius:
        15px;

    border:
        1px solid
        rgba(255,255,255,.1);

    background:
        rgba(25,26,35,.95);

    box-shadow:
        0 20px 55px
        rgba(0,0,0,.45);

    backdrop-filter:
        blur(25px);

    -webkit-backdrop-filter:
        blur(25px);

    color:
        white;

    font-size:
        11px;

    font-weight:
        800;

    transition:
        opacity .2s ease,
        transform .2s ease;
}}

.toast.show {{

    opacity:
        1;

    transform:
        translate(-50%,0);
}}


/* ============================================================
   RESPONSIVE
============================================================ */

@media (max-width: 390px) {{

    .app {{

        padding-left:
            10px;

        padding-right:
            10px;
    }}

    .hero {{

        padding:
            24px 14px 21px;

        border-radius:
            28px;
    }}

    .panel {{

        padding:
            11px;

        border-radius:
            27px;
    }}

    .hero h1 {{

        font-size:
            28px;
    }}

    .stats {{

        gap:
            7px;
    }}

    .stat {{

        padding:
            12px;

        min-height:
            90px;
    }}
}}

@media (min-width: 700px) {{

    .app {{

        padding-top:
            30px;
    }}

    .hero {{

        padding-top:
            35px;

        padding-bottom:
            30px;
    }}
}}

@media (prefers-reduced-motion: reduce) {{

    *,
    *::before,
    *::after {{

        animation:
            none !important;

        transition:
            none !important;
    }}
}}

</style>

</head>

<body>


<div class="background">

    <div class="grid-overlay"></div>

    <div class="orb orb-one"></div>

    <div class="orb orb-two"></div>

    <div class="orb orb-three"></div>

</div>


<div class="app">


    <!-- ====================================================
         TOPBAR
    ===================================================== -->

    <div class="topbar">

        <div class="top-brand">

            <div class="mini-logo">
                ☂️
            </div>

            <div>

                <strong>
                    ixxy VPN
                </strong>

                <small>
                    PREMIUM ACCESS
                </small>

            </div>

        </div>


        <button
            class="theme"
            id="themeButton"
            type="button"
            onclick="toggleTheme()"
        >
            🌙
        </button>

    </div>


    <!-- ====================================================
         HERO
    ===================================================== -->

    <section class="hero">

        <div class="hero-logo">
            ☂️
        </div>

        <h1>
            Моя подписка
        </h1>

        <div class="hero-subtitle">
            Персональный доступ к
            ixxy VPN
        </div>

        <div
            class="status-pill {status_class}"
        >

            <span class="status-dot"></span>

            <span>
                {status_text}
            </span>

        </div>

    </section>


    <!-- ====================================================
         MAIN PANEL
    ===================================================== -->

    <section class="panel">


        <div class="panel-header">

            <div class="panel-title">

                <strong>
                    Ваша подписка
                </strong>

                <span>
                    Персональная конфигурация
                </span>

            </div>

            <div class="secure-badge">
                🔐 SECURE
            </div>

        </div>


        <!-- STATS -->

        <div class="stats">


            <div class="stat">

                <div class="stat-label">
                    {tariff_icon}
                    ТАРИФ
                </div>

                <div class="stat-value purple">
                    {safe_tariff}
                </div>

            </div>


            <div class="stat">

                <div class="stat-label">
                    📅 ДЕЙСТВУЕТ ДО
                </div>

                <div class="stat-value">
                    {safe_until}
                </div>

            </div>


        </div>


        <!-- REMAINING -->

        <div class="remaining">

            <div class="remaining-top">

                <div>

                    <div class="remaining-label">
                        ⏳ ОСТАЛОСЬ
                    </div>

                    <div class="remaining-number">

                        {days_left}

                        <span>
                            {days_word(days_left)}
                        </span>

                    </div>

                </div>


                <div class="remaining-icon">
                    ⚡
                </div>

            </div>


            <div class="progress">

                <div
                    class="progress-inner"
                ></div>

            </div>

        </div>


        <!-- PROFILE -->

        <div class="profile">


            <div class="profile-head">

                <div class="avatar">
                    👤
                </div>

                <div>

                    <strong>
                        Профиль
                    </strong>

                    <span>
                        Telegram account
                    </span>

                </div>

            </div>


            <div class="profile-row">

                <span class="profile-label">
                    Имя
                </span>

                <span class="profile-value">
                    {safe_first_name}
                </span>

            </div>


            <div class="profile-row">

                <span class="profile-label">
                    Username
                </span>

                <span class="profile-value">
                    @{safe_username}
                </span>

            </div>


        </div>


        <!-- TELEGRAM ID -->

        <div class="telegram-id">

            <span>
                🆔 Telegram ID
            </span>

            <code>
                {user_id}
            </code>

        </div>


        <!-- CONNECTION -->

        <div class="section">


            <div class="section-head">

                <strong>
                    Подключение
                </strong>

                <span>
                    ONE TAP
                </span>

            </div>


            <div class="section-description">

                Добавьте персональную подписку
                прямо в VPN-клиент.

            </div>


            <!-- HAPP -->

            <button
                type="button"
                class="
                    connect-button
                    happ-button
                "
                onclick="openApp('happ')"
            >

                <div class="connect-icon">
                    🚀
                </div>


                <div class="connect-content">

                    <strong>
                        Добавить в Happ
                    </strong>

                    <small>
                        Защищённый Crypt5-импорт
                    </small>

                </div>


                <div class="connect-arrow">
                    ›
                </div>

            </button>


            <!-- INCY -->

            <button
                type="button"
                class="
                    connect-button
                    incy-button
                "
                onclick="openApp('incy')"
            >

                <div class="connect-icon">
                    ⚡
                </div>


                <div class="connect-content">

                    <strong>
                        Добавить в INCY
                    </strong>

                    <small>
                        Быстрое подключение
                        к персональной подписке
                    </small>

                </div>


                <div class="connect-arrow">
                    ›
                </div>

            </button>


        </div>


        <!-- HAPP LINK -->

        <div class="copy-card">


            <div class="copy-head">

                <strong>
                    🔐
                    Happ Crypt5
                </strong>

                <span>
                    PRIVATE
                </span>

            </div>


            <div
                class="link"
                onclick="copyLink()"
            >
                {safe_subscription_url}
            </div>


            <button
                type="button"
                class="copy"
                onclick="copyLink()"
            >
                📋 Скопировать Crypt5-ссылку
            </button>


        </div>


        <!-- REFRESH -->

        <button
            type="button"
            class="refresh"
            onclick="refreshPage()"
        >
            🔄 Обновить данные подписки
        </button>


        <!-- HELP -->

        <div class="help">

            <div class="help-title">
                💡 Как подключиться
            </div>


            <div class="help-text">

                1. Нажмите «Добавить в Happ».<br>

                2. Happ получит зашифрованную
                Crypt5-ссылку.<br>

                3. Подтвердите добавление
                подписки в приложении.<br>

                4. Включите VPN.

            </div>

        </div>


        <!-- TELEGRAM -->

        <a
            class="telegram"
            href="{js_telegram_url}"
        >
            ← Вернуться в Telegram
        </a>


    </section>


    <!-- FOOTER -->

    <div class="footer">

        ☂️

        <strong>
            ixxy VPN
        </strong>

        &nbsp;•&nbsp;

        Premium VPN

    </div>


</div>


<!-- TOAST -->

<div
    class="toast"
    id="toast"
>

    <span>
        ✓
    </span>

    <span id="toastText">
        Готово
    </span>

</div>


<script>

/* ============================================================
   VARIABLES
============================================================ */

const subscriptionLink =
    '{js_subscription_url}';


const happUrl =
    '{js_happ_url}';


const incyUrl =
    '{js_incy_url}';


const pageUrl =
    '{js_page_url}';


/* ============================================================
   TOAST
============================================================ */

let toastTimer = null;


function showToast(message) {{

    const toast =
        document.getElementById(
            "toast"
        );


    const text =
        document.getElementById(
            "toastText"
        );


    if (
        !toast ||
        !text
    ) {{

        return;

    }}


    text.textContent =
        message;


    toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(() => {{

            toast.classList.remove(
                "show"
            );

        }}, 2200);

}}


/* ============================================================
   THEME
============================================================ */

function applyTheme(theme) {{

    const button =
        document.getElementById(
            "themeButton"
        );


    if (
        theme === "light"
    ) {{

        document.body.classList.add(
            "light"
        );


        if (button) {{

            button.textContent =
                "☀️";

        }}

    }} else {{

        document.body.classList.remove(
            "light"
        );


        if (button) {{

            button.textContent =
                "🌙";

        }}

    }}

}}


function toggleTheme() {{

    const current =
        localStorage.getItem(
            "ixxy_theme"
        ) || "dark";


    const next =
        current === "dark"
            ? "light"
            : "dark";


    localStorage.setItem(
        "ixxy_theme",
        next
    );


    applyTheme(
        next
    );

}}


applyTheme(

    localStorage.getItem(
        "ixxy_theme"
    ) || "dark"

);


/* ============================================================
   OPEN APP
============================================================ */

function openApp(name) {{

    let url;

    let title;


    if (
        name === "happ"
    ) {{

        url =
            happUrl;

        title =
            "Happ";

    }} else {{

        url =
            incyUrl;

        title =
            "INCY";

    }}


    if (!url) {{

        showToast(
            "❌ Ссылка недоступна"
        );

        return;

    }}


    showToast(

        "📲 Открываем "
        + title
        + "..."

    );


    const started =
        Date.now();


    try {{

        window.location.href =
            url;

    }} catch (error) {{

        console.log(
            error
        );

    }}


    setTimeout(() => {{

        if (
            !document.hidden &&
            Date.now() - started < 3000
        ) {{

            showToast(

                "⚠️ Приложение не открылось. Скопируйте ссылку."

            );

        }}

    }}, 1800);

}}


/* ============================================================
   COPY
============================================================ */

async function copyLink() {{

    if (!subscriptionLink) {{

        showToast(
            "❌ Ссылка недоступна"
        );

        return;

    }}


    try {{

        await navigator.clipboard.writeText(
            subscriptionLink
        );


        showToast(
            "✓ Crypt5-ссылка скопирована"
        );


        return;

    }} catch (error) {{

        console.log(
            error
        );

    }}


    fallbackCopy(
        subscriptionLink
    );

}}


/* ============================================================
   FALLBACK COPY
============================================================ */

function fallbackCopy(text) {{

    try {{

        const textarea =
            document.createElement(
                "textarea"
            );


        textarea.value =
            text;


        textarea.style.position =
            "fixed";


        textarea.style.left =
            "-9999px";


        textarea.style.top =
            "0";


        textarea.style.opacity =
            "0";


        document.body.appendChild(
            textarea
        );


        textarea.focus();


        textarea.select();


        const result =
            document.execCommand(
                "copy"
            );


        textarea.remove();


        if (result) {{

            showToast(
                "✓ Crypt5-ссылка скопирована"
            );

        }} else {{

            throw new Error(
                "copy failed"
            );

        }}

    }} catch (error) {{

        prompt(
            "Скопируйте ссылку:",
            text
        );

    }}

}}


/* ============================================================
   REFRESH
============================================================ */

function refreshPage() {{

    showToast(
        "🔄 Обновляем подписку..."
    );


    setTimeout(() => {{

        window.location.href =
            pageUrl
            + "?refresh="
            + Date.now();

    }}, 250);

}}


/* ============================================================
   KEYBOARD
============================================================ */

document.addEventListener(

    "keydown",

    function(event) {{

        if (
            event.key === "Escape"
        ) {{

            const toast =
                document.getElementById(
                    "toast"
                );


            if (toast) {{

                toast.classList.remove(
                    "show"
                );

            }}

        }}

    }

);

</script>

</body>

</html>
"""


    # ========================================================
    # RESPONSE
    # ========================================================

    return Response(

        page,

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
# RAW SUBSCRIPTION
# ============================================================

@app.route(
    "/sub/<token>"
)
def subscription_content(token):

    user_id = get_user_id_from_token(
        token
    )


    if user_id is None:

        abort(404)


    try:

        content = (
            get_subscription_content(
                user_id
            )
        )

    except Exception:

        content = ""


    if not content:

        return Response(

            "#profile-title: ⛔ ixxy VPN\n"
            "#announce: Подписка не найдена",

            status=404,

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

            "Access-Control-Allow-Origin":
                "*",

        },

    )


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
    content="
        width=device-width,
        initial-scale=1
    "
>

<meta
    name="theme-color"
    content="#07070b"
>

<title>
    ☂️ ixxy VPN
</title>

<style>

* {{
    box-sizing:
        border-box;
}}

html,
body {{
    margin:
        0;

    min-height:
        100%;
}}

body {{

    min-height:
        100vh;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    padding:
        20px;

    color:
        white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;

    background:
        radial-gradient(
            circle at 10% 0%,
            rgba(255,30,190,.25),
            transparent 35%
        ),
        radial-gradient(
            circle at 90% 0%,
            rgba(0,190,255,.2),
            transparent 35%
        ),
        #07070b;
}}

.card {{

    width:
        100%;

    max-width:
        450px;

    padding:
        42px 25px;

    text-align:
        center;

    border-radius:
        32px;

    background:
        rgba(17,18,27,.85);

    border:
        1px solid
        rgba(255,255,255,.09);

    box-shadow:
        0 30px 100px
        rgba(0,0,0,.5);

    backdrop-filter:
        blur(30px);

    -webkit-backdrop-filter:
        blur(30px);
}}

.logo {{

    width:
        90px;

    height:
        90px;

    margin:
        0 auto 22px;

    display:
        flex;

    align-items:
        center;

    justify-content:
        center;

    border-radius:
        28px;

    font-size:
        46px;

    background:
        linear-gradient(
            135deg,
            #ff25bd,
            #743cff,
            #00c9ff
        );

    box-shadow:
        0 20px 65px
        rgba(120,60,255,.4);
}}

h1 {{

    margin:
        0;

    font-size:
        32px;

    font-weight:
        900;
}}

p {{

    margin-top:
        10px;

    color:
        #9295a4;

    font-size:
        14px;

    line-height:
        1.55;
}}

</style>

</head>

<body>

<div class="card">

    <div class="logo">
        ☂️
    </div>

    <h1>
        ixxy VPN
    </h1>

    <p>
        Персональный сервер подписок
        работает.
    </p>

</div>

</body>

</html>
"""


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return Response(

        "OK",

        status=200,

        mimetype="text/plain",

        headers={

            "Cache-Control":
                "no-cache, no-store, must-revalidate",

        },

    )


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


    app.run(

        host="0.0.0.0",

        port=port,

    )