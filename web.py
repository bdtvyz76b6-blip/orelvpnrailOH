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
# IXXY VPN
# ============================================================

APP_VERSION = "ixxy-2026.09.01"

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy"
).strip()

TELEGRAM_URL = "https://t.me/orelvpntopbot"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# HPWNR / HAPP CRYPT5
# ============================================================

HPWNR_PATH = os.getenv(
    "HPWNR_PATH",
    "bin/hpwnr"
)


def find_hpwnr():
    candidates = [
        HPWNR_PATH,
        "./bin/hpwnr",
        "bin/hpwnr",
        "./hpwnr",
        "hpwnr",

        "/opt/render/project/src/bin/hpwnr",
        "/opt/render/project/src/hpwnr",

        "/usr/local/bin/hpwnr",
        "/usr/bin/hpwnr",

        "/opt/hpwnr",
        "/opt/bin/hpwnr",
    ]

    for candidate in candidates:

        if not candidate:
            continue

        try:
            if (
                os.path.isfile(candidate)
                and os.access(candidate, os.X_OK)
            ):
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
        print("[HAPP] hpwnr НЕ НАЙДЕН")
        return ""

    try:

        print("[HAPP] Используется:", hpwnr)
        print("[HAPP] Генерация Crypt5...")

        result = subprocess.run(
            [hpwnr, subscription_url],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

        stdout = (
            result.stdout or ""
        ).strip()

        stderr = (
            result.stderr or ""
        ).strip()

        print(
            "[HAPP] returncode:",
            result.returncode
        )

        if stdout:
            print(
                "[HAPP] stdout:",
                stdout[:500]
            )

        if stderr:
            print(
                "[HAPP] stderr:",
                stderr[:500]
            )

        if result.returncode != 0:
            return ""

        for line in stdout.splitlines():

            line = line.strip()

            if line.startswith(
                "happ://crypt5/"
            ):
                print(
                    "[HAPP] Crypt5 успешно создан"
                )

                return line

        pos = stdout.find(
            "happ://crypt5/"
        )

        if pos >= 0:

            value = (
                stdout[pos:]
                .split()[0]
                .strip()
            )

            if value.startswith(
                "happ://crypt5/"
            ):
                return value

        print(
            "[HAPP] Crypt5 не найден"
        )

        return ""

    except subprocess.TimeoutExpired:

        print(
            "[HAPP] hpwnr timeout"
        )

        return ""

    except Exception as e:

        print(
            "[HAPP] ошибка:",
            repr(e)
        )

        return ""


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
# URLS
# ============================================================

def get_urls(user_id):

    token = get_token(user_id)

    page_url = (
        f"{PUBLIC_SITE_URL}"
        f"/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}"
        f"/sub/{token}"
    )

    happ_url = generate_happ_crypt5(
        subscription_url
    )

    if not happ_url:

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
# DATE
# ============================================================

def parse_subscription_date(value):

    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",

        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt
            )

        except Exception:
            pass

    try:

        return datetime.fromisoformat(
            value.replace("Z", "")
        )

    except Exception:
        return None


def get_subscription_status(user):

    if not user:
        return (
            "Неактивна",
            "expired"
        )

    until = None

    if isinstance(user, dict):

        until = user.get(
            "subscription_until"
        )

    if not until:

        return (
            "Неактивна",
            "expired"
        )

    date = parse_subscription_date(
        until
    )

    if not date:

        return (
            "Активна",
            "active"
        )

    if date > datetime.now():

        return (
            "Активна",
            "active"
        )

    return (
        "Истекла",
        "expired"
    )


# ============================================================
# USER
# ============================================================

def load_user_data(user_id):

    user = get_user(user_id)

    content = ""

    try:

        content = (
            get_subscription_content(
                user_id
            )
            or ""
        )

    except Exception as e:

        print(
            "[SUB] Ошибка:",
            repr(e)
        )

    return (
        user,
        content
    )


def esc(value):

    return html.escape(
        str(value or "")
    )


# ============================================================
# MAIN HTML
# ============================================================

