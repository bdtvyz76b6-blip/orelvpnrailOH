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
# ФАЙЛ С СЕРВЕРАМИ
# =====================

SERVERS_FILE = "servers.txt"


# =====================
# ЗАГРУЗКА СЕРВЕРОВ
# =====================

def load_servers():

    url = (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{SERVERS_FILE}"
    )

    response = requests.get(
        url,
        timeout=20
    )

    response.raise_for_status()

    servers = response.text.strip()

    if not servers:

        raise Exception(
            "❌ servers.txt пустой"
        )

    return servers


# =====================
# GITHUB HEADERS
# =====================

def github_headers():

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }


# =====================
# GITHUB URL
# =====================

def github_url(path):

    return (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/{path}"
    )


# =====================
# ШАБЛОН НОВОГО ПОЛЬЗОВАТЕЛЯ
# =====================

NEW_USER_TEMPLATE = """
#profile-title: ☂️ ixxy vpn

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку
""".strip()


# =====================
# ШАБЛОН ПРОСРОЧКИ
# =====================

EXPIRED_TEMPLATE = """
#profile-title: ⛔ ixxy vpn

#profile-update-interval: 1

#announce: Срок действия подписки закончился. Продлите у @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Подписка истекла
""".strip()


# =====================
# ОБНОВЛЕНИЕ ФАЙЛА GITHUB
# =====================

def update_file(
    path,
    content
):

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

    # =====================
    # ФАЙЛ СУЩЕСТВУЕТ
    # =====================

    if old.status_code == 200:

        data["sha"] = old.json()["sha"]

    # =====================
    # ФАЙЛ НЕ СУЩЕСТВУЕТ
    # =====================

    elif old.status_code == 404:

        pass

    # =====================
    # ОШИБКА
    # =====================

    else:

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
# СОЗДАНИЕ ФАЙЛА НОВОГО
# ПОЛЬЗОВАТЕЛЯ
# =====================

def create_user_subscription(user_id):

    path = f"users/{user_id}.txt"

    update_file(
        path,
        NEW_USER_TEMPLATE
    )

    link = get_subscription_link(
        user_id
    )

    save_subscription_link(
        user_id,
        link
    )

    return link


# =====================
# СОЗДАНИЕ АКТИВНОЙ
# ПОДПИСКИ
# =====================

def create_subscription(
    user_id,
    days=30
):

    days = int(days)

    if days < 1:
        raise ValueError(
            "Количество дней должно быть больше 0"
        )

    # =====================
    # Считаем дату
    # =====================

    expire_date = (
        datetime.now().date()
        +
        timedelta(days=days)
    )

    display_date = expire_date.strftime(
        "%d.%m.%Y"
    )

    return activate_subscription_file(
        user_id,
        display_date
    )


# =====================
# ОБНОВЛЕНИЕ АКТИВНОГО
# ФАЙЛА
# =====================

def activate_subscription_file(
    user_id,
    date
):

    servers = load_servers()

    path = f"users/{user_id}.txt"

    content = f"""
#profile-title: ☂️ ixxy vip

#profile-update-interval: 1

#announce: ‼️ Подписка активна до {date} ‼️
🆔 Ваш ID: {user_id}

{servers}
""".strip()

    update_file(
        path,
        content
    )

    link = get_subscription_link(
        user_id
    )

    save_subscription_link(
        user_id,
        link
    )

    return link


# =====================
# АКТИВАЦИЯ ПОДПИСКИ
# =====================

def activate_user_subscription(
    user_id,
    days
):

    return create_subscription(
        user_id,
        days
    )


# =====================
# ОБНОВЛЕНИЕ ПОСЛЕ
# ПРОДЛЕНИЯ
# =====================

def update_subscription_file(
    user_id,
    date
):

    try:

        parsed = datetime.strptime(
            str(date),
            "%Y-%m-%d"
        )

        display_date = parsed.strftime(
            "%d.%m.%Y"
        )

    except Exception:

        display_date = str(date)

    return activate_subscription_file(
        user_id,
        display_date
    )


