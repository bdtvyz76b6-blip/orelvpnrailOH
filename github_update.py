import os
import base64
import requests

from datetime import datetime, timedelta

from database import save_subscription_link


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("❌ GITHUB_TOKEN не найден")


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



NEW_USER_TEMPLATE = """
#profile-title: ☂️ ixxy vpn

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку

"""


ACTIVE_TEMPLATE = """
#profile-title: ☂️ ixxy vip

#profile-update-interval: 1

#announce: Подписка активна до {date}


vless://8b706aff-ca60-4632-9658-aeb5c0f48561@84.32.102.222:443?type=tcp&security=reality&pbk=TFT7MPZtAMZ7sQgoNlxK3dIX1j3I1oSyzl4fMXyk6Ww&fp=firefox&sni=nlch.dgtserv.xyz&sid=07494b3ed9ed2128&flow=xtls-rprx-vision#🇳🇱 нидерланды

vless://2c634977-584e-4e1f-b501-1b70c77a6743@78.159.245.32:28474?type=tcp&security=tls&sni=secure.furrycdn.net&fp=chrome&flow=xtls-rprx-vision#🇳🇱 нидерланды-2

vless://d6f56765-c9b4-4b40-8d0c-48b724886074@78.159.245.32:28473?type=tcp&security=tls&sni=secure.furrycdn.net&fp=firefox&flow=xtls-rprx-vision#🇳🇱 нидерланды-3

vless://d82891a6-48da-4b5a-bc50-3d861478be2a@91.185.83.94:4443?type=tcp&security=reality&pbk=7nfL5nnISA027dQ-thHwql8JquJwH09zZJrYrw994XU&fp=firefox&sni=5post-gate.x5.ru&flow=xtls-rprx-vision#🇳🇱 нидерланды-4

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#обходы б/с скоро ⬆️
"""


EXPIRED_TEMPLATE = """
#profile-title: ⛔ ixxy vpn

#profile-update-interval: 1

#announce: Срок действия подписки закончился. Продлите у @orelvpntopbot


vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла

"""



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
        ).decode("utf-8"),

        "branch": BRANCH
    }


    if old.status_code == 200:

        data["sha"] = old.json()["sha"]


    r = requests.put(
        url,
        headers=github_headers(),
        json=data
    )

    r.raise_for_status()



def create_user_subscription(user_id):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        NEW_USER_TEMPLATE
    )


    link = (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )


    save_subscription_link(
        user_id,
        link
    )


    return link



def create_subscription(user_id, days=30):

    expire_date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime("%d.%m.%Y")


    path = f"users/{user_id}.txt"


    update_file(
        path,
        ACTIVE_TEMPLATE.format(
            date=expire_date
        )
    )


    link = (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )


    save_subscription_link(
        user_id,
        link
    )


    return link



def activate_user_subscription(user_id, days):

    return create_subscription(
        user_id,
        days
    )



def expire_subscription(user_id):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        EXPIRED_TEMPLATE
    )