def render_subscription_page(
    user_id,
    user,
    page_url,
    subscription_url,
    happ_url,
    incy_url
):

    status_text, status_class = (
        get_subscription_status(user)
    )

    tariff = "IXXY VPN"

    expires = "Без ограничений"

    if isinstance(user, dict):

        tariff = (
            user.get("subscription")
            or user.get("tariff")
            or "IXXY VPN"
        )

        expires = (
            user.get(
                "subscription_until"
            )
            or "Без ограничений"
        )

    is_active = (
        status_class == "active"
    )

    status_dot = (
        "active"
        if is_active
        else "inactive"
    )

    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    return f"""
<!DOCTYPE html>

<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width,
             initial-scale=1,
             maximum-scale=1,
             viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#08090d"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
>

<title>
IXXY VPN
</title>

<style>

/* =========================================================
   RESET
   ========================================================= */

* {{
    box-sizing: border-box;
    -webkit-tap-highlight-color:
        transparent;
}}

html {{
    background: #08090d;
}}

body {{
    margin: 0;
    min-height: 100vh;

    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(126, 82, 255, .16),
            transparent 35%
        ),
        #08090d;

    color: #f6f6f8;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        "Segoe UI",
        sans-serif;

    letter-spacing: -0.15px;
}}

button,
a {{
    font-family: inherit;
}}

a {{
    text-decoration: none;
    color: inherit;
}}


/* =========================================================
   PAGE
   ========================================================= */

.page {{
    width: 100%;
    max-width: 720px;

    min-height: 100vh;

    margin: 0 auto;

    padding:
        calc(18px + env(safe-area-inset-top))
        16px
        calc(24px + env(safe-area-inset-bottom));
}}


/* =========================================================
   TOP
   ========================================================= */

.top {{
    display: flex;
    align-items: center;
    justify-content: space-between;

    margin-bottom: 18px;
}}

.logo {{
    display: flex;
    align-items: center;
    gap: 10px;
}}

.logo-icon {{
    width: 40px;
    height: 40px;

    border-radius: 12px;

    display: flex;
    align-items: center;
    justify-content: center;

    background:
        linear-gradient(
            145deg,
            #8f5cff,
            #6635e9
        );

    box-shadow:
        0 8px 30px
        rgba(118, 69, 255, .25);

    font-size: 15px;
    font-weight: 950;
}}

.logo-name {{
    font-size: 17px;
    font-weight: 850;
}}

.logo-sub {{
    margin-top: 1px;

    color: #737581;

    font-size: 11px;
}}


/* =========================================================
   STATUS
   ========================================================= */

.status {{
    display: flex;
    align-items: center;
    gap: 7px;

    padding:
        8px 11px;

    border-radius: 999px;

    background: rgba(
        255,
        255,
        255,
        .035
    );

    border: 1px solid rgba(
        255,
        255,
        255,
        .065
    );

    color: #aeb0ba;

    font-size: 11px;
    font-weight: 750;
}}

.status-dot {{
    width: 7px;
    height: 7px;

    border-radius: 50%;
}}

.status-dot.active {{
    background: #55df91;

    box-shadow:
        0 0 10px
        rgba(85, 223, 145, .65);
}}

.status-dot.inactive {{
    background: #ef5d68;
}}


/* =========================================================
   MAIN CARD
   ========================================================= */

.main-card {{
    position: relative;

    overflow: hidden;

    border-radius: 27px;

    background:
        linear-gradient(
            145deg,
            rgba(27, 28, 37, .98),
            rgba(15, 16, 22, .98)
        );

    border:
        1px solid rgba(
            255,
            255,
            255,
            .075
        );

    box-shadow:
        0 25px 80px
        rgba(0, 0, 0, .38);
}}

.main-card::before {{
    content: "";

    position: absolute;

    width: 240px;
    height: 240px;

    top: -150px;
    right: -90px;

    border-radius: 50%;

    background: #7950ff;

    filter: blur(90px);

    opacity: .14;

    pointer-events: none;
}}

.content {{
    position: relative;

    padding: 24px;
}}


/* =========================================================
   TITLE
   ========================================================= */

.small-title {{
    color: #7d7f8c;

    font-size: 11px;

    font-weight: 750;

    text-transform: uppercase;

    letter-spacing: 1.2px;
}}

h1 {{
    margin:
        7px 0 0;

    font-size: 31px;

    line-height: 1.05;

    font-weight: 900;

    letter-spacing: -1.3px;
}}

.subtitle {{
    margin-top: 9px;

    color: #858793;

    font-size: 13px;

    line-height: 1.55;
}}


/* =========================================================
   INFO
   ========================================================= */

.info {{
    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 10px;

    margin-top: 21px;
}}

.info-item {{
    min-width: 0;

    padding: 15px;

    border-radius: 17px;

    background:
        rgba(
            255,
            255,
            255,
            .035
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .055
        );
}}

.info-label {{
    color: #70727d;

    font-size: 10px;

    margin-bottom: 6px;
}}

.info-value {{
    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

    font-size: 14px;

    font-weight: 850;
}}


/* =========================================================
   BIG CONNECT
   ========================================================= */

.connect {{
    display: flex;

    align-items: center;

    justify-content: center;

    width: 100%;

    min-height: 58px;

    margin-top: 16px;

    border-radius: 17px;

    background:
        linear-gradient(
            135deg,
            #925fff,
            #6634e9
        );

    box-shadow:
        0 15px 40px
        rgba(
            106,
            54,
            239,
            .22
        );

    font-size: 15px;

    font-weight: 900;

    transition:
        transform .15s ease,
        filter .15s ease;
}}

.connect:active {{
    transform: scale(.985);

    filter: brightness(.9);
}}


/* =========================================================
   SECONDARY BUTTONS
   ========================================================= */

.buttons {{
    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 10px;

    margin-top: 10px;
}}

.secondary {{
    display: flex;

    align-items: center;

    justify-content: center;

    min-height: 52px;

    border-radius: 16px;

    background:
        rgba(
            255,
            255,
            255,
            .035
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .065
        );

    color: #d8d9df;

    font-size: 13px;

    font-weight: 800;
}}

.secondary:active {{
    background:
        rgba(
            255,
            255,
            255,
            .06
        );
}}


/* =========================================================
   SUBSCRIPTION
   ========================================================= */

.subscription {{
    margin-top: 13px;

    padding: 17px;

    border-radius: 18px;

    background:
        #0c0d12;

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .055
        );
}}

.subscription-title {{
    margin-bottom: 9px;

    color: #858792;

    font-size: 11px;

    font-weight: 750;
}}

.url-row {{
    display: flex;

    align-items: center;

    gap: 8px;
}}

.url {{
    min-width: 0;

    flex: 1;

    overflow: hidden;

    text-overflow: ellipsis;

    white-space: nowrap;

    color: #b6b8c2;

    font-family:
        ui-monospace,
        SFMono-Regular,
        Menlo,
        monospace;

    font-size: 10px;
}}

.copy {{
    flex-shrink: 0;

    border: 0;

    padding:
        9px 11px;

    border-radius: 11px;

    background:
        rgba(
            142,
            91,
            255,
            .16
        );

    color: #ae8aff;

    font-size: 11px;

    font-weight: 850;

    cursor: pointer;
}}


/* =========================================================
   INSTRUCTIONS
   ========================================================= */

.instructions {{
    margin-top: 13px;

    padding: 18px;

    border-radius: 18px;

    background:
        rgba(
            255,
            255,
            255,
            .025
        );

    border:
        1px solid
        rgba(
            255,
            255,
            255,
            .05
        );
}}

.instruction-title {{
    font-size: 13px;

    font-weight: 850;

    margin-bottom: 13px;
}}

.step {{
    display: flex;

    align-items: flex-start;

    gap: 10px;

    margin-top: 11px;
}}

.step-number {{
    width: 24px;
    height: 24px;

    flex-shrink: 0;

    display: flex;

    align-items: center;

    justify-content: center;

    border-radius: 8px;

    background:
        rgba(
            140,
            91,
            255,
            .12
        );

    color: #a987ff;

    font-size: 10px;

    font-weight: 900;
}}

.step-text {{
    padding-top: 3px;

    color: #888a95;

    font-size: 11px;

    line-height: 1.45;
}}


/* =========================================================
   FOOTER
   ========================================================= */

.footer {{
    text-align: center;

    padding:
        18px 0 4px;

    color: #4e505a;

    font-size: 10px;
}}

.footer strong {{
    color: #666875;
}}


/* =========================================================
   MOBILE
   ========================================================= */

@media (max-width: 430px) {{

    .page {{
        padding-left: 11px;
        padding-right: 11px;
    }}

    .content {{
        padding: 20px;
    }}

    h1 {{
        font-size: 29px;
    }}

    .info {{
        gap: 8px;
    }}

    .info-item {{
        padding: 13px;
    }}

}}

</style>

</head>


<body>

<div class="page">


    <!-- TOP -->

    <div class="top">

        <div class="logo">

            <div class="logo-icon">
                IX
            </div>

            <div>

                <div class="logo-name">
                    IXXY VPN
                </div>

                <div class="logo-sub">
                    Private connection
                </div>

            </div>

        </div>


        <div class="status">

            <span
                class="status-dot {status_dot}"
            ></span>

            {esc(status_text)}

        </div>

    </div>


    <!-- MAIN -->

    <div class="main-card">

        <div class="content">


            <div class="small-title">
                Подписка
            </div>


            <h1>
                Добро пожаловать<br>
                в IXXY VPN
            </h1>


            <div class="subtitle">
                Ваша персональная подписка
                готова к подключению.
            </div>


            <!-- INFO -->

            <div class="info">


                <div class="info-item">

                    <div class="info-label">
                        Тариф
                    </div>

                    <div class="info-value">
                        {esc(tariff)}
                    </div>

                </div>


                <div class="info-item">

                    <div class="info-label">
                        Действует до
                    </div>

                    <div class="info-value">
                        {esc(expires)}
                    </div>

                </div>


            </div>


            <!-- HAPP -->

            <a
                class="connect"
                href="{esc(happ_url)}"
            >
                Подключить в Happ
            </a>


            <!-- OTHER CLIENTS -->

            <div class="buttons">

                <a
                    class="secondary"
                    href="{esc(incy_url)}"
                >
                    Добавить в INCY
                </a>


                <a
                    class="secondary"
                    href="{TELEGRAM_URL}"
                >
                    Telegram
                </a>

            </div>


            <!-- SUBSCRIPTION URL -->

            <div class="subscription">

                <div class="subscription-title">
                    Ссылка подписки
                </div>


                <div class="url-row">

                    <div
                        class="url"
                        id="subscription-url"
                    >
                        {esc(subscription_url)}
                    </div>


                    <button
                        class="copy"
                        onclick="copySubscription()"
                    >
                        Копировать
                    </button>

                </div>

            </div>


            <!-- INSTRUCTIONS -->

            <div class="instructions">

                <div class="instruction-title">
                    Как подключиться
                </div>


                <div class="step">

                    <div class="step-number">
                        1
                    </div>

                    <div class="step-text">
                        Нажмите «Подключить в Happ».
                    </div>

                </div>


                <div class="step">

                    <div class="step-number">
                        2
                    </div>

                    <div class="step-text">
                        Happ автоматически добавит
                        вашу подписку.
                    </div>

                </div>


                <div class="step">

                    <div class="step-number">
                        3
                    </div>

                    <div class="step-text">
                        Включите подключение
                        и пользуйтесь IXXY VPN.
                    </div>

                </div>

            </div>


        </div>

    </div>


    <div class="footer">

        IXXY VPN
        <br>

        <strong>
            {APP_VERSION}
        </strong>

    </div>


</div>


<script>

function copySubscription() {{

    const value =
        document
        .getElementById(
            "subscription-url"
        )
        .innerText
        .trim();

    const button =
        document.querySelector(
            ".copy"
        );

    if (
        navigator.clipboard &&
        navigator.clipboard.writeText
    ) {{

        navigator.clipboard
            .writeText(value)
            .then(() => {{

                button.innerText =
                    "Скопировано ✓";

                setTimeout(() => {{

                    button.innerText =
                        "Копировать";

                }}, 1600);

            }})
            .catch(() => {{

                fallbackCopy(
                    value,
                    button
                );

            }});

    }} else {{

        fallbackCopy(
            value,
            button
        );

    }}

}}


function fallbackCopy(
    value,
    button
) {{

    const textarea =
        document.createElement(
            "textarea"
        );

    textarea.value = value;

    textarea.style.position =
        "fixed";

    textarea.style.opacity = "0";

    document.body.appendChild(
        textarea
    );

    textarea.select();

    try {{

        document.execCommand(
            "copy"
        );

        button.innerText =
            "Скопировано ✓";

    }} catch (e) {{

        alert(
            "Скопируй ссылку вручную"
        );

    }}

    document.body.removeChild(
        textarea
    );

    setTimeout(() => {{

        button.innerText =
            "Копировать";

    }}, 1600);

}}

</script>

</body>

</html>
"""


