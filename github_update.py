import os
import base64
import requests

from datetime import datetime, timedelta

from database import (
    save_subscription_link,
    get_all_users
)


# ============================================================
# GITHUB
# ============================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

OWNER = "bdtvyz76b6-blip"
REPO = "vpn-sub"
BRANCH = "main"


# ============================================================
# ФАЙЛЫ
# ============================================================

SERVERS_FILE = "servers.txt"
NO_SERVERS_FILE = "no_servers.txt"


# ============================================================
# ПРОВЕРКА GITHUB TOKEN
# ============================================================

def check_github_token():

    if not GITHUB_TOKEN:

        raise Exception(
            "❌ GITHUB_TOKEN не найден в Railway Variables"
        )

    return GITHUB_TOKEN


# ============================================================
# RAW GITHUB
# ============================================================

def raw_url(filename):

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{filename}"
    )


# ============================================================
# ЗАГРУЗКА ФАЙЛА
# ============================================================

def load_github_file(filename):

    check_github_token()

    response = requests.get(
        raw_url(filename),
        timeout=20
    )

    if response.status_code != 200:

        raise Exception(
            f"❌ Не удалось загрузить "
            f"{filename}: "
            f"HTTP {response.status_code}"
        )

    content = response.text.strip()

    if not content:

        raise Exception(
            f"❌ Файл {filename} пустой"
        )

    return content


# ============================================================
# АКТИВНЫЕ СЕРВЕРЫ
# ============================================================

def load_servers():

    return load_github_file(
        SERVERS_FILE
    )


# ============================================================
# СЕРВЕРЫ ДЛЯ ПРОСРОЧЕННЫХ
# ============================================================

def load_no_servers():

    return load_github_file(
        NO_SERVERS_FILE
    )


# ============================================================
# GITHUB HEADERS
# ============================================================

def github_headers():

    check_github_token()

    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }


# ============================================================
# GITHUB API URL
# ============================================================

def github_url(path):

    return (
        f"https://api.github.com/repos/"
        f"{OWNER}/{REPO}/contents/{path}"
    )


# ============================================================
# ШАБЛОН НОВОГО ПОЛЬЗОВАТЕЛЯ
# ============================================================

NEW_USER_TEMPLATE = """
#profile-title: ☂️ ixxy vpn

#profile-update-interval: 1

#announce: Активируйте подписку через @orelvpntopbot

vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку
""".strip()


# ============================================================
# ОБНОВЛЕНИЕ ФАЙЛА GITHUB
# ============================================================

def update_file(path, content):

    url = github_url(path)

    headers = github_headers()

    # --------------------------------------------------------
    # Получаем текущий файл
    # --------------------------------------------------------

    old = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    data = {
        "message": "Update ixxy VPN subscription",
        "content": base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8"),
        "branch": BRANCH
    }

    # --------------------------------------------------------
    # Файл существует
    # --------------------------------------------------------

    if old.status_code == 200:

        old_data = old.json()

        sha = old_data.get("sha")

        if sha:

            data["sha"] = sha

    # --------------------------------------------------------
    # Файл отсутствует
    # --------------------------------------------------------

    elif old.status_code == 404:

        pass

    # --------------------------------------------------------
    # Другая ошибка
    # --------------------------------------------------------

    else:

        print(
            "❌ GitHub GET error:",
            old.status_code,
            old.text
        )

        old.raise_for_status()

    # --------------------------------------------------------
    # Записываем файл
    # --------------------------------------------------------

    response = requests.put(
        url,
        headers=headers,
        json=data,
        timeout=20
    )

    if response.status_code not in (200, 201):

        print(
            "❌ GitHub PUT error:",
            response.status_code
        )

        print(
            response.text
        )

    response.raise_for_status()

    return response.json()


# ============================================================
# ССЫЛКА ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_subscription_link(user_id):

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/"
        f"users/{user_id}.txt"
    )


# ============================================================
# СОЗДАНИЕ ФАЙЛА НОВОГО ПОЛЬЗОВАТЕЛЯ
# ============================================================

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

    print(
        f"✅ Создан файл пользователя {user_id}"
    )

    return link


# ============================================================
# СОЗДАНИЕ АКТИВНОЙ ПОДПИСКИ
# ============================================================

def create_subscription(
    user_id,
    days=30
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
        display_date
    )


# ============================================================
# АКТИВНАЯ ПОДПИСКА
# ============================================================

def activate_subscription_file(
    user_id,
    date
):

    servers = load_servers()

    path = f"users/{user_id}.txt"

    content = (
        f"#profile-title: ☂️ ixxy vip\n\n"
        f"#profile-update-interval: 1\n\n"
        f"#announce: ‼️ Подписка активна "
        f"до {date} ‼️ __ 🆔 ID: {user_id}\n\n"
        f"{servers}"
    )

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

    print(
        f"✅ Подписка пользователя "
        f"{user_id} обновлена до {date}"
    )

    return link


