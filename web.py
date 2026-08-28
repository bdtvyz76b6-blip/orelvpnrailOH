import os

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
# ГЛАВНАЯ
# =========================================================

@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>☂️ ixxy vpn</title>

<style>
body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0b0b0f;
    color: white;
    font-family: Arial, sans-serif;
}

.card {
    width: 90%;
    max-width: 480px;
    padding: 35px;
    text-align: center;
    background: #15151c;
    border-radius: 24px;
}

h1 {
    margin-bottom: 10px;
}

p {
    color: #aaa;
}
</style>
</head>

<body>

<div class="card">

<h1>☂️ ixxy vpn</h1>

<p>
Веб-сервис подписок работает
</p>

</div>

</body>
</html>
"""


# =========================================================
# HEALTH CHECK
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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ixxy vpn</title>
</head>

<body style="
margin:0;
background:#0b0b0f;
color:white;
font-family:Arial;
display:flex;
align-items:center;
justify-content:center;
min-height:100vh;
">

<div style="
background:#15151c;
padding:30px;
border-radius:20px;
text-align:center;
">

<h2>⛔ Подписка не найдена</h2>

<p style="color:#aaa;">
Проверьте ссылку подписки
</p>

</div>

</body>
</html>
""", 404

        subscription_url = (
            f"{PUBLIC_SITE_URL}/sub/{token}"
        )

        return f"""
<!DOCTYPE html>
<html lang="ru">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>☂️ ixxy vpn</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    min-height: 100vh;

    display: flex;
    align-items: center;
    justify-content: center;

    background: #0b0b0f;

    color: white;

    font-family: Arial, sans-serif;

    padding: 20px;
}}

.card {{
    width: 100%;
    max-width: 500px;

    background: #15151c;

    border-radius: 24px;

    padding: 30px;

    text-align: center;

    box-shadow:
        0 15px 50px rgba(0,0,0,.45);
}}

h1 {{
    margin: 0 0 10px;
    font-size: 28px;
}}

p {{
    color: #aaa;
    line-height: 1.5;
}}

.id {{
    margin: 20px 0;

    padding: 14px;

    background: #20202a;

    border-radius: 14px;

    font-size: 15px;
}}

.button {{
    display: block;

    width: 100%;

    padding: 16px;

    margin-top: 12px;

    border-radius: 14px;

    border: 0;

    text-decoration: none;

    font-size: 16px;

    font-weight: bold;

    cursor: pointer;
}}

.primary {{
    background: white;
    color: black;
}}

.secondary {{
    background: #24242f;
    color: white;
}}

</style>

</head>

<body>

<div class="card">

<h1>☂️ ixxy vpn</h1>

<p>
Ваша персональная ссылка подписки
</p>

<div class="id">
🆔 ID: {user_id}
</div>

<a
class="button primary"
href="{subscription_url}"
>
📡 Открыть подписку
</a>

<button
class="button secondary"
onclick="copyLink()"
>
📋 Скопировать ссылку
</button>

</div>

<script>

function copyLink() {{

    const link = "{subscription_url}";

    if (navigator.clipboard) {{

        navigator.clipboard.writeText(link)

        .then(() => {{
            alert("✅ Ссылка скопирована");
        }})

        .catch(() => {{
            prompt("Скопируйте ссылку:", link);
        }});

    }} else {{

        prompt("Скопируйте ссылку:", link);

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