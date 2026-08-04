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

#announce: ‼️ Подписка активна до {date} ‼️
🚀 На многих серверах работает Gemini
📡 Наш VPN обходит любые глушилки
🆔 Ваш ID: {user_id}

vless://8b706aff-ca60-4632-9658-aeb5c0f48561@84.32.102.222:443?type=tcp&security=reality&pbk=TFT7MPZtAMZ7sQgoNlxK3dIX1j3I1oSyzl4fMXyk6Ww&fp=firefox&sni=nlch.dgtserv.xyz&sid=07494b3ed9ed2128&flow=xtls-rprx-vision#🇳🇱 Нидерланды

vless://eb78e1f0-d921-4ca9-a889-261fcc5a0547@78.159.250.214:443?type=tcp&security=reality&pbk=drY21DHNOr6ezJLA2B10mzTExeJ9-gVBfTBNLwVBtWI&fp=chrome&sni=qq.utiltools.ru&sid=&flow=xtls-rprx-vision#🇷🇺 При глушилках (временно недоступен)

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#Обходы б/с и wifi ⬆️
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
    
    
    
    # =====================
# ОБНОВЛЕНИЕ ФАЙЛА ПОСЛЕ ПРОДЛЕНИЯ
# =====================

def update_subscription_file(user_id, date):

    path = f"users/{user_id}.txt"


    update_file(
        path,
        ACTIVE_TEMPLATE.format(
            date=date
        )
    )