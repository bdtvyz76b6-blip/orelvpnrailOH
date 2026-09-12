import os
import time
import threading
import base64
import requests

from datetime import datetime, timedelta

from dotenv import load_dotenv

from database import (
    save_subscription_link,
    save_subscription_content,
    get_all_users,
)


load_dotenv()


# ============================================================
# НАСТРОЙКИ
# ============================================================

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()

PROFILE_TITLE = os.getenv(
    "PROFILE_TITLE",
    "𝗦𝗨𝗕 - 𝗜𝗫𝗫𝗬 ☂️",
).strip()

try:
    PROFILE_UPDATE_INTERVAL = int(
        os.getenv("PROFILE_UPDATE_INTERVAL", "1")
    )
except Exception:
    PROFILE_UPDATE_INTERVAL = 1


# ============================================================
# HAPP — ТРАФИК
# ============================================================

try:
    TRAFFIC_TOTAL = int(
        os.getenv("TRAFFIC_TOTAL", "0")
    )
except Exception:
    TRAFFIC_TOTAL = 0

try:
    TRAFFIC_UPLOAD = int(
        os.getenv("TRAFFIC_UPLOAD", "0")
    )
except Exception:
    TRAFFIC_UPLOAD = 0

try:
    TRAFFIC_DOWNLOAD = int(
        os.getenv("TRAFFIC_DOWNLOAD", "0")
    )
except Exception:
    TRAFFIC_DOWNLOAD = 0


# ============================================================
# HAPP — СКРЫТИЕ НАСТРОЕК
# ============================================================

HIDE_SETTINGS = os.getenv(
    "HIDE_SETTINGS",
    "1",
).strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)


# ============================================================
# АВТОСИНХРОНИЗАЦИЯ
# ============================================================

AUTO_SYNC_ENABLED = os.getenv(
    "AUTO_SYNC_ENABLED",
    "1",
).strip() == "1"

try:
    AUTO_SYNC_INTERVAL = int(
        os.getenv("AUTO_SYNC_INTERVAL", "600")
    )
except Exception:
    AUTO_SYNC_INTERVAL = 600


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
).strip()

REPO = os.getenv(
    "GITHUB_REPO",
    "vpn-sub",
).strip()

BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
).strip()


SERVERS_FILE = os.getenv(
    "SERVERS_FILE",
    "servers.txt",
).strip()

NO_SERVERS_FILE = os.getenv(
    "NO_SERVERS_FILE",
    "no_servers.txt",
).strip()


# ============================================================
# GITHUB API
# ============================================================

GITHUB_API = (
    f"https://api.github.com/repos/"
    f"{OWNER}/{REPO}/contents"
)


def github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ixxy-vpn-bot",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = (
            f"Bearer {GITHUB_TOKEN}"
        )

    return headers


# ============================================================
# RAW URL
# ============================================================

def get_subscription_link(user_id):
    """
    Постоянная RAW-ссылка пользователя.
    """

    return (
        f"https://raw.githubusercontent.com/"
        f"{OWNER}/{REPO}/{BRANCH}/"
        f"users/{user_id}.txt"
    )


# ============================================================
# GITHUB RAW
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
        headers=github_headers(),
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


def load_servers():
    return load_github_file(
        SERVERS_FILE
    )


def load_no_servers():
    return load_github_file(
        NO_SERVERS_FILE
    )


# ============================================================
# ЗАПИСЬ ПЕРСОНАЛЬНОГО ФАЙЛА В GITHUB
# ============================================================

def upload_user_file(user_id, content):

    path = f"users/{user_id}.txt"

    url = f"{GITHUB_API}/{path}"

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("ascii")

    # --------------------------------------------------------
    # Получаем SHA старого файла, если он существует
    # --------------------------------------------------------

    sha = None

    response = requests.get(
        url,
        headers=github_headers(),
        params={
            "ref": BRANCH,
        },
        timeout=20,
    )

    if response.status_code == 200:

        data = response.json()

        sha = data.get("sha")

    elif response.status_code != 404:

        raise Exception(
            f"Ошибка проверки GitHub файла "
            f"{path}: HTTP {response.status_code}"
        )

    # --------------------------------------------------------
    # Создаём / обновляем
    # --------------------------------------------------------

    payload = {
        "message": (
            f"☂️ ixxy: update user {user_id}"
        ),
        "content": encoded_content,
        "branch": BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        url,
        headers=github_headers(),
        json=payload,
        timeout=30,
    )

    if response.status_code not in (
        200,
        201,
    ):

        raise Exception(
            f"GitHub не смог сохранить "
            f"{path}: "
            f"HTTP {response.status_code} "
            f"{response.text[:500]}"
        )

    return get_subscription_link(
        user_id
    )


# ============================================================
# DATE → UNIX
# ============================================================

