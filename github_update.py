import os
import base64
import requests

from datetime import datetime, timedelta


GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)


print(
    "GITHUB_TOKEN:",
    GITHUB_TOKEN[:10] if GITHUB_TOKEN else "EMPTY"
)


OWNER = "bdtvyz76b6-blip"

REPO = "vpn-sub"

BRANCH = "main"



# =====================
# НОВЫЙ ПОЛЬЗОВАТЕЛЬ
# =====================


NEW_USER_TEMPLATE = """
#profile-title: 🦅 Orel VPN

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#❌ Подписка отсутствует


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#Активировать в @orelvpntopbot


vless://c61ec320-29f1-4e00-9272-8b676e6957b4@telegram.looks-free.rutube.info:443?type=tcp&security=reality&sni=tradingview.com&fp=qq&pbk=Lbug_wz0y9xgKeDK44D9kuUap0fXzNKyv_nMJxnZRzU&sid=08&flow=xtls-rprx-vision#Telegram

"""





# =====================
# АКТИВНАЯ ПОДПИСКА
# =====================


ACTIVE_TEMPLATE = """
#profile-title: 🦅 Orel VPN

#profile-update-interval: 1

#announce: Подписка активна до {date}



vless://1833e2e7-ac13-4be3-b63d-f13b6ed195ad@185.81.115.233:8443?type=tcp&security=reality&pbk=AleVV90POpOeIxhTgPNAqVPXENd5u-yrIe_i6R5_NjQ&fp=firefox&sni=prod.cryptoofarm.com&sid=0f990c62cb6f5627&flow=xtls-rprx-vision#🇩🇪 Germany


vless://6949d13a-6695-4ef6-95a6-59f5a17c0978@189.74.114.135:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=api.yandex-dev.org&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇧🇷 Brazil


vless://505386b6-8740-11f1-9ca5-1e6febe3e1df@95.163.183.109:2053?encryption=none&security=reality&type=grpc&serviceName=grpc-direct&mode=gun&pbk=WUY8Lb4LfUUKLzZK3oSlRAdoy-Iu0w3Ait1-jtxbW1M&sni=hh.ru&sid=4b685844d0b4f724&fp=chrome#🇷🇺 LTE | Russia


vless://505386b6-8740-11f1-9ca5-1e6febe3e1df@95.163.183.109:2053?encryption=none&security=reality&type=grpc&serviceName=grpc-direct&mode=gun&pbk=WUY8Lb4LfUUKLzZK3oSlRAdoy-Iu0w3Ait1-jtxbW1M&sni=hh.ru&sid=4b685844d0b4f724&fp=chrome#🇫🇮 LTE | Finland


vless://505386b6-8740-11f1-9ca5-1e6febe3e1df@95.163.183.109:2053?encryption=none&security=reality&type=grpc&serviceName=grpc-direct&mode=gun&pbk=WUY8Lb4LfUUKLzZK3oSlRAdoy-Iu0w3Ait1-jtxbW1M&sni=hh.ru&sid=4b685844d0b4f724&fp=chrome#🇸🇪 LTE | Sweden

"""





# =====================
# ИСТЕКШАЯ
# =====================


EXPIRED_TEMPLATE = """
#profile-title: ⛔ Orel VPN

#profile-update-interval: 1

#announce: Срок действия подписки закончился. Продлите у @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#Продлите в @orelvpntopbot
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
# ОБНОВЛЕНИЕ ФАЙЛА
# =====================


def update_file(path, content):

    url = github_url(path)


    old = requests.get(
        url,
        headers=github_headers()
    )


    data = {

        "message":
        "Update Orel VPN subscription",

        "content":
        base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8"),

        "branch":
        BRANCH
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
# СОЗДАТЬ ФАЙЛ ПОСЛЕ START
# =====================


def create_user_subscription(user_id):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        NEW_USER_TEMPLATE
    )


    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )






# =====================
# АКТИВИРОВАТЬ ПОСЛЕ ОПЛАТЫ
# =====================


def create_subscription(user_id, days=30):

    expire_date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime(
        "%d.%m.%Y"
    )


    content = ACTIVE_TEMPLATE.format(
        date=expire_date
    )


    path = f"users/{user_id}.txt"


    update_file(
        path,
        content
    )


    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
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