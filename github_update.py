import os
import base64
import requests
from datetime import datetime


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

OWNER = "bdtvyz76b6-blip"
REPO = "vpn-sub"


# =====================
# АКТИВНАЯ ПОДПИСКА
# =====================

ACTIVE_TEMPLATE = """
#profile-title: 🦅 Orel VPN
#profile-update-interval: 1
#announce: Подписка активна до {date}


vless://1833e2e7-ac13-4be3-b63d-f13b6ed195ad@185.81.115.233:8443?type=tcp&security=reality&pbk=AleVV90POpOeIxhTgPNAqVPXENd5u-yrIe_i6R5_NjQ&fp=firefox&sni=prod.cryptoofarm.com&sid=0f990c62cb6f5627&flow=xtls-rprx-vision#🇩🇪 GERMANY 🛜 🦅

vless://6949d13a-6695-4ef6-95a6-59f5a17c0978@189.74.114.135:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=api.yandex-dev.org&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇧🇷 BRAZIL 🛜 🦅

vless://391c4575-3195-4917-817c-f7f26fa7fe5b@82.202.177.145:5269?type=tcp&security=reality&pbk=dvue8xDyKMWNJELyMBrEYLy5SezehG_FOtDrDl-bVGQ&fp=firefox&sni=max.ru&sid=9473acb8aaf08627#🇷🇺 LTE | Россия 📶 🦅

vless://1833e2e7-ac13-4be3-b63d-f13b6ed195ad@95.181.212.109:443?type=tcp&security=reality&pbk=xM7dyVtRXmZoSTY0S38BAC0XZrcE3qoWyu-PWIAi9ms&fp=firefox&sni=ya.ru&sid=4257ea33bd10bc0e&flow=xtls-rprx-vision#🇩🇪 LTE | Германия 📶 🦅

vless://1833e2e7-ac13-4be3-b63d-f13b6ed195ad@212.193.153.47:443?type=ws&security=tls&host=s30515.cdn.ngenix.net&path=/v1/data/sync/&sni=s30515.cdn.ngenix.net&fp=chrome#🇳🇱 LTE | Нидерланды 📶 🦅
"""


# =====================
# ИСТЕКШАЯ ПОДПИСКА
# =====================

EXPIRED_TEMPLATE = """
#profile-title: ⛔ Orel VPN
#profile-update-interval: 1
#announce: Срок действия VIP-подписки закончился. Обратитесь к @orelvpntopbot для продления.


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision# Продлите в @orelvpntopbot


vless://c61ec320-29f1-4e00-9272-8b676e6957b4@telegram.looks-free.rutube.info:443?type=tcp&security=reality&sni=tradingview.com&fp=qq&pbk=Lbug_wz0y9xgKeDK44D9kuUap0fXzNKyv_nMJxnZRzU&sid=08&flow=xtls-rprx-vision# Для Telegram @orelvpntopbot
"""


# =====================
# GITHUB
# =====================

def github_headers():

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }



def github_url(path):

    return (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/{path}"
    )



# =====================
# СОЗДАНИЕ / ОБНОВЛЕНИЕ
# =====================

def update_file(path, content):

    url = github_url(path)


    old = requests.get(
        url,
        headers=github_headers()
    )


    data = {
        "message": "Update Orel VPN subscription",
        "content": base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")
    }


    if old.status_code == 200:
        data["sha"] = old.json()["sha"]


    response = requests.put(
        url,
        headers=github_headers(),
        json=data
    )


    response.raise_for_status()



# =====================
# ВЫДАТЬ ПОДПИСКУ
# =====================

def create_subscription(user_id):

    date = datetime.now().strftime(
        "%d.%m.%Y"
    )


    content = ACTIVE_TEMPLATE.format(
        date=date
    )


    path = f"users/{user_id}.txt"


    update_file(
        path,
        content
    )


    return (
        "https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/main/{path}"
    )



# =====================
# ИСТЕЧЕНИЕ
# =====================

def expire_subscription(user_id):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        EXPIRED_TEMPLATE
    )