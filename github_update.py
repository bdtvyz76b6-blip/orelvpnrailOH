import os
import time
import threading
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
# НАЗВАНИЕ ПОДПИСКИ
# ============================================================

PROFILE_TITLE = "𝗦𝗨𝗕 - 𝗜𝗫𝗫𝗬 ☂️"

PROFILE_UPDATE_INTERVAL = 1

# ============================================================
# HAPP — СКРЫТИЕ НАСТРОЕК СЕРВЕРОВ
# ============================================================

# Эта переменная больше не используется напрямую,
# скрытие всегда включено принудительно.
HIDE_SETTINGS = True

# ============================================================
# АВТОМАТИЧЕСКАЯ ПРОВЕРКА ПОДПИСОК
# ============================================================

AUTO_SYNC_ENABLED = os.getenv(
    "AUTO_SYNC_ENABLED",
    "1",
).strip() == "1"

AUTO_SYNC_INTERVAL = int(
    os.getenv(
        "AUTO_SYNC_INTERVAL",
        "600",
    )
)

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
# СЕРВЕРА ДЛЯ НЕАКТИВНОЙ ПОДПИСКИ
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
# ЗАГОЛОВОК ПОДПИСКИ HAPP
# ============================================================

def build_profile_header(announce):
    # Принудительно всегда скрываем настройки серверов
    hide_value = "true"
    return (
        f"#profile-title: {PROFILE_TITLE}\n"
        f"#profile-update-interval: "
        f"{PROFILE_UPDATE_INTERVAL}\n"
        f"#hide-settings: {hide_value}\n"
        f"#announce: {announce}\n\n"
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

# Генерируем заголовок через общую функцию, чтобы гарантировать
# одинаковые параметры и скрытие настроек.
_NEW_USER_ANNOUNCE = "🔒 Подписка не активна • Оформите подписку через @orelvpntopbot"

NEW_USER_TEMPLATE = (
    build_profile_header(_NEW_USER_ANNOUNCE)
    + "vless://00000000-0000-0000-0000-000000000000@expired.invalid:443?type=tcp&security=reality&sni=expired.invalid&fp=chrome&pbk=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA&sid=&flow=xtls-rprx-vision#⛔ Активируйте подписку"
).strip()

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
    announce = (
        f"🟢 Подписка активна • "
        f"до {date} • "
        f"🆔 ID: {user_id}"
    )
    content = (
        build_profile_header(announce)
        + servers
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
# АКТИВАЦИЯ ПОДПИСКИ
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
    no_servers = load_no_servers()
    announce = (
        "🔴 Подписка истекла • "
        "Продлите подписку через @orelvpntopbot"
    )
    content = (
        build_profile_header(announce)
        + no_servers
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
# АКТИВНЫЕ ТАРИФЫ
# ============================================================

ACTIVE_SUBSCRIPTIONS = {
    "vip",
    "trial",

    # Совместимость со старыми названиями тарифов
    "👑 Орёл VPN",
    "🎁 Пробный период",
}

# ============================================================
# СИНХРОНИЗАЦИЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
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
            # =============================================
            # НЕАКТИВНЫЙ ТАРИФ
            # =============================================
            if subscription not in ACTIVE_SUBSCRIPTIONS:
                announce = (
                    "🔴 Подписка не активна • "
                    "Оформите подписку через @orelvpntopbot"
                )
                content = (
                    build_profile_header(announce)
                    + no_servers
                )
                save_user_subscription(
                    user_id,
                    content,
                )
                expired += 1
                print(
                    f"{user_id} — "
                    f"нет активной подписки"
                )
                continue
            # =============================================
            # НЕТ ДАТЫ ПОДПИСКИ
            # =============================================
            if not subscription_until:
                announce = (
                    "🔴 Подписка не активна • "
                    "Оформите подписку через @orelvpntopbot"
                )
                content = (
                    build_profile_header(announce)
                    + no_servers
                )
                save_user_subscription(
                    user_id,
                    content,
                )
                expired += 1
                print(
                    f"{user_id} — "
                    f"нет даты подписки"
                )
                continue
            # =============================================
            # ПРОВЕРКА ФОРМАТА ДАТЫ
            # =============================================
            try:
                expire_date = datetime.strptime(
                    str(subscription_until),
                    "%Y-%m-%d",
                ).date()
            except Exception:
                print(
                    f"❌ Неверная дата у {user_id}: "
                    f"{subscription_until}"
                )
                announce = (
                    "🔴 Ошибка даты подписки • "
                    "Обратитесь в поддержку @orelvpntopbot"
                )
                content = (
                    build_profile_header(announce)
                    + no_servers
                )
                save_user_subscription(
                    user_id,
                    content,
                )
                expired += 1
                continue
            # =============================================
            # ПОДПИСКА ИСТЕКЛА
            # =============================================
            if expire_date < today:
                announce = (
                    "🔴 Подписка истекла • "
                    "Продлите подписку через @orelvpntopbot"
                )
                content = (
                    build_profile_header(announce)
                    + no_servers
                )
                save_user_subscription(
                    user_id,
                    content,
                )
                expired += 1
                print(
                    f"{user_id} — 🔴 подписка истекла"
                )
                continue
            # =============================================
            # АКТИВНАЯ ПОДПИСКА
            # =============================================
            display_date = expire_date.strftime(
                "%d.%m.%Y"
            )
            announce = (
                f"🟢 Подписка активна • "
                f"до {display_date} • "
                f"🆔 ID: {user_id}"
            )
            content = (
                build_profile_header(announce)
                + servers
            )
            save_user_subscription(
                user_id,
                content,
            )
            updated += 1
            print(
                f"{user_id} — "
                f"🟢 активна до {display_date}"
            )
        except Exception as e:
            errors += 1
            print(
                f"❌ Ошибка пользователя "
                f"{user_id}: {e}"
            )
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ Синхронизация завершена")
    print(f"🟢 Обновлено: {updated}")
    print(f"🔴 Истекло/отключено: {expired}")
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
# ОБНОВЛЕНИЕ СЕРВЕРОВ ИЗ АДМИНКИ
# ============================================================

def sync_servers_update():
    print(
        "🔄 Запущено обновление серверов "
        "из админ-панели"
    )
    return sync_all_active_users()

# ============================================================
# АВТОМАТИЧЕСКИЙ СИНХРОНИЗАТОР
# ============================================================

def _auto_sync_worker():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🤖 Автоматическая проверка подписок запущена")
    print(
        f"⏱ Интервал: "
        f"{AUTO_SYNC_INTERVAL} секунд"
    )
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    # Даём приложению время полностью загрузиться.
    time.sleep(15)
    while True:
        try:
            sync_all_active_users()
        except Exception as e:
            print(
                f"❌ Ошибка автоматической "
                f"синхронизации: {e}"
            )
        time.sleep(
            AUTO_SYNC_INTERVAL
        )

# ============================================================
# ЗАПУСК АВТОМАТИЧЕСКОГО СИНХРОНИЗАТОРА
# ============================================================

if AUTO_SYNC_ENABLED:
    sync_thread = threading.Thread(
        target=_auto_sync_worker,
        daemon=True,
        name="ixxy-vpn-auto-sync",
    )
    sync_thread.start()