# =====================
# ИСТЕЧЕНИЕ ПОДПИСКИ
# =====================

def expire_subscription(
    user_id
):

    path = f"users/{user_id}.txt"

    update_file(
        path,
        EXPIRED_TEMPLATE
    )


# =====================
# ОБНОВИТЬ ВСЕХ АКТИВНЫХ
# ПОЛЬЗОВАТЕЛЕЙ
# =====================

def sync_all_active_users():

    print(
        "🔄 Начинаю синхронизацию серверов..."
    )

    # Загружаем servers.txt один раз.
    # Не нужно скачивать его отдельно
    # для каждого пользователя.

    servers = load_servers()

    users = get_all_users()

    updated = 0
    skipped = 0
    expired = 0
    errors = 0

    today = datetime.now().date()

    for user in users:

        try:

            # =====================
            # СТРУКТУРА USERS
            # =====================

            user_id = user[0]
            subscription = user[3]
            subscription_until = user[4]

            # =====================
            # ТОЛЬКО VIP/TRIAL
            # =====================

            if subscription not in (
                "vip",
                "trial"
            ):

                skipped += 1
                continue

            # =====================
            # НЕТ ДАТЫ
            # =====================

            if not subscription_until:

                skipped += 1
                continue

            # =====================
            # ПАРСИМ ДАТУ
            # =====================

            try:

                expire_date = datetime.strptime(
                    str(subscription_until),
                    "%Y-%m-%d"
                ).date()

            except Exception:

                print(
                    f"⚠️ Неверная дата у {user_id}: "
                    f"{subscription_until}"
                )

                skipped += 1
                continue

            # =====================
            # ПРОСРОЧЕН
            # =====================

            if expire_date < today:

                try:

                    expire_subscription(
                        user_id
                    )

                    expired += 1

                    print(
                        f"⛔ {user_id} — подписка истекла"
                    )

                except Exception as e:

                    errors += 1

                    print(
                        f"❌ Ошибка отключения "
                        f"{user_id}: {e}"
                    )

                continue

            # =====================
            # ФОРМАТ ДАТЫ
            # =====================

            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )

            # =====================
            # СОЗДАЁМ ФАЙЛ
            # =====================

            path = f"users/{user_id}.txt"

            content = f"""
#profile-title: ☂️ ixxy vip

#profile-update-interval: 1

#announce: ‼️ Подписка активна до {display_date} ‼️
🆔 Ваш ID: {user_id}

{servers}
""".strip()

            update_file(
                path,
                content
            )

            # =====================
            # СОХРАНЯЕМ ССЫЛКУ
            # =====================

            link = get_subscription_link(
                user_id
            )

            save_subscription_link(
                user_id,
                link
            )

            updated += 1

            print(
                f"✅ {user_id} обновлён "
                f"до {display_date}"
            )

        except Exception as e:

            errors += 1

            print(
                f"❌ Ошибка пользователя "
                f"{user_id}: {e}"
            )

    # =====================
    # РЕЗУЛЬТАТ
    # =====================

    print(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "☂️ Синхронизация завершена"
    )

    print(
        f"✅ Обновлено: {updated}"
    )

    print(
        f"⏭ Пропущено: {skipped}"
    )

    print(
        f"⛔ Просрочено: {expired}"
    )

    print(
        f"❌ Ошибок: {errors}"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━"
    )

    return {
        "updated": updated,
        "skipped": skipped,
        "expired": expired,
        "errors": errors
    }


# =====================
# СИНХРОНИЗАЦИЯ ПОСЛЕ
# ИЗМЕНЕНИЯ SERVERS.TXT
# =====================

def sync_servers_update():

    print(
        "🔄 Обновление серверов для "
        "всех активных подписок..."
    )

    return sync_all_active_users()