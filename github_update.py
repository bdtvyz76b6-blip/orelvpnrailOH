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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise Exception("❌ GITHUB_TOKEN не найден")


OWNER = "bdtvyz76b6-blip"
REPO = "vpn-sub"
BRANCH = "main"


# ============================================================
# ФАЙЛЫ
# ============================================================

SERVERS_FILE = "servers.txt"
NO_SERVERS_FILE = "no_servers.txt"


# ============================================================
# ЗАГРУЗКА ФАЙЛА С GITHUB
# ============================================================

def load_github_raw_file(filename):

    url = (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{filename}"
    )

    response = requests.get(
        url,
        timeout=20
    )

    response.raise_for_status()

    content = response.text.strip()

    if not content:
        raise Exception(
            f"❌ {filename} пустой"
        )

    return content


# ============================================================
# АКТИВНЫЕ СЕРВЕРЫ
# ============================================================

def load_servers():

    return load_github_raw_file(
        SERVERS_FILE
    )


# ============================================================
# СЕРВЕРЫ ДЛЯ ПРОСРОЧЕННЫХ
# ============================================================

def load_no_servers():

    return load_github_raw_file(
        NO_SERVERS_FILE
    )


# ============================================================
# GITHUB HEADERS
# ============================================================

def github_headers():

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
# ОБНОВЛЕНИЕ ФАЙЛА НА GITHUB
# ============================================================

def update_file(
    path,
    content
):

    url = github_url(path)

    # --------------------------------------------------------
    # Получаем существующий файл
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Файл существует
    # --------------------------------------------------------

    if old.status_code == 200:

        old_data = old.json()

        sha = old_data.get("sha")

        if sha:
            data["sha"] = sha

    # --------------------------------------------------------
    # Файла нет
    # --------------------------------------------------------

    elif old.status_code == 404:

        pass

    # --------------------------------------------------------
    # Другая ошибка
    # --------------------------------------------------------

    else:

        print(
            f"❌ GitHub GET ERROR {path}: "
            f"{old.status_code}"
        )

        print(
            old.text
        )

        old.raise_for_status()

    # --------------------------------------------------------
    # PUT
    # --------------------------------------------------------

    response = requests.put(
        url,
        headers=github_headers(),
        json=data,
        timeout=20
    )

    if response.status_code not in (
        200,
        201
    ):

        print(
            f"❌ GitHub PUT ERROR {path}: "
            f"{response.status_code}"
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

    path = f"users/{user_id}.txt"

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/{path}"
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

    if days < 1:

        raise ValueError(
            "Количество дней должно быть больше 0"
        )

    # --------------------------------------------------------
    # Дата окончания
    # --------------------------------------------------------

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


# ============================================================
# СОЗДАНИЕ АКТИВНОГО ФАЙЛА
# ============================================================

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

    print(
        f"✅ Активная подписка создана "
        f"для {user_id} до {date}"
    )

    return link


# ============================================================
# АКТИВАЦИЯ ПОДПИСКИ
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
# ИСТЕЧЕНИЕ ПОДПИСКИ
# ============================================================

def expire_subscription(
    user_id
):

    path = f"users/{user_id}.txt"

    # --------------------------------------------------------
    # Загружаем no_servers.txt
    # --------------------------------------------------------

    no_servers = load_no_servers()

    # --------------------------------------------------------
    # Создаём файл пользователя
    # --------------------------------------------------------

    content = f"""
#profile-title: ⛔ ixxy vpn

#profile-update-interval: 1

#announce: ⛔ Подписка истекла. Продлите подписку в @orelvpntopbot

🆔 Ваш ID: {user_id}

{no_servers}
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

    print(
        f"⛔ {user_id} переведён "
        f"на no_servers.txt"
    )

    return link


# ============================================================
# ОБНОВЛЕНИЕ ОДНОГО ПОЛЬЗОВАТЕЛЯ
# ============================================================

def sync_user(
    user_id,
    subscription,
    subscription_until,
    servers,
    no_servers,
    today
):

    # --------------------------------------------------------
    # Нет подписки
    # --------------------------------------------------------

    if subscription not in (
        "vip",
        "trial"
    ):

        return "skipped"

    # --------------------------------------------------------
    # Нет даты
    # --------------------------------------------------------

    if not subscription_until:

        return "skipped"

    # --------------------------------------------------------
    # Парсим дату
    # --------------------------------------------------------

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

        return "skipped"

    path = f"users/{user_id}.txt"

    # ========================================================
    # ПРОСРОЧЕН
    # ========================================================

    if expire_date < today:

        content = f"""
#profile-title: ⛔ ixxy vpn

#profile-update-interval: 1

#announce: ⛔ Подписка истекла. Продлите подписку в @orelvpntopbot

🆔 Ваш ID: {user_id}

{no_servers}
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

        print(
            f"⛔ {user_id} — подписка истекла"
        )

        return "expired"

    # ========================================================
    # АКТИВЕН
    # ========================================================

    display_date = expire_date.strftime(
        "%d.%m.%Y"
    )

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

    link = get_subscription_link(
        user_id
    )

    save_subscription_link(
        user_id,
        link
    )

    print(
        f"✅ {user_id} обновлён "
        f"до {display_date}"
    )

    return "updated"


# ============================================================
# ОБНОВИТЬ ВСЕХ АКТИВНЫХ И ПРОСРОЧЕННЫХ
# ============================================================

def sync_all_active_users():

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "🔄 Начинаю полную синхронизацию..."
    )

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    # --------------------------------------------------------
    # Загружаем оба файла ОДИН раз
    # --------------------------------------------------------

    servers = load_servers()

    no_servers = load_no_servers()

    # --------------------------------------------------------
    # Пользователи
    # --------------------------------------------------------

    users = get_all_users()

    updated = 0
    skipped = 0
    expired = 0
    errors = 0

    today = datetime.now().date()

    # ========================================================
    # ОБХОД ПОЛЬЗОВАТЕЛЕЙ
    # ========================================================

    for user in users:

        user_id = user[0]

        try:

            # ------------------------------------------------
            # Структура users
            # ------------------------------------------------

            subscription = user[3]

            subscription_until = user[4]

            # ------------------------------------------------
            # Синхронизация
            # ------------------------------------------------

            result = sync_user(
                user_id,
                subscription,
                subscription_until,
                servers,
                no_servers,
                today
            )

            # ------------------------------------------------
            # Результат
            # ------------------------------------------------

            if result == "updated":

                updated += 1

            elif result == "expired":

                expired += 1

            else:

                skipped += 1

        except Exception as e:

            errors += 1

            print(
                f"❌ Ошибка пользователя "
                f"{user_id}: {e}"
            )

    # ========================================================
    # РЕЗУЛЬТАТ
    # ========================================================

    print(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print(
        "☂️ Синхронизация завершена"
    )

    print(
        f"✅ Активных обновлено: {updated}"
    )

    print(
        f"⛔ Истёкших обновлено: {expired}"
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
# СИНХРОНИЗАЦИЯ ПО КНОПКЕ АДМИНА
# ============================================================

def sync_servers_update():

    print(
        "🔄 Администратор запустил "
        "обновление серверов..."
    )

    return sync_all_active_users()