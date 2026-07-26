import os
import base64
import requests

from datetime import datetime, timedelta


# =====================
# GITHUB
# =====================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN"
)

if not GITHUB_TOKEN:
    raise Exception(
        "❌ GITHUB_TOKEN не найден"
    )


OWNER = "bdtvyz76b6-blip"

REPO = "vpn-sub"

BRANCH = "main"



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
# ШАБЛОНЫ
# =====================


NEW_USER_TEMPLATE = """
#profile-title: 🦅 Orel VPN

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку

"""



ACTIVE_TEMPLATE = """
#profile-title: 🦅 Orel VPN VIP

#profile-update-interval: 1

#announce: Подписка активна до {date}



vless://8fbd33cf-ff7b-4352-a48d-0cd4f723c7e4@189.74.106.66:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=safari&sni=api.yandex-cloud.org&sid=122218f4c1f172e4&flow=xtls-rprx-vision&encryption=none#🇧🇷 Brazil


vless://8fbd33cf-ff7b-4352-a48d-0cd4f723c7e4@189.74.117.4:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=edge&sni=api.yandex-api.org&sid=122218f4c1f172e4&flow=xtls-rprx-vision&encryption=none#🇧🇷 Brazil Reserve


vless://52d0b2d5-a003-4509-ab70-d1d720a14cd7@95.85.253.107:443?type=tcp&security=reality&pbk=z-TKWOWgZLfzQ-wNdwXQqVwaUgCmbchM2Xtrk1NGynU&fp=qq&sni=pl20.bearbeer.digital&flow=xtls-rprx-vision&encryption=none&spx=/#🇳🇱 Netherlands


vless://96006428-88d4-11f1-9ca5-1e6febe3e1df@89.208.229.243:2053?type=grpc&serviceName=grpc-direct&security=reality&pbk=WUY8Lb4LfUUKLzZK3oSlRAdoy-Iu0w3Ait1-jtxbW1M&fp=chrome&sni=hh.ru&sid=7824dfd19eab1acc&encryption=none#🇸🇨 LTE

"""



EXPIRED_TEMPLATE = """
#profile-title: ⛔ Orel VPN

#profile-update-interval: 1

#announce: Срок действия подписки закончился. Продлите у @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла

"""



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
            content.encode()
        ).decode(),

        "branch":
        BRANCH
    }


    if old.status_code == 200:

        data["sha"] = old.json()["sha"]



    r = requests.put(
        url,
        headers=github_headers(),
        json=data
    )


    r.raise_for_status()



# =====================
# СОЗДАТЬ ПУСТОЙ ФАЙЛ
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
# АКТИВАЦИЯ
# =====================


def activate_user_subscription(
        user_id,
        days
):

    date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime(
        "%d.%m.%Y"
    )


    path = f"users/{user_id}.txt"


    update_file(
        path,
        ACTIVE_TEMPLATE.format(
            date=date
        )
    )


    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )



# =====================
# ИСТЕКЛА
# =====================


def expire_subscription(user_id):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        EXPIRED_TEMPLATE
    )