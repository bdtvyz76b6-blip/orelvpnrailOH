import os
from urllib.parse import quote
from flask import Flask, Response, abort
from database import get_subscription_content
app = Flask(__name__)
# =========================================================
# НАСТРОЙКИ
# =========================================================
PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")
SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()
# =========================================================
# TOKEN → USER ID
# =========================================================
def get_user_id_from_token(token):
    if not token.startswith(SUBSCRIPTION_PREFIX):
        return None
    user_id = token[len(SUBSCRIPTION_PREFIX):]
    if not user_id.isdigit():
        return None
    return int(user_id)
# =========================================================
# ПОЛУЧЕНИЕ ССЫЛКИ ПОДПИСКИ
# =========================================================
def get_subscription_url(token):
    return f"{PUBLIC_SITE_URL}/sub/{token}"
# =========================================================
# ГЛАВНАЯ
# =========================================================
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">
<title>☂️ ixxy vpn</title>
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
    background:
        radial-gradient(
            circle at 15% 20%,
            rgba(119, 75, 255, .35),
            transparent 35%
        ),
        radial-gradient(
            circle at 85% 80%,
            rgba(0, 220, 255, .25),
            transparent 35%
        ),
        #080810;
    color: white;
    font-family: -apple-system, BlinkMacSystemFont,
                 "SF Pro Display", Arial, sans-serif;
    padding: 20px;
}
.card {
    width: 100%;
    max-width: 520px;
    padding: 40px 28px;
    border-radius: 32px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.10),
            rgba(255,255,255,.035)
        );
    border: 1px solid rgba(255,255,255,.12);
    backdrop-filter: blur(25px);
    text-align: center;
    box-shadow:
        0 30px 100px rgba(0,0,0,.5);
}
.logo {
    font-size: 64px;
}
h1 {
    margin: 8px 0;
    font-size: 34px;
    background:
        linear-gradient(
            90deg,
            #ffffff,
            #a78bfa,
            #22d3ee
        );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
p {
    color: #a5a5b5;
}
</style>
</head>
<body>
<div class="card">
<div class="logo">☂️</div>
<h1>ixxy vpn</h1>
<p>
Веб-сервис подписок работает
</p>
</div>
</body>
</html>
"""
# =========================================================
# HEALTH
# =========================================================
@app.route("/health")
def health():
    return "OK", 200
# =========================================================
# СТРАНИЦА ПОДПИСКИ
# =========================================================
@app.route("/s/<token>")
def subscription_page(token):
    try:
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
<title>ixxy vpn</title>
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
    padding: 20px;
    background:
        radial-gradient(
            circle at 20% 10%,
            rgba(255, 60, 120, .25),
            transparent 35%
        ),
        #080810;
    color: white;
    font-family: Arial, sans-serif;
}
.card {
    width: 100%;
    max-width: 480px;
    padding: 35px;
    text-align: center;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 30px;
    backdrop-filter: blur(25px);
}
.icon {
    font-size: 60px;
}
h1 {
    margin: 15px 0 8px;
}
p {
    color: #aaa;
}
</style>
</head>
<body>
<div class="card">
<div class="icon">⛔</div>
<h1>Подписка не найдена</h1>
<p>
Проверьте ссылку или обратитесь в поддержку.
</p>
</div>
</body>
</html>
""", 404
        subscription_url = get_subscription_url(token)
        # URL-кодируем подписку для deep-link
        encoded_subscription_url = quote(
            subscription_url,
            safe=""
        )
        # INCY
        incy_url = (
            f"incy://add/{encoded_subscription_url}"
        )
        # Happ
        happ_url = (
            f"happ://add/{encoded_subscription_url}"
        )
        # =====================================================
        # ПЫТАЕМСЯ ОПРЕДЕЛИТЬ СТАТУС
        # =====================================================
        active = True
        if "Подписка истекла" in content:
            active = False
        if "Активируйте подписку" in content:
            active = False
        # =====================================================
        # ДАТА
        # =====================================================
        expire_text = "Активна"
        marker = "до "
        if marker in content:
            try:
                part = content.split(marker, 1)[1]
                expire_text = (
                    part
                    .split("‼️", 1)[0]
                    .strip()
                )
            except Exception:
                expire_text = "Активна"
        if not active:
            status_text = "Подписка истекла"
            status_class = "expired"
            status_icon = "⛔"
        else:
            status_text = "Подписка активна"
            status_class = "active"
            status_icon = "✓"
        # =====================================================
        # HTML
        # =====================================================
        return f"""
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
    content="#090912"
>
<title>☂️ ixxy vpn</title>
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
    color: #fff;
    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "SF Pro Text",
        Arial,
        sans-serif;
    background:
        radial-gradient(
            circle at 5% 5%,
            rgba(168, 85, 247, .32),
            transparent 30%
        ),
        radial-gradient(
            circle at 95% 20%,
            rgba(34, 211, 238, .25),
            transparent 32%
        ),
        radial-gradient(
            circle at 50% 100%,
            rgba(236, 72, 153, .25),
            transparent 35%
        ),
        #07070d;
    overflow-x: hidden;
}}
.background {{
    position: fixed;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
    z-index: 0;
}}
.orb {{
    position: absolute;
    width: 260px;
    height: 260px;
    border-radius: 50%;
    filter: blur(80px);
    opacity: .28;
    animation: float 8s ease-in-out infinite;
}}
.orb.one {{
    background: #7c3aed;
    top: -100px;
    left: -80px;
}}
.orb.two {{
    background: #06b6d4;
    right: -100px;
    top: 35%;
    animation-delay: -3s;
}}
.orb.three {{
    background: #ec4899;
    left: 20%;
    bottom: -150px;
    animation-delay: -5s;
}}
@keyframes float {{
    0%,100% {{
        transform: translateY(0) scale(1);
    }}
    50% {{
        transform: translateY(-25px) scale(1.08);
    }}
}}
.container {{
    position: relative;
    z-index: 1;
    width: 100%;
    max-width: 560px;
    margin: 0 auto;
    padding: 28px 18px 35px;
}}
.header {{
    text-align: center;
    margin-bottom: 22px;
}}
.logo {{
    width: 76px;
    height: 76px;
    margin: 0 auto 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 24px;
    font-size: 42px;
    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #ec4899,
            #06b6d4
        );
    box-shadow:
        0 15px 45px rgba(124,58,237,.45);
    animation: logoPulse 3s ease-in-out infinite;
}}
@keyframes logoPulse {{
    0%,100% {{
        transform: translateY(0);
    }}
    50% {{
        transform: translateY(-5px);
    }}
}}
.brand {{
    margin: 0;
    font-size: 36px;
    font-weight: 900;
    letter-spacing: -1.5px;
    background:
        linear-gradient(
            90deg,
            #fff,
            #c4b5fd,
            #67e8f9
        );
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.subtitle {{
    margin-top: 8px;
    color: #9898a8;
    font-size: 15px;
}}
.main-card {{
    padding: 22px;
    border-radius: 30px;
    background:
        linear-gradient(
            145deg,
            rgba(255,255,255,.105),
            rgba(255,255,255,.035)
        );
    border:
        1px solid rgba(255,255,255,.12);
    backdrop-filter: blur(30px);
    box-shadow:
        0 25px 90px rgba(0,0,0,.45);
}}
.status {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 18px;
    margin-bottom: 18px;
    font-weight: 700;
}}
.status.active {{
    background:
        rgba(34,197,94,.12);
    border:
        1px solid rgba(34,197,94,.22);
    color: #86efac;
}}
.status.expired {{
    background:
        rgba(239,68,68,.12);
    border:
        1px solid rgba(239,68,68,.22);
    color: #fca5a5;
}}
.status-dot {{
    width: 11px;
    height: 11px;
    border-radius: 50%;
    background: currentColor;
    box-shadow:
        0 0 16px currentColor;
}}
.info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
}}
.info {{
    padding: 18px;
    border-radius: 20px;
    background:
        rgba(255,255,255,.055);
    border:
        1px solid rgba(255,255,255,.07);
}}
.info-label {{
    color: #888899;
    font-size: 12px;
    margin-bottom: 7px;
}}
.info-value {{
    font-size: 16px;
    font-weight: 800;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}
.buttons {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}
.button {{
    width: 100%;
    min-height: 58px;
    border: 0;
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: white;
    text-decoration: none;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
    transition:
        transform .18s ease,
        filter .18s ease;
}}
.button:active {{
    transform: scale(.97);
}}
.button:hover {{
    filter: brightness(1.1);
}}
.happ {{
    background:
        linear-gradient(
            135deg,
            #7c3aed,
            #a855f7,
            #ec4899
        );
    box-shadow:
        0 12px 35px rgba(168,85,247,.30);
}}
.incy {{
    background:
        linear-gradient(
            135deg,
            #06b6d4,
            #2563eb,
            #4f46e5
        );
    box-shadow:
        0 12px 35px rgba(37,99,235,.30);
}}
.copy {{
    background:
        rgba(255,255,255,.08);
    border:
        1px solid rgba(255,255,255,.11);
}}
.share {{
    background:
        rgba(236,72,153,.10);
    border:
        1px solid rgba(236,72,153,.20);
}}
.small-text {{
    text-align: center;
    color: #737383;
    font-size: 12px;
    line-height: 1.5;
    margin-top: 20px;
}}
.footer {{
    text-align: center;
    color: #555566;
    font-size: 12px;
    margin-top: 22px;
}}
.toast {{
    position: fixed;
    left: 50%;
    bottom: 25px;
    transform:
        translate(-50%, 120px);
    z-index: 20;
    padding: 14px 20px;
    border-radius: 16px;
    background:
        rgba(25,25,35,.94);
    border:
        1px solid rgba(255,255,255,.12);
    backdrop-filter: blur(20px);
    box-shadow:
        0 15px 45px rgba(0,0,0,.45);
    font-weight: 700;
    transition:
        transform .3s ease;
}}
.toast.show {{
    transform:
        translate(-50%, 0);
}}
@media (max-width: 430px) {{
    .container {{
        padding: 20px 13px 30px;
    }}
    .main-card {{
        padding: 17px;
        border-radius: 26px;
    }}
    .brand {{
        font-size: 32px;
    }}
    .info {{
        padding: 15px;
    }}
    .button {{
        min-height: 56px;
    }}
}}
</style>
</head>
<body>
<div class="background">
<div class="orb one"></div>
<div class="orb two"></div>
<div class="orb three"></div>
</div>
<div class="container">
<div class="header">
<div class="logo">
☂️
</div>
<h1 class="brand">
ixxy vpn
</h1>
<div class="subtitle">
Персональная подписка
</div>
</div>
<div class="main-card">
<div class="status {status_class}">
<div class="status-dot"></div>
<span>
{status_icon} {status_text}
</span>
</div>
<div class="info-grid">
<div class="info">
<div class="info-label">
📅 Срок действия
</div>
<div class="info-value">
{expire_text}
</div>
</div>
<div class="info">
<div class="info-label">
🆔 Ваш ID
</div>
<div class="info-value">
{user_id}
</div>
</div>
</div>
<div class="buttons">
<a
class="button happ"
href="{happ_url}"
>
📡 Добавить в Happ
</a>
<a
class="button incy"
href="{incy_url}"
>
⚡ Добавить в INCY
</a>
<button
class="button copy"
onclick="copySubscription()"
>
📋 Скопировать ссылку
</button>
<button
class="button share"
onclick="shareSubscription()"
>
↗️ Поделиться
</button>
</div>
<div class="small-text">
Нажмите на приложение выше, чтобы
добавить персональную подписку.
Если приложение не открылось —
используйте «Скопировать ссылку».
</div>
</div>
<div class="footer">
☂️ ixxy vpn • Быстро • Удобно • Надёжно
</div>
</div>
<div id="toast" class="toast">
✅ Ссылка скопирована
</div>
<script>
const subscriptionUrl = {subscription_url!r};
function showToast(text) {{
    const toast =
        document.getElementById("toast");
    toast.textContent = text;
    toast.classList.add("show");
    setTimeout(() => {{
        toast.classList.remove("show");
    }}, 2200);
}}
async function copySubscription() {{
    try {{
        await navigator.clipboard.writeText(
            subscriptionUrl
        );
        showToast("✅ Ссылка скопирована");
    }} catch (error) {{
        prompt(
            "Скопируйте ссылку:",
            subscriptionUrl
        );
    }}
}}
async function shareSubscription() {{
    if (
        navigator.share
    ) {{
        try {{
            await navigator.share({{
                title: "☂️ ixxy vpn",
                text: "Моя подписка ixxy vpn",
                url: subscriptionUrl
            }});
        }} catch (error) {{
        }}
    }} else {{
        await copySubscription();
    }}
}}
</script>
</body>
</html>
"""
    except Exception as e:
        print(
            "❌ WEB ERROR /s:",
            repr(e),
            flush=True
        )
        return (
            "Internal Server Error: "
            + str(e),
            500,
        )
# =========================================================
# ЧИСТАЯ ПОДПИСКА
# =========================================================
@app.route("/sub/<token>")
def subscription_content(token):
    try:
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
    except Exception as e:
        print(
            "❌ WEB ERROR /sub:",
            repr(e),
            flush=True
        )
        return Response(
            "Web server error",
            status=500,
            mimetype="text/plain",
        )
# =========================================================
# ЗАПУСК
# =========================================================
if __name__ == "__main__":
    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )
    print(
        f"☂️ ixxy vpn web server started on port {port}",
        flush=True
    )
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
    )