# ============================================================
# АКТИВАЦИЯ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def activate_user_subscription(
    user_id,
    days
):

    return create_subscription(
        user_id,
        days
    )


# ============================================================
# ОБНОВЛЕНИЕ ПОСЛЕ ПРОДЛЕНИЯ
# ============================================================

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


# ============================================================
# ПРОСРОЧЕННАЯ ПОДПИСКА
# ============================================================

def expire_subscription(user_id):

    no_servers = load_no_servers()

    path = f"users/{user_id}.txt"

    content = (
        f"#profile-title: ⛔ ixxy vpn\n\n"
        f"#profile-update-interval: 1\n\n"
        f"#announce: ⛔ Подписка истекла. "
        f"Продлите подписку в @orelvpntopbot\n"
        f"🆔 Ваш ID: {user_id}\n\n"
        f"{no_servers}"
    )

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

    print(
        f"⛔ {user_id} — подписка истекла"
    )

    return link


# ============================================================
# СИНХРОНИЗАЦИЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

def sync_all_active_users():

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "🔄 Начинаю синхронизацию..."
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    # --------------------------------------------------------
    # Загружаем серверы один раз
    # --------------------------------------------------------

    servers = load_servers()

    # --------------------------------------------------------
    # Загружаем заглушки один раз
    # --------------------------------------------------------

    no_servers = load_no_servers()

    # --------------------------------------------------------
    # Получаем пользователей
    # --------------------------------------------------------

    users = get_all_users()

    updated = 0
    skipped = 0
    expired = 0
    errors = 0

    today = datetime.now().date()

    # ========================================================
    # ОБХОД
    # ========================================================

    for user in users:

        user_id = user[0]

        try:

            subscription = user[3]

            subscription_until = user[4]

            # ------------------------------------------------
            # Только VIP / trial
            # ------------------------------------------------

            if subscription not in (
                "vip",
                "trial"
            ):

                skipped += 1
                continue

            # ------------------------------------------------
            # Нет даты
            # ------------------------------------------------

            if not subscription_until:

                skipped += 1
                continue

            # ------------------------------------------------
            # Дата
            # ------------------------------------------------

            try:

                expire_date = datetime.strptime(
                    str(subscription_until),
                    "%Y-%m-%d"
                ).date()

            except Exception:

                print(
                    f"⚠️ Неверная дата "
                    f"у {user_id}: "
                    f"{subscription_until}"
                )

                skipped += 1
                continue

            path = f"users/{user_id}.txt"

            # =================================================
            # ПРОСРОЧЕН
            # =================================================

            if expire_date < today:

                content = (
                    f"#profile-title: ⛔ ixxy vpn\n\n"
                    f"#profile-update-interval: 1\n\n"
                    f"#announce: ⛔ Подписка истекла. "
                    f"Продлите подписку в "
                    f"@orelvpntopbot\n"
                    f"🆔 Ваш ID: {user_id}\n\n"
                    f"{no_servers}"
                )

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

                expired += 1

                print(
                    f"⛔ {user_id} — "
                    f"переведён на no_servers"
                )

                continue

            # =================================================
            # АКТИВЕН
            # =================================================

            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )

            content = (
                f"#profile-title: ☂️ ixxy vip\n\n"
                f"#profile-update-interval: 1\n\n"
                f"#announce: ‼️ Подписка активна "
                f"до {display_date} ‼️ __ 🆔 ID: {user_id}\n\n"
                f"{servers}"
            )

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

            updated += 1

            print(
                f"✅ {user_id} — "
                f"обновлён до {display_date}"
            )

        except Exception as e:

            errors += 1

            print(
                f"❌ Ошибка пользователя "
                f"{user_id}: {e}"
            )

    # ========================================================
    # ИТОГ
    # ========================================================

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "☂️ Синхронизация завершена"
    )

    print(
        f"✅ Обновлено: {updated}"
    )

    print(
        f"⛔ Истекло: {expired}"
    )

    print(
        f"⏭ Пропущено: {skipped}"
    )

    print(
        f"❌ Ошибок: {errors}"
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    return {
        "updated": updated,
        "skipped": skipped,
        "expired": expired,
        "errors": errors
    }


# ============================================================
# ОБНОВЛЕНИЕ ПО КНОПКЕ АДМИНА
# ============================================================

def sync_servers_update():

    print(
        "🔄 Запущено обновление серверов "
        "из админ-панели"
    )

    return sync_all_active_users()