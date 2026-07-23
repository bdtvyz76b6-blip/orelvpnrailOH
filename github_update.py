import os
import base64
import requests

from config import BS_LINK


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OWNER = "bdtvyz76b6-blip"
REPO = "vpn-sub"
BRANCH = "main"


def get_active_content():
    r = requests.get(BS_LINK)
    return r.text


EXPIRED_CONTENT = """#profile-title: ⛔ Orel VPN
#profile-update-interval: 1
#announce: Срок действия VIP-подписки закончился. Обратитесь к @orelvpntopbot для продления.

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#Продлите в @orelvpntopbot

vless://c61ec320-29f1-4e00-9272-8b676e6957b4@telegram.looks-free.rutube.info:443?type=tcp&security=reality&sni=tradingview.com&fp=qq&pbk=Lbug_wz0y9xgKeDK44D9kuUap0fXzNKyv_nMJxnZRzU&sid=08&flow=xtls-rprx-vision#Для Telegram @orelvpntopbot
"""


def update_file(path, content, message):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    r = requests.get(url, headers=headers)

    sha = None
    if r.status_code == 200:
        sha = r.json().get("sha")

    data = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": BRANCH
    }

    if sha:
        data["sha"] = sha

    requests.put(url, headers=headers, json=data)


def create_subscription(user_id):
    content = get_active_content()
    path = f"users/{user_id}.txt"

    update_file(
        path,
        content,
        f"Create/update subscription for {user_id}"
    )

    return f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{path}"


def expire_subscription(user_id):
    path = f"users/{user_id}.txt"

    update_file(
        path,
        EXPIRED_CONTENT,
        f"Expire subscription for {user_id}"
    )