def date_to_timestamp(date):

    if isinstance(date, datetime):
        return int(date.timestamp())

    value = str(date).strip()

    for fmt in (
        "%Y-%m-%d",
        "%d.%m.%Y",
    ):

        try:

            parsed = datetime.strptime(
                value,
                fmt,
            )

            return int(
                datetime.combine(
                    parsed.date(),
                    datetime.min.time(),
                ).timestamp()
            )

        except Exception:
            pass

    return 0


# ============================================================
# PROFILE HEADER
# ============================================================

def build_profile_header(
    announce,
    expire=0,
    upload=TRAFFIC_UPLOAD,
    download=TRAFFIC_DOWNLOAD,
    total=TRAFFIC_TOTAL,
):

    hide_settings = (
        "true"
        if HIDE_SETTINGS
        else "false"
    )

    return (
        f"#profile-title: {PROFILE_TITLE}\n"
        f"#profile-update-interval: "
        f"{PROFILE_UPDATE_INTERVAL}\n"
        f"#subscription-userinfo: "
        f"upload={int(upload)}; "
        f"download={int(download)}; "
        f"total={int(total)}; "
        f"expire={int(expire)}\n"
        f"#hide-settings: {hide_settings}\n"
        f"#happ-hide-settings: {hide_settings}\n"
        f"#hide_server_settings: {hide_settings}\n"
        f"#hidesettings: {hide_settings}\n"
        f"#announce: {announce}\n\n"
    )


# ============================================================
# СОХРАНЕНИЕ
# ============================================================

def save_user_subscription(
    user_id,
    content,
):

    link = upload_user_file(
        user_id,
        content,
    )

    # Оставляем сохранение в БД,
    # чтобы существующий код не ломался.

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

_NEW_USER_ANNOUNCE = (
    "🔒 Подписка не активна • "
    "Оформите подписку через @orelvpntopbot"
)


NEW_USER_TEMPLATE = (
    build_profile_header(
        _NEW_USER_ANNOUNCE,
        expire=0,
        upload=0,
        download=0,
        total=0,
    )
    +
    "vless://00000000-0000-0000-0000-000000000000"
    "@expired.invalid:443"
    "?type=tcp"
    "&security=reality"
    "&sni=expired.invalid"
    "&fp=chrome"
    "&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "&sid="
    "&flow=xtls-rprx-vision"
    "#⛔ Активируйте подписку"
).strip()


def create_user_subscription(user_id):

    link = save_user_subscription(
        user_id,
        NEW_USER_TEMPLATE,
    )

    print(
        f"🆕 Создан файл "
        f"users/{user_id}.txt"
    )

    print(
        f"🔗 RAW: {link}"
    )

    return link


# ============================================================
# ФОРМАТ ДАТЫ
# ============================================================

def format_subscription_date(date):

    if isinstance(date, datetime):
        return date.strftime("%d.%m.%Y")

    if hasattr(date, "strftime"):

        try:
            return date.strftime("%d.%m.%Y")
        except Exception:
            pass

    value = str(date).strip()

    for fmt in (
        "%Y-%m-%d",
        "%d.%m.%Y",
    ):

        try:

            parsed = datetime.strptime(
                value,
                fmt,
            )

            return parsed.strftime(
                "%d.%m.%Y"
            )

        except Exception:
            pass

    return value


# ============================================================
# АКТИВНАЯ ПОДПИСКА
# ============================================================

def activate_subscription_file(
    user_id,
    date,
):

    servers = load_servers()

    display_date = format_subscription_date(
        date
    )

    expire_timestamp = date_to_timestamp(
        display_date
    )

    announce = (
        f"🟢 Подписка активна • "
        f"до {display_date} • "
        f"🆔 ID: {user_id}"
    )

    content = (
        build_profile_header(
            announce,
            expire=expire_timestamp,
            upload=0,
            download=0,
            total=0,
        )
        + servers
    )

    link = save_user_subscription(
        user_id,
        content,
    )

    print(
        f"🟢 {user_id} — "
        f"подписка до {display_date}"
    )

    print(
        f"🔗 RAW: {link}"
    )

    return link


# ============================================================
# СОЗДАНИЕ ПОДПИСКИ
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

    return activate_subscription_file(
        user_id,
        expire_date.strftime("%d.%m.%Y"),
    )


def activate_user_subscription(
    user_id,
    days,
):

    return create_subscription(
        user_id,
        days,
    )


def update_subscription_file(
    user_id,
    date,
):

    return activate_subscription_file(
        user_id,
        date,
    )


# ============================================================
# ИСТЁКШАЯ ПОДПИСКА
# ============================================================

def expire_subscription(user_id):

    no_servers = load_no_servers()

    announce = (
        "🔴 Подписка истекла • "
        "Продлите подписку через @orelvpntopbot"
    )

    content = (
        build_profile_header(
            announce,
            expire=0,
            upload=0,
            download=0,
            total=0,
        )
        + no_servers
    )

    link = save_user_subscription(
        user_id,
        content,
    )

    print(
        f"🔴 {user_id} — подписка отключена"
    )

    print(
        f"🔗 RAW: {link}"
    )

    return link


