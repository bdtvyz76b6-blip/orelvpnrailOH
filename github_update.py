import os
import base64
import requests

from datetime import datetime, timedelta

from database import (
    save_subscription_link,
    get_all_users
)


# =====================
# GITHUB
# =====================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("❌ GITHUB_TOKEN не найден")


OWNER = "bdtvyz76b6-blip"
REPO = "vpn-sub"
BRANCH = "main"


# =====================
# ОБЩИЙ СПИСОК СЕРВЕРОВ
# =====================

SERVERS = """
vless://8b706aff-ca60-4632-9658-aeb5c0f48561@84.32.102.222:443?type=tcp&security=reality&pbk=TFT7MPZtAMZ7sQgoNlxK3dIX1j3I1oSyzl4fMXyk6Ww&fp=firefox&sni=nlch.dgtserv.xyz&sid=07494b3ed9ed2128&flow=xtls-rprx-vision#🇳🇱 Нидерланды #1

vless://65761043-f5c1-4e7b-8c16-b72c7a3fa4b7@nl.superbuba.top:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=nl.superbuba.top&fp=firefox&pbk=z37XIezsPyfMgmdXyFd9qT4C4maDAs1OcRt-wfyrXVo&sid=9c2378562188c3cb#🇳🇱 Нидерланды #2

vless://65761043-f5c1-4e7b-8c16-b72c7a3fa4b7@it.superbuba.top:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=it.superbuba.top&fp=firefox&pbk=G2U8_BvRAgcOw0sX8u_0yYdVAlD8CWLSi-uYjvH07hw&sid=4fa44664f6a566d3#🇮🇹 Италия #1

vless://65761043-f5c1-4e7b-8c16-b72c7a3fa4b7@mur.burladuck.com:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.vk.com&fp=firefox&pbk=nkpZyXHfG7nhEh1vjBjEDV-Tn7UhHEb5iN9iA8gc9VE&sid=c31188450fe50718#🇷🇺 При глушилках #1

vless://65761043-f5c1-4e7b-8c16-b72c7a3fa4b7@185.229.9.236:49005?encryption=none&flow=xtls-rprx-vision&security=reality&sni=max.ru&fp=firefox&pbk=dzjhpiDcvFBRzIODtrUVADf24qFE-636IVIdEof0XFQ&sid=512acc0133720b9e#🇷🇺 При глушилках #2

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#Обходы б/с и wifi ⬆️
""".strip()


# =====================
# ШАБЛОНЫ
# =====================

NEW_USER_TEMPLATE = f"""
#profile-title: ☂️ ixxy vpn

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку
""".strip()


EXPIRED_TEMPLATE = """
#profile-title: ⛔ ixxy vpn

#profile-update-interval: 1

#announce: Срок действия подписки закончился. Продлите у @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла
""".strip()


# =====================
# GITHUB HELPERS
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
        headers=github_headers(),
        timeout=20
    )

    data = {
        "message": "Update ixxy VPN subscription",
        "content": base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8"),
        "branch": BRANCH
    }

    if old.status_code == 200:

        data["sha"] = old.json()["sha"]

    elif old.status_code != 404:

        old.raise_for_status()

    response = requests.put(
        url,
        headers=github_headers(),
        json=data,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


# =====================
# ССЫЛКА ПОЛЬЗОВАТЕЛЯ
# =====================

def get_subscription_link(user_id):

    path = f"users/{user_id}.txt"

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
    )


# =====================
# НОВЫЙ ПОЛЬЗОВАТЕЛЬ
# =====================

def create_user_subscription(user_id):

    path = f"users/{user_id}.txt"

    update_file(
        path,
        NEW_USER_TEMPLATE
    )

    link = get_subscription_link(user_id)

    save_subscription_link(
        user_id,
        link
    )

    return link


# =====================
# АКТИВНАЯ ПОДПИСКА
# =====================

def create_subscription(user_id, days=30):

    expire_date = (
        datetime.now()
        + timedelta(days=days)
    ).strftime("%d.%m.%Y")

    return activate_subscription_file(
        user_id,
        expire_date
    )


def activate_subscription_file(user_id, date):

    path = f"users/{user_id}.txt"

    content = f"""
#profile-title: ☂️ ixxy vip

#profile-update-interval: 1

#announce: ‼️ Подписка активна до {date} ‼️
🆔 Ваш ID: {user_id}

{SERVERS}
""".strip()

    update_file(
        path,
        content
    )

    link = get_subscription_link(user_id)

    save_subscription_link(
        user_id,
        link
    )

    return link


# =====================
# АКТИВАЦИЯ
# =====================

def activate_user_subscription(user_id, days):

    return create_subscription(
        user_id,
        days
    )


# =====================
# ПРОДЛЕНИЕ
# =====================

def update_subscription_file(user_id, date):

    # Если дата пришла из database.py
    # в формате YYYY-MM-DD,
    # превращаем её в DD.MM.YYYY.

    try:

        parsed = datetime.strptime(
            str(date),
            "%Y-%m-%d"
        )

        display_date = parsed.strftime(
            "%d.%m.%Y"
        )

    except:

        display_date = str(date)

    return activate_subscription_file(
        user_id,
        display_date
    )


# =====================
# ПРОСРОЧКА
# =====================

def expire_subscription(user_id):

    path = f"users/{user_id}.txt"

    update_file(
        path,
        EXPIRED_TEMPLATE
    )


# =====================
# ОБНОВИТЬ ВСЕХ АКТИВНЫХ
# =====================

def sync_all_active_users():

    users = get_all_users()

    updated = 0
    skipped = 0

    for user in users:

        try:

            user_id = user[0]
            subscription = user[3]
            subscription_until = user[4]

            # Только активные подписки
            if subscription not in ("vip", "trial"):
                skipped += 1
                continue

            if not subscription_until:
                skipped += 1
                continue

            # Проверяем дату
            try:

                expire_date = datetime.strptime(
                    subscription_until,
                    "%Y-%m-%d"
                )

            except:

                skipped += 1
                continue

            # Если уже истёк — не трогаем
            if expire_date <= datetime.now():
                skipped += 1
                continue

            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )

            activate_subscription_file(
                user_id,
                display_date
            )

            updated += 1

        except Exception as e:

            print(
                f"❌ Ошибка обновления пользователя "
                f"{user_id}: {e}"
            )

    print(
        f"☂️ Синхронизация серверов завершена: "
        f"{updated} обновлено, {skipped} пропущено"
    )

    return updated