# ============================================================
# /s/<token>
# ============================================================

@app.route("/s/<token>")
def subscription_page(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    user, content = (
        load_user_data(user_id)
    )

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    page = render_subscription_page(
        user_id=user_id,
        user=user,
        page_url=page_url,
        subscription_url=subscription_url,
        happ_url=happ_url,
        incy_url=incy_url,
    )

    response = make_response(page)

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers[
        "X-Ixxy-Version"
    ] = APP_VERSION

    return response


# ============================================================
# /sub/<token>
# ============================================================

@app.route("/sub/<token>")
def subscription_raw(token):

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
            or ""
        )

    except Exception as e:

        print(
            "[SUB] Ошибка:",
            repr(e)
        )

        content = ""

    response = Response(
        content,
        mimetype="text/plain; charset=utf-8"
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers[
        "X-Ixxy-Version"
    ] = APP_VERSION

    return response


# ============================================================
# /happ-test/<token>
# ============================================================

@app.route("/happ-test/<token>")
def happ_test(token):

    user_id = get_user_id_from_token(
        token
    )

    if user_id is None:
        abort(404)

    (
        page_url,
        subscription_url,
        happ_url,
        incy_url,
    ) = get_urls(user_id)

    text = f"""IXXY VPN

PAGE:
{page_url}

SUBSCRIPTION:
{subscription_url}

HAPP:
{happ_url}

INCY:
{incy_url}

VERSION:
{APP_VERSION}
"""

    response = Response(
        text,
        mimetype="text/plain; charset=utf-8"
    )

    for key, value in NO_CACHE_HEADERS.items():
        response.headers[key] = value

    response.headers[
        "X-Ixxy-Version"
    ] = APP_VERSION

    return response


# ============================================================
# /health
# ============================================================

@app.route("/health")
def health():

    hpwnr = find_hpwnr()

    return {
        "service": "IXXY VPN",
        "status": "ok",
        "version": APP_VERSION,
        "hpwnr": bool(hpwnr),
        "hpwnr_path": hpwnr or "",
    }


# ============================================================
# /
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
             initial-scale=1"
>

<title>IXXY VPN</title>

<style>

body {
    margin: 0;
    min-height: 100vh;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #08090d;
    color: white;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

.box {
    text-align: center;
}

.logo {
    font-size: 56px;
    font-weight: 950;
    letter-spacing: -4px;
}

.text {
    margin-top: 8px;
    color: #666874;
    font-size: 13px;
}

</style>

</head>

<body>

<div class="box">

    <div class="logo">
        IXXY
    </div>

    <div class="text">
        Private VPN
    </div>

</div>

</body>

</html>
"""


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def not_found(error):

    return Response(
        "IXXY VPN: page not found",
        status=404,
        mimetype="text/plain"
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

    print(
        "[IXXY] Starting on port",
        port
    )

    print(
        "[IXXY] Version:",
        APP_VERSION
    )

    print(
        "[IXXY] HPWNR:",
        find_hpwnr()
    )

    app.run(
        host="0.0.0.0",
        port=port
    )