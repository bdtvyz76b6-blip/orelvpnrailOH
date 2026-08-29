import os
import requests

from datetime import datetime, timedelta

from database import (
    save_subscription_link,
    save_subscription_content,
    get_all_users,
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()


# ============================================================
# GITHUB
# ============================================================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
).strip()

OWNER = os.getenv(
    "GITHUB_OWNER",
    "bdtvyz76b6-blip",
)

REPO = os.getenv(
    "GITHUB_REPO",
    "vpn-sub",
)

BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
)


# ============================================================
# ФАЙЛЫ С СЕРВЕРАМИ
# ============================================================

SERVERS_FILE = "servers.txt"
NO_SERVERS_FILE = "no_servers.txt"


# ============================================================
# RAW GITHUB URL
# ============================================================

def raw_url(filename):

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{filename}"
    )


# ============================================================
# ЗАГРУЗКА GITHUB ФАЙЛА
# ============================================================

def load_github_file(filename):

    response = requests.get(
        raw_url(filename),
        timeout=20,
    )

    if response.status_code != 200:

        raise Exception(
            f"Не удалось загрузить {filename}: "
            f"HTTP {response.status_code}"
        )

    content = response.text.strip()

    if not content:

        raise Exception(
            f"Файл {filename} пустой"
        )

    return content


# ============================================================
# АКТИВНЫЕ СЕРВЕРА
# ============================================================

def load_servers():

    return load_github_file(
        SERVERS_FILE
    )


# ============================================================
# СЕРВЕРА ДЛЯ ОТКЛЮЧЁННОЙ / ИСТЁКШЕЙ ПОДПИСКИ
# ============================================================

def load_no_servers():

    return load_github_file(
        NO_SERVERS_FILE
    )


# ============================================================
# ПЕРСОНАЛЬНАЯ СТРАНИЦА ПОДПИСКИ
# ============================================================

def get_subscription_link(user_id):

    return (
        f"{PUBLIC_SITE_URL}/s/"
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )


# ============================================================
# ПРЯМАЯ ССЫЛКА ПОДПИСКИ
# ============================================================

def get_subscription_content_url(user_id):

    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )


# ============================================================
# СОХРАНЕНИЕ ПОДПИСКИ
# ============================================================

def save_user_subscription(
    user_id,
    content,
):

    link = get_subscription_link(
        user_id
    )

    save_subscription_content(
        user_id,
        content,
    )

    save_subscription_link(
        user_id,
        link,
    )

    return link


# ============================================================
# НОВЫЙ ПОЛЬЗОВАТЕЛЬ
# ============================================================

NEW_USER_TEMPLATE = """
#profile-title: ☂️ ixxy vpn
#profile-update-interval: 1
#announce: Активируйте подписку через @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку
""".strip()


# ============================================================
# СОЗДАНИЕ ПОДПИСКИ НОВОМУ ПОЛЬЗОВАТЕЛЮ
# ============================================================

def create_user_subscription(user_id):

    link = save_user_subscription(
        user_id,
        NEW_USER_TEMPLATE,
    )

    print(
        f"Создана подписка пользователя {user_id}"
    )

    print(
        f"Страница: {link}"
    )

    print(
        "Subscription URL: "
        f"{get_subscription_content_url(user_id)}"
    )

    return link


# ============================================================
# СОЗДАНИЕ АКТИВНОЙ ПОДПИСКИ
# ============================================================

def create_subscription(
    user_id,
    days=30,
):

    days = int(days)

    if days <= 0:

        raise ValueError(
            "Количество дней должно быть больше 0"
        )

    expire_date = (
        datetime.now().date()
        + timedelta(days=days)
    )

    display_date = expire_date.strftime(
        "%d.%m.%Y"
    )

    return activate_subscription_file(
        user_id,
        display_date,
    )


# ============================================================
# АКТИВНАЯ ПОДПИСКА
# ============================================================

def activate_subscription_file(
    user_id,
    date,
):

    servers = load_servers()

    content = (
        f"#profile-title: ☂️ ixxy vpn\n\n"
        f"#profile-update-interval: 1\n\n"
        f"#announce: ‼️ Подписка активна "
        f"до {date} ‼️ __ 🆔 ID: {user_id}\n\n"
        f"{servers}"
    )

    link = save_user_subscription(
        user_id,
        content,
    )

    print(
        f"Подписка пользователя {user_id} "
        f"обновлена до {date}"
    )

    print(
        f"Страница: {link}"
    )

    print(
        "Subscription URL: "
        f"{get_subscription_content_url(user_id)}"
    )

    return link


# ============================================================
# АКТИВАЦИЯ
# ============================================================

def activate_user_subscription(
    user_id,
    days,
):

    return create_subscription(
        user_id,
        days,
    )


# ============================================================
# ОБНОВЛЕНИЕ ПОСЛЕ ПРОДЛЕНИЯ
# ============================================================

