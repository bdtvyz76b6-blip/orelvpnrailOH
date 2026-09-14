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

from github_update import update_subscription_file


app = Flask(__name__)


# ============================================================
# CONFIG
# ============================================================

APP_VERSION = "ixxy-2026.09.14"

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://ixxyweb.onrender.com",
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
)

TELEGRAM_URL = os.getenv(
    "TELEGRAM_URL",
    "https://t.me/orelvpntopbot",
).strip()

HPWNR_PATH = os.getenv(
    "HPWNR_PATH",
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "bin",
        "hpwnr",
    ),
)


# ============================================================
# CACHE
# ============================================================

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


# ============================================================
# TOKEN
# ============================================================

def parse_token(token):
    if not token:
        return None

    if not token.startswith(
        SUBSCRIPTION_PREFIX
    ):
        return None

    raw = token[
        len(SUBSCRIPTION_PREFIX):
    ]

    if not raw.isdigit():
        return None

    try:
        return int(raw)
    except Exception:
        return None


# ============================================================
# SUBSCRIPTION URL
# ============================================================

def build_subscription_url(token):
    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{quote(token, safe='')}"
    )


# ============================================================
# HPWNR / HAPP
# ============================================================

def find_hpwnr():
    candidates = [
        HPWNR_PATH,

        os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "bin",
            "hpwnr",
        ),

        os.path.join(
            os.getcwd(),
            "bin",
            "hpwnr",
        ),

        shutil.which("hpwnr"),
    ]

    for path in candidates:
        if not path:
            continue

        try:
            if (
                os.path.isfile(path)
                and os.access(path, os.X_OK)
            ):
                return path
        except Exception:
            pass

    return None


def encrypt_happ_crypt4(subscription_url):
    binary = find_hpwnr()

    if not binary:
        raise RuntimeError(
            "hpwnr binary not found"
        )

    result = subprocess.run(
        [
            binary,
            subscription_url,
            "crypt4",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )

    if result.returncode != 0:
        raise RuntimeError(
            (
                result.stderr
                or result.stdout
                or "hpwnr encryption failed"
            ).strip()
        )

    encrypted = (
        result.stdout or ""
    ).strip()

    if not encrypted.startswith(
        "happ://crypt4/"
    ):
        raise RuntimeError(
            "hpwnr returned invalid crypt4 link"
        )

    return encrypted


def build_happ_url(token):
    encrypted = encrypt_happ_crypt4(
        build_subscription_url(token)
    )

    return (
        "https://happ.vpnbypass.click/?RAW="
        + quote(
            encrypted,
            safe=":/+=",
        )
    )


# ============================================================
# INCY
# ============================================================

def build_incy_url(token):
    return (
        "incy://add/"
        + quote(
            build_subscription_url(token),
            safe="",
        )
    )


# ============================================================
# TEXT HELPERS
# ============================================================

def safe_text(
    value,
    default="—",
):
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
        if isinstance(
            value,
            datetime,
        ):
            dt = value
        else:
            dt = datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00",
                )
            )

        return dt.strftime(
            "%d.%m.%Y"
        )

    except Exception:
        return safe_text(value)


