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

vless://52d0b2d5-a003-4509-ab70-d1d720a14cd7@37.221.210.181:443?type=xhttp&security=reality&pbk=z-TKWOWgZLfzQ-wNdwXQqVwaUgCmbchM2Xtrk1NGynU&fp=qq&sni=hu007.bearbeer.digital&path=/&mode=auto&encryption=none#🇳🇱 Netherlands

vless://26cd92ed-2bff-4e97-963a-d5ec374ba8f8@87.121.86.120:443?type=tcp&security=reality&pbk=z-TKWOWgZLfzQ-wNdwXQqVwaUgCmbchM2Xtrk1NGynU&fp=qq&sni=ee001.bearbeer.digital&flow=xtls-rprx-vision&encryption=none#🇧🇬 Bulgaria

vless://0c1b9d61-377e-41d5-9be4-d0035d851a10@64.188.81.56:443?type=tcp&security=reality&pbk=SwfpVdTE6Ay33LQpgRl2Q97t7HFrGREkpE7E1A6pCD4&fp=qq&sni=api-maps.yandex.ru&flow=xtls-rprx-vision&encryption=none#🇺🇸 USA

vless://4fcd5a7f-0cd8-4259-a8cc-65c23ab81a13@195.209.88.3:443?type=ws&security=tls&host=s30515.cdn.ngenix.net&path=/v1/data/sync/&fp=chrome&sni=s30515.cdn.ngenix.net&encryption=none#🇸🇨 LTE | Универсальный

"""


EXPIRED_TEMPLATE = """
#profile-title: ⛔ Orel VPN

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