def update_subscription_file(
    user_id,
    date,
):

    try:

        parsed = datetime.strptime(
            str(date),
            "%Y-%m-%d",
        )

        display_date = parsed.strftime(
            "%d.%m.%Y"
        )

    except Exception:

        display_date = str(date)

    return activate_subscription_file(
        user_id,
        display_date,
    )


# ============================================================
# ОТКЛЮЧЕНИЕ / ИСТЕЧЕНИЕ ПОДПИСКИ
# ============================================================

def expire_subscription(user_id):

    # --------------------------------------------------------
    # ВАЖНО:
    # ВСЕГДА берём именно no_servers.txt
    # --------------------------------------------------------

    no_servers = load_no_servers()

    content = (
        f"#profile-title: ⛔ ixxy vpn\n\n"
        f"#profile-update-interval: 1\n\n"
        f"#announce: ‼️ Ваша подписка истекла "
        f"или была отключена администратором. "
        f"Зайдите в @orelvpntopbot\n\n"
        f"{no_servers}"
    )

    link = save_user_subscription(
        user_id,
        content,
    )

    print(
        f"{user_id} — подписка отключена"
    )

    print(
        "Использован файл: "
        f"{NO_SERVERS_FILE}"
    )

    print(
        f"Страница: {link}"
    )

    print(
        "Subscription URL: "
        f"{get_subscription_content_url(user_id)}"
    )

    return link


# ============================================================
# СИНХРОНИЗАЦИЯ
# ============================================================

def sync_all_active_users():

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Начинаю синхронизацию...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

    servers = load_servers()
    no_servers = load_no_servers()
    users = get_all_users()

    updated = 0
    skipped = 0
    expired = 0
    errors = 0

    today = datetime.now().date()

    for user in users:

        user_id = user[0]

        try:

            subscription = user[3]
            subscription_until = user[4]

            # =================================================
            # УЧИТЫВАЕМ ТОЛЬКО АКТИВНЫЕ ТАРИФЫ
            # =================================================

            if subscription not in (
                "vip",
                "trial",
            ):

                # ------------------------------------------------
                # Если подписка не vip/trial — считаем её
                # отключённой и ставим no_servers.
                # ------------------------------------------------

                expire_subscription(
                    user_id
                )

                expired += 1

                print(
                    f"{user_id} — "
                    f"отключён / нет активного тарифа"
                )

                continue

            # =================================================
            # НЕТ ДАТЫ
            # =================================================

            if not subscription_until:

                expire_subscription(
                    user_id
                )

                expired += 1

                print(
                    f"{user_id} — "
                    f"нет даты подписки, установлен no_servers"
                )

                continue

            # =================================================
            # ПРОВЕРКА ДАТЫ
            # =================================================

            try:

                expire_date = datetime.strptime(
                    str(subscription_until),
                    "%Y-%m-%d",
                ).date()

            except Exception:

                print(
                    f"Неверная дата у {user_id}: "
                    f"{subscription_until}"
                )

                expire_subscription(
                    user_id
                )

                expired += 1

                continue

            # =================================================
            # ИСТЕКЛА
            # =================================================

            if expire_date < today:

                content = (
                    f"#profile-title: ⛔ ixxy vpn\n\n"
                    f"#profile-update-interval: 1\n\n"
                    f"#announce: ‼️ Ваша подписка истекла "
                    f"или была отключена администратором. "
                    f"Зайдите в @orelvpntopbot\n\n"
                    f"{no_servers}"
                )

                save_user_subscription(
                    user_id,
                    content,
                )

                expired += 1

                print(
                    f"{user_id} — подписка истекла"
                )

                print(
                    f"{user_id} — "
                    f"использован {NO_SERVERS_FILE}"
                )

                continue

            # =================================================
            # АКТИВЕН
            # =================================================

            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )

            content = (
                f"#profile-title: ☂️ ixxy vpn\n\n"
                f"#profile-update-interval: 1\n\n"
                f"#announce: ‼️ Подписка активна "
                f"до {display_date} ‼️ __ 🆔 ID: {user_id}\n\n"
                f"{servers}"
            )

            save_user_subscription(
                user_id,
                content,
            )

            updated += 1

            print(
                f"{user_id} — "
                f"обновлён до {display_date}"
            )

        except Exception as e:

            errors += 1

            print(
                f"Ошибка пользователя "
                f"{user_id}: {e}"
            )

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Синхронизация завершена")
    print(f"Обновлено: {updated}")
    print(f"Истекло/отключено: {expired}")
    print(f"Пропущено: {skipped}")
    print(f"Ошибок: {errors}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return {
        "updated": updated,
        "skipped": skipped,
        "expired": expired,
        "errors": errors,
    }


# ============================================================
# ОБНОВЛЕНИЕ СЕРВЕРОВ ИЗ АДМИНКИ
# ============================================================

def sync_servers_update():

    print(
        "Запущено обновление серверов "
        "из админ-панели"
    )

    return sync_all_active_users()