def get_days_left(value):
    if not value:
        return 0

    try:
        if isinstance(
            value,
            datetime,
        ):
            dt = value
        else:
            dt = datetime.fromisoformat(
                str(value).replace(
                    "Z",
                    "+00:00",
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
            int(seconds / 86400),
        )

    except Exception:
        return 0


# ============================================================
# SUBSCRIPTION STATUS
# ============================================================

def is_subscription_active(
    subscription,
    subscription_until,
):
    """
    Подписка активна только если:

    1. subscription = True
    2. subscription_until ещё не истёк
    """

    if subscription is not True:
        return False

    if not subscription_until:
        return False

    try:
        if isinstance(
            subscription_until,
            datetime,
        ):
            dt = subscription_until

        else:
            dt = datetime.fromisoformat(
                str(
                    subscription_until
                ).replace(
                    "Z",
                    "+00:00",
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
# CABINET PAGE
# ============================================================

def render_page(
    token,
    first_name,
    subscription,
    subscription_until,
):
    active = is_subscription_active(
        subscription,
        subscription_until,
    )

    days = get_days_left(
        subscription_until
    )

    name = safe_text(
        first_name,
        "Пользователь",
    )

    tariff = safe_text(
        subscription,
        "ixxy",
    )

    expiry = format_date(
        subscription_until
    )

    subscription_url = (
        build_subscription_url(token)
    )

    # --------------------------------------------------------
    # HAPP
    # --------------------------------------------------------

    try:
        happ_url = build_happ_url(
            token
        )
        happ_error = False

    except Exception:
        happ_url = "#"
        happ_error = True

    # --------------------------------------------------------
    # INCY
    # --------------------------------------------------------

    incy_url = build_incy_url(
        token
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = (
        "Активна"
        if active
        else "Неактивна"
    )

    status_class = (
        "online"
        if active
        else "offline"
    )

    days_text = (
        f"{days} дн."
        if active
        else "Завершена"
    )

    error_html = (
        ""
        if not happ_error
        else (
            '<div class="error">'
            "Happ crypt4 сейчас недоступен. "
            "Проверьте установку hpwnr на Render."
            "</div>"
        )
    )

    # ========================================================
    # HTML
    # ========================================================

    return f'''<!doctype html>
<html lang="ru">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1,maximum-scale=1,viewport-fit=cover"
>

<meta
    name="theme-color"
    content="#050505"
>

<meta
    name="apple-mobile-web-app-capable"
    content="yes"
>

<meta
    name="apple-mobile-web-app-status-bar-style"
    content="black-translucent"
>

<title>ixxy VPN — Личный кабинет</title>

<style>

:root{{
    --bg:#050505;
    --card:rgba(18,18,20,.76);
    --line:rgba(255,255,255,.09);
    --muted:#8e8e95;
    --text:#f5f5f7;
}}

*{{
    box-sizing:border-box;
    -webkit-tap-highlight-color:transparent;
}}

html,
body{{
    margin:0;
    min-height:100%;
    background:var(--bg);
    color:var(--text);
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Inter,
        Arial,
        sans-serif;
}}

body{{
    min-height:100vh;

    background:
        radial-gradient(
            circle at 50% -10%,
            rgba(255,255,255,.13),
            transparent 34%
        ),

        radial-gradient(
            circle at 100% 45%,
            rgba(255,255,255,.04),
            transparent 30%
        ),

        linear-gradient(
            180deg,
            #090909,
            #050505 58%,
            #020202
        );
}}

.container{{
    width:min(100% - 32px,620px);
    margin:auto;

    padding:
        calc(20px + env(safe-area-inset-top))
        0
        calc(30px + env(safe-area-inset-bottom));
}}

.header{{
    display:flex;
    align-items:center;
    justify-content:space-between;
    margin-bottom:22px;
}}

.brandWrap{{
    display:flex;
    align-items:center;
    gap:11px;
}}

.logo{{
    width:43px;
    height:43px;
    border-radius:14px;

    display:grid;
    place-items:center;

    border:1px solid var(--line);

    background:
        linear-gradient(
            145deg,
            #252527,
            #0d0d0e
        );

    box-shadow:
        0 14px 35px rgba(0,0,0,.35);
}}

.logo span{{
    font-size:18px;
    font-weight:900;
    letter-spacing:-1px;
}}

.brand{{
    font-size:20px;
    font-weight:850;
    letter-spacing:-.7px;
}}

.secure{{
    font-size:10px;
    color:#777;
    letter-spacing:1.2px;
}}

.hero{{
    text-align:center;
    padding:22px 0 25px;
}}

.eyebrow{{
    font-size:13px;
    color:#85858b;
    margin-bottom:8px;
}}

.hero h1{{
    font-size:42px;
    line-height:1.03;
    letter-spacing:-2.4px;
    margin:0 0 11px;
    font-weight:900;
}}

.hero p{{
    margin:0;
    color:#85858b;
    font-size:15px;
    line-height:1.5;
}}

.card{{
    margin-top:13px;
    padding:20px;

    border:1px solid var(--line);
    border-radius:25px;

    background:var(--card);

    backdrop-filter:blur(25px);

    box-shadow:
        0 18px 55px rgba(0,0,0,.22);
}}

.statusTop{{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:17px;
}}

.label{{
    font-size:11px;
    color:#777;
    text-transform:uppercase;
    letter-spacing:1px;
    font-weight:800;
}}

.badge{{
    display:flex;
    align-items:center;
    gap:7px;

    padding:8px 11px;

    border-radius:999px;

    background:rgba(255,255,255,.055);

    font-size:12px;
    font-weight:750;
}}

.dot{{
    width:7px;
    height:7px;
    border-radius:50%;
    background:#666;
}}

.online .dot{{
    background:#fff;

    box-shadow:
        0 0 12px rgba(255,255,255,.9);
}}

.main{{
    font-size:30px;
    font-weight:850;
    letter-spacing:-1.2px;
    margin-bottom:18px;
}}

.grid{{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:10px;
}}

.stat{{
    padding:15px;

    border-radius:17px;

    background:rgba(255,255,255,.045);

    border:1px solid rgba(255,255,255,.055);
}}

.statLabel{{
    font-size:10px;
    color:#777;

    text-transform:uppercase;
    letter-spacing:.8px;

    margin-bottom:7px;
}}

.statValue{{
    font-size:16px;
    font-weight:800;

    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}}

.title{{
    font-size:19px;
    font-weight:850;
    letter-spacing:-.5px;
}}

.sub{{
    color:var(--muted);
    font-size:13px;
    line-height:1.45;
    margin:5px 0 17px;
}}

.primary{{
    display:flex;
    align-items:center;
    justify-content:center;

    width:100%;
    min-height:54px;

    border-radius:17px;

    background:#fff;
    color:#050505;

    text-decoration:none;

    font-size:15px;
    font-weight:850;

    transition:
        transform .15s,
        opacity .15s;

    box-shadow:
        0 14px 34px rgba(255,255,255,.08);
}}

.primary:active{{
    transform:scale(.98);
    opacity:.88;
}}

.actions{{
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:9px;
    margin-top:9px;
}}

.action{{
    min-height:48px;

    border:1px solid var(--line);
    border-radius:15px;

    background:rgba(255,255,255,.045);
    color:#fff;

    text-decoration:none;

    display:flex;
    align-items:center;
    justify-content:center;

    font-size:13px;
    font-weight:800;

    cursor:pointer;
}}

.urlBox{{
    display:flex;
    align-items:center;
    gap:7px;

    padding:6px;

    background:#080808;

    border:1px solid var(--line);
    border-radius:16px;
}}

.urlBox input{{
    min-width:0;
    flex:1;

    border:0;
    outline:0;

    background:transparent;
    color:#85858b;

    font-size:11px;
    padding:10px;
}}

.copy{{
    border:0;
    border-radius:11px;

    background:#fff;
    color:#000;

    padding:10px 12px;

    font-size:10px;
    font-weight:900;

    cursor:pointer;
}}

.notice{{
    display:flex;
    gap:11px;

    margin-top:13px;
    padding:14px;

    border-radius:17px;

    background:rgba(255,255,255,.035);

    border:1px solid rgba(255,255,255,.055);
}}

.check{{
    width:30px;
    height:30px;

    flex:0 0 30px;

    border-radius:10px;

    background:rgba(255,255,255,.08);

    display:grid;
    place-items:center;

    font-weight:900;
}}

.notice b{{
    font-size:13px;
}}

.notice p{{
    margin:4px 0 0;

    color:#777;

    font-size:11px;
    line-height:1.5;
}}

.error{{
    margin-top:10px;

    color:#8b8b90;

    font-size:11px;
    line-height:1.4;
}}

.footer{{
    text-align:center;

    color:#5f5f64;

    font-size:10px;
    line-height:1.6;

    padding:25px 0 4px;
}}

.footer a{{
    color:#888;
    text-decoration:none;
}}

.toast{{
    position:fixed;

    left:50%;
    bottom:
        calc(
            20px +
            env(safe-area-inset-bottom)
        );

    transform:
        translate(-50%,20px);

    opacity:0;
    pointer-events:none;

    background:#fff;
    color:#000;

    padding:12px 16px;

    border-radius:14px;

    font-size:12px;
    font-weight:850;

    transition:.25s;

    z-index:5;
}}

.toast.show{{
    transform:
        translate(-50%,0);

    opacity:1;
}}

@media(max-width:430px){{
    .hero h1{{
        font-size:37px;
    }}

    .main{{
        font-size:27px;
    }}
}}

</style>

</head>

<body>

<div class="container">

<header class="header">

    <div class="brandWrap">

        <div class="logo">
            <span>ix</span>
        </div>

        <div class="brand">
            ixxy VPN
        </div>

    </div>

    <div class="secure">
        SECURE ACCESS
    </div>

</header>


<section class="hero">

    <div class="eyebrow">
        Личный кабинет
    </div>

    <h1>
        Привет, {name}
    </h1>

    <p>
        Ваш VPN готов к подключению.<br>
        Без сложных настроек.
    </p>

</section>


<section class="card">

    <div class="statusTop">

        <div class="label">
            Состояние подписки
        </div>

        <div class="badge {status_class}">

            <span class="dot"></span>

            {status}

        </div>

    </div>

    <div class="main">
        {days_text}
    </div>

    <div class="grid">

        <div class="stat">

            <div class="statLabel">
                Тариф
            </div>

            <div class="statValue">
                {tariff}
            </div>

        </div>


        <div class="stat">

            <div class="statLabel">
                Действует до
            </div>

            <div class="statValue">
                {expiry}
            </div>

        </div>

    </div>

</section>


<section class="card">

    <div class="title">
        Подключение
    </div>

    <div class="sub">
        Защищённый импорт конфигурации
        в Happ. Серверные параметры
        на странице не отображаются.
    </div>

    <a
        class="primary"
        href="{happ_url}"
    >
        Подключить через Happ
    </a>

    <div class="actions">

        <a
            class="action"
            href="{incy_url}"
        >
            Открыть в INCY
        </a>

        <button
            class="action"
            onclick="copySubscription()"
        >
            Скопировать
        </button>

    </div>

    {error_html}

</section>


<section class="card">

    <div class="title">
        Моя подписка
    </div>

    <div class="sub">
        Ваша персональная ссылка
        для VPN-клиента.
    </div>

    <div class="urlBox">

        <input
            id="subUrl"
            readonly
            value="{html.escape(subscription_url, quote=True)}"
        >

        <button
            class="copy"
            onclick="copySubscription()"
        >
            COPY
        </button>

    </div>


    <div class="notice">

        <div class="check">
            ✓
        </div>

        <div>

            <b>
                Технические данные скрыты
            </b>

            <p>
                IP-адреса, порты, UUID,
                Reality и другие параметры
                серверов не выводятся
                в интерфейсе.
            </p>

        </div>

    </div>

</section>


<section class="card">

    <div class="title">
        Поддержка
    </div>

    <div class="sub">
        Если возникнут проблемы
        с подключением —
        напишите нам в Telegram.
    </div>

    <a
        class="primary"
        href="{html.escape(TELEGRAM_URL, quote=True)}"
    >
        Открыть поддержку
    </a>

</section>


<footer class="footer">

    ixxy VPN · {APP_VERSION}

    <br>

    Быстро. Приватно. Без лишнего.

</footer>

</div>


<div
    class="toast"
    id="toast"
>
    Ссылка скопирована
</div>


<script>

const SUB_URL = {subscription_url!r};


async function copySubscription() {{

    try {{

        await navigator.clipboard.writeText(
            SUB_URL
        );

    }} catch(e) {{

        const a =
            document.createElement(
                'textarea'
            );

        a.value = SUB_URL;

        a.style.position =
            'fixed';

        a.style.opacity =
            '0';

        document.body.appendChild(a);

        a.select();

        document.execCommand(
            'copy'
        );

        a.remove();
    }}

    const t =
        document.getElementById(
            'toast'
        );

    t.classList.add(
        'show'
    );

    setTimeout(
        () => t.classList.remove('show'),
        1600
    );
}}

</script>

</body>

</html>'''


# ============================================================
# MAIN
# ============================================================

@app.route("/")
def index():

    return """
<!doctype html>

<html lang="ru">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<meta
    name="theme-color"
    content="#050505"
>

<title>ixxy VPN</title>

<style>

*{
    box-sizing:border-box;
}

body{
    margin:0;
    min-height:100vh;

    background:#050505;
    color:#fff;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        Arial,
        sans-serif;

    display:grid;
    place-items:center;

    text-align:center;
}

main{
    width:min(90%,520px);
    padding:40px;
}

.logo{
    font-size:62px;
    font-weight:900;
    letter-spacing:-5px;
}

h1{
    font-size:40px;
    margin:10px 0;
}

p{
    color:#888;
    line-height:1.5;
}

a{
    display:block;

    margin-top:25px;
    padding:17px;

    border-radius:17px;

    background:#fff;
    color:#000;

    text-decoration:none;

    font-weight:800;
}

</style>

</head>

<body>

<main>

<div class="logo">
    ix
</div>

<h1>
    ixxy VPN
</h1>

<p>
    Быстрый и защищённый доступ
    <br>
    без лишних настроек.
</p>

<a href="https://t.me/orelvpntopbot">
    Открыть ixxy VPN
</a>

</main>

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
        mimetype="application/json",
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

    user_id = parse_token(
        token
    )

    if user_id is None:
        abort(404)

    try:

        user = get_user(
            user_id
        )

    except Exception as e:

        return Response(
            (
                "Database error: "
                + html.escape(
                    str(e)
                )
            ),
            status=500,
            mimetype="text/plain",
        )

    if not user:
        abort(404)

    # ========================================================
    # IMPORTANT:
    # database.py uses RealDictCursor.
    # Therefore user is a dict.
    # ========================================================

    first_name = (
        user.get("first_name")
        or user.get("username")
        or "Пользователь"
    )

    subscription = user.get(
        "subscription"
    )

    subscription_until = (
        user.get(
            "subscription_until"
        )
        or ""
    )

    page = render_page(
        token,
        first_name,
        subscription,
        subscription_until,
    )

    response = Response(
        page,
        mimetype="text/html",
    )

    response.headers.update(
        NO_CACHE_HEADERS
    )

    return response


# ============================================================
# PERMANENT SUBSCRIPTION
# ============================================================

@app.route("/sub/<token>")
def subscription(token):

    user_id = parse_token(
        token
    )

    if user_id is None:
        abort(404)

    try:

        user = get_user(
            user_id
        )

        if not user:
            abort(404)

        # ----------------------------------------------------
        # Обновляем subscription_content перед выдачей.
        #
        # Это важно:
        # если админ продлил подписку,
        # старая ссылка остаётся той же,
        # но содержимое должно стать актуальным.
        # ----------------------------------------------------

        try:

            update_subscription_file(
                user_id
            )

        except TypeError:

            # Совместимость со старой сигнатурой,
            # если функция принимает вторым аргументом дату.

            update_subscription_file(
                user_id,
                user.get(
                    "subscription_until"
                ),
            )

        content = get_subscription_content(
            user_id
        )

    except Exception as e:

        print(
            "Subscription endpoint error:",
            repr(e),
        )

        content = ""

    if not content:
        abort(404)

    response = Response(
        content,
        mimetype="text/plain",
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
        mimetype="text/plain",
    )


# ============================================================
# RUN
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