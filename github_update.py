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


vless://8def1e12-9c10-48a4-b9eb-a5cfdd552e18@189.74.115.2:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=api.yandex-dev.online&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇧🇷 brazil

vless://8def1e12-9c10-48a4-b9eb-a5cfdd552e18@159.195.47.170:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=at.c2horizon.app&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇳🇱 netherlands

vless://8def1e12-9c10-48a4-b9eb-a5cfdd552e18@77.91.68.206:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=am.c2horizon.app&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇳🇱 netherlands 2

vless://8def1e12-9c10-48a4-b9eb-a5cfdd552e18@192.241.126.174:443?type=tcp&security=reality&pbk=IuvAXlAWBpeXehmEk0P-FIGTctUhny2H3UilbWWfJC0&fp=qq&sni=ads.yandex-dev.online&sid=122218f4c1f172e4&flow=xtls-rprx-vision#🇺🇸 usa

vless://42d3cfb6-8a1d-11f1-9ca5-1e6febe3e1df@95.163.183.109:2053?type=grpc&serviceName=grpc-direct&security=reality&pbk=WUY8Lb4LfUUKLzZK3oSlRAdoy-Iu0w3Ait1-jtxbW1M&fp=chrome&sni=hh.ru&sid=e432eea05ffadf84#🇸🇨 LTE | universal
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