# ============================================================
# АКТИВНЫЕ ТАРИФЫ
# ============================================================

ACTIVE_SUBSCRIPTIONS = {
    "vip",
    "trial",

    # Старые названия
    "👑 Орёл VPN",
    "🎁 Пробный период",
}


# ============================================================
# СИНХРОНИЗАЦИЯ
# ============================================================

def sync_all_active_users():

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔄 Начинаю синхронизацию...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:

        servers = load_servers()
        no_servers = load_no_servers()
        users = get_all_users()

    except Exception as e:

        print(
            f"❌ Не удалось загрузить данные: {e}"
        )

        return {
            "updated": 0,
            "skipped": 0,
            "expired": 0,
            "errors": 1,
        }

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

            # ------------------------------------------------
            # НЕАКТИВНА
            # ------------------------------------------------

            if subscription not in ACTIVE_SUBSCRIPTIONS:

                announce = (
                    "🔴 Подписка не активна • "
                    "Оформите подписку через @orelvpntopbot"
                )

                content = (
                    build_profile_header(
                        announce,
                        expire=0,
                        upload=0,
                        download=0,
                        total=0,
                    )
                    + no_servers
                )

                save_user_subscription(
                    user_id,
                    content,
                )

                skipped += 1

                print(
                    f"{user_id} — ⚪ "
                    f"нет активной подписки"
                )

                continue

            # ------------------------------------------------
            # НЕТ ДАТЫ
            # ------------------------------------------------

            if not subscription_until:

                announce = (
                    "🔴 Подписка не активна • "
                    "Оформите подписку через @orelvpntopbot"
                )

                content = (
                    build_profile_header(
                        announce,
                        expire=0,
                        upload=0,
                        download=0,
                        total=0,
                    )
                    + no_servers
                )

                save_user_subscription(
                    user_id,
                    content,
                )

                expired += 1

                continue

            # ------------------------------------------------
            # ДАТА
            # ------------------------------------------------

            try:

                expire_date = datetime.strptime(
                    str(subscription_until),
                    "%Y-%m-%d",
                ).date()

            except Exception:

                print(
                    f"❌ Неверная дата "
                    f"{user_id}: "
                    f"{subscription_until}"
                )

                errors += 1

                continue

            # ------------------------------------------------
            # ИСТЕКЛА
            # ------------------------------------------------

            if expire_date < today:

                announce = (
                    "🔴 Подписка истекла • "
                    "Продлите подписку через @orelvpntopbot"
                )

                content = (
                    build_profile_header(
                        announce,
                        expire=0,
                        upload=0,
                        download=0,
                        total=0,
                    )
                    + no_servers
                )

                save_user_subscription(
                    user_id,
                    content,
                )

                expired += 1

                print(
                    f"{user_id} — 🔴 истекла"
                )

                continue

            # ------------------------------------------------
            # АКТИВНА
            # ------------------------------------------------

            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )

            expire_timestamp = int(
                datetime.combine(
                    expire_date,
                    datetime.min.time(),
                ).timestamp()
            )

            announce = (
                f"🟢 Подписка активна • "
                f"до {display_date} • "
                f"🆔 ID: {user_id}"
            )

            content = (
                build_profile_header(
                    announce,
                    expire=expire_timestamp,
                    upload=0,
                    download=0,
                    total=0,
                )
                + servers
            )

            save_user_subscription(
                user_id,
                content,
            )

            updated += 1

            print(
                f"{user_id} — 🟢 "
                f"до {display_date}"
            )

        except Exception as e:

            errors += 1

            print(
                f"❌ Ошибка {user_id}: {e}"
            )

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Синхронизация завершена")
    print(f"🟢 Обновлено: {updated}")
    print(f"🔴 Истекло: {expired}")
    print(f"⚪ Пропущено: {skipped}")
    print(f"❌ Ошибок: {errors}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return {
        "updated": updated,
        "skipped": skipped,
        "expired": expired,
        "errors": errors,
    }


# ============================================================
# АДМИНСКОЕ ОБНОВЛЕНИЕ
# ============================================================

def sync_servers_update():

    print(
        "🔄 Обновление серверов..."
    )

    return sync_all_active_users()


# ============================================================
# АВТОСИНХРОНИЗАТОР
# ============================================================

def _auto_sync_worker():

    print(
        "🤖 Автоматическая синхронизация "
        "запущена"
    )

    print(
        f"⏱ Интервал: "
        f"{AUTO_SYNC_INTERVAL} сек."
    )

    time.sleep(15)

    while True:

        try:

            sync_all_active_users()

        except Exception as e:

            print(
                f"❌ Ошибка автосинхронизации: "
                f"{e}"
            )

        time.sleep(
            AUTO_SYNC_INTERVAL
        )


if AUTO_SYNC_ENABLED:

    sync_thread = threading.Thread(
        target=_auto_sync_worker,
        daemon=True,
        name="ixxy-vpn-auto-sync",
    )

    sync_thread.start()