# ============================================================
# ☂️ IXXY VPN — server updater
#
# Постоянные ссылки:
# https://ixxyweb.onrender.com/sub/2ix847xy<USER_ID>
#
# Логика:
# GitHub servers.txt
#        ↓
# новый список серверов
#        ↓
# обновление subscription_content
#        ↓
# постоянные ссылки пользователей НЕ меняются
# ============================================================
import os
import logging
from datetime import datetime, date, timezone
from typing import Optional
import requests
from dotenv import load_dotenv
from database import (
    get_all_users,
    get_user,
    save_subscription_content,
    save_subscription_link,
)
load_dotenv()
logger = logging.getLogger(__name__)
UTC = timezone.utc
# ============================================================
# CONFIG
# ============================================================
PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://ixxyweb.onrender.com",
).rstrip("/")
SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()
PROFILE_TITLE = os.getenv(
    "PROFILE_TITLE",
    "𝗦𝗨𝗕 - 𝗜𝗫𝗫𝗬 ☂️",
)
PROFILE_UPDATE_INTERVAL = os.getenv(
    "PROFILE_UPDATE_INTERVAL",
    "1",
)
HIDE_SETTINGS = os.getenv(
    "HIDE_SETTINGS",
    "True",
)
TRAFFIC_TOTAL = os.getenv(
    "TRAFFIC_TOTAL",
    "0",
)
TRAFFIC_UPLOAD = os.getenv(
    "TRAFFIC_UPLOAD",
    "0",
)
TRAFFIC_DOWNLOAD = os.getenv(
    "TRAFFIC_DOWNLOAD",
    "0",
)
# ============================================================
# GITHUB
# ============================================================
GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
).strip()
GITHUB_OWNER = os.getenv(
    "GITHUB_OWNER",
    "bdtvyz76b6-blip",
).strip()
GITHUB_REPO = os.getenv(
    "GITHUB_REPO",
    "vpn-sub",
).strip()
GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
).strip()
SERVERS_FILE = os.getenv(
    "SERVERS_FILE",
    "servers.txt",
).strip()
GITHUB_SERVERS_URL = os.getenv(
    "GITHUB_SERVERS_URL",
    "",
).strip()
LOCAL_SERVERS_FILE = os.getenv(
    "LOCAL_SERVERS_FILE",
    "servers.txt",
).strip()
# ============================================================
# GITHUB HEADERS
# ============================================================
def github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ixxy-vpn",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = (
            f"Bearer {GITHUB_TOKEN}"
        )
    return headers
# ============================================================
# RAW GITHUB URL
# ============================================================
def raw_url(filename: str) -> str:
    return (
        "https://raw.githubusercontent.com/"
        f"{GITHUB_OWNER}/"
        f"{GITHUB_REPO}/"
        f"{GITHUB_BRANCH}/"
        f"{filename.lstrip('/')}"
    )
# ============================================================
# ПОСТОЯННАЯ ССЫЛКА
# ============================================================
def get_subscription_link(
    user_id: int,
) -> str:
    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}{int(user_id)}"
    )
# ============================================================
# GITHUB FILE
# ============================================================
def load_github_file(
    filename: str,
) -> str:
    response = requests.get(
        raw_url(filename),
        headers=github_headers(),
        timeout=20,
    )
    response.raise_for_status()
    return response.text.strip()
# ============================================================
# ЗАГРУЗКА СЕРВЕРОВ
# ============================================================
def load_servers() -> str:
    # --------------------------------------------------------
    # 1. Прямая ссылка
    # --------------------------------------------------------
    if GITHUB_SERVERS_URL:
        try:
            logger.info(
                "📡 Загружаю серверы из GITHUB_SERVERS_URL"
            )
            response = requests.get(
                GITHUB_SERVERS_URL,
                headers=github_headers(),
                timeout=20,
            )
            response.raise_for_status()
            text = response.text.strip()
            if text:
                logger.info(
                    "✅ Серверы загружены: %s символов",
                    len(text),
                )
                return text
        except Exception as e:
            logger.error(
                "❌ Ошибка GITHUB_SERVERS_URL: %s",
                e,
            )
    # --------------------------------------------------------
    # 2. GitHub servers.txt
    # --------------------------------------------------------
    try:
        logger.info(
            "📡 Загружаю %s из GitHub",
            SERVERS_FILE,
        )
        text = load_github_file(
            SERVERS_FILE
        )
        if text:
            logger.info(
                "✅ servers.txt загружен: %s символов",
                len(text),
            )
            return text
    except Exception as e:
        logger.error(
            "❌ Ошибка загрузки servers.txt: %s",
            e,
        )
    # --------------------------------------------------------
    # 3. Локальный файл
    # --------------------------------------------------------
    try:
        if os.path.exists(
            LOCAL_SERVERS_FILE
        ):
            logger.info(
                "📂 Использую локальный %s",
                LOCAL_SERVERS_FILE,
            )
            with open(
                LOCAL_SERVERS_FILE,
                "r",
                encoding="utf-8",
            ) as f:
                text = f.read().strip()
            if text:
                return text
    except Exception as e:
        logger.error(
            "❌ Ошибка локального servers.txt: %s",
            e,
        )
    return ""
# ============================================================
# DATETIME
# ============================================================
def _to_datetime(
    value,
) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(
        value,
        datetime,
    ):
        if value.tzinfo is None:
            return value.replace(
                tzinfo=UTC
            )
        return value.astimezone(
            UTC
        )
    if isinstance(
        value,
        date,
    ):
        return datetime.combine(
            value,
            datetime.min.time(),
            tzinfo=UTC,
        )
    text = str(value).strip()
    if not text:
        return None
    parsers = (
        lambda x: datetime.fromisoformat(
            x.replace(
                "Z",
                "+00:00",
            )
        ),
        lambda x: datetime.strptime(
            x,
            "%Y-%m-%d",
        ),
        lambda x: datetime.strptime(
            x,
            "%d.%m.%Y",
        ),
        lambda x: datetime.strptime(
            x,
            "%Y-%m-%d %H:%M:%S",
        ),
    )
    for parser in parsers:
        try:
            dt = parser(text)
            if dt.tzinfo is None:
                return dt.replace(
                    tzinfo=UTC
                )
            return dt.astimezone(
                UTC
            )
        except (
            ValueError,
            TypeError,
        ):
            continue
    return None
# ============================================================
# DATE → UNIX
# ============================================================
def date_to_timestamp(
    value,
) -> int:
    dt = _to_datetime(
        value
    )
    if not dt:
        return 0
    return int(
        dt.timestamp()
    )
# ============================================================
# ФОРМАТ ДАТЫ
# ============================================================
def format_subscription_date(
    value,
) -> str:
    dt = _to_datetime(
        value
    )
    if not dt:
        return "—"
    return dt.strftime(
        "%d.%m.%Y"
    )
# ============================================================
# АКТИВНА ЛИ ПОДПИСКА
# ============================================================
def is_subscription_active(
    user: dict,
) -> bool:
    if not isinstance(
        user,
        dict,
    ):
        return False
    # ВАЖНО:
    # PostgreSQL subscription должен быть True.
    if user.get(
        "subscription"
    ) is not True:
        return False
    until = _to_datetime(
        user.get(
            "subscription_until"
        )
    )
    if not until:
        return False
    return (
        until.date()
        >= datetime.now(
            UTC
        ).date()
    )
# ============================================================
# HEADER
# ============================================================
def build_profile_header(
    subscription_until=None,
    user_id=None,
    active=True,
) -> str:
    date_text = format_subscription_date(
        subscription_until
    )
    expire_timestamp = date_to_timestamp(
        subscription_until
    )
    if active:
        announce = (
            "🟢 Подписка активна"
            f" • до {date_text}"
        )
        if user_id is not None:
            announce += (
                f" • 🆔 ID: {user_id}"
            )
    else:
        announce = (
            "🔴 Подписка не активна"
            " • Продлите подписку"
            " в боте ixxy VPN"
        )
    lines = [
        f"#profile-title: {PROFILE_TITLE}",
        (
            "#profile-update-interval: "
            f"{PROFILE_UPDATE_INTERVAL}"
        ),
        (
            "#subscription-userinfo: "
            f"upload={TRAFFIC_UPLOAD}; "
            f"download={TRAFFIC_DOWNLOAD}; "
            f"total={TRAFFIC_TOTAL}; "
            f"expire={expire_timestamp}"
        ),
        (
            "#hide-settings: "
            f"{str(HIDE_SETTINGS).lower()}"
        ),
        "#happ-hide-settings: true",
        "#hide_server_settings: true",
        "#hidesettings: true",
        f"#announce: {announce}",
    ]
    return "\n".join(
        lines
    )
# ============================================================
# СОЗДАНИЕ CONTENT
#
# servers передаём аргументом.
#
# Благодаря этому при массовой синхронизации GitHub
# запрашивается ОДИН раз, а не для каждого пользователя.
# ============================================================
def build_subscription_content(
    user_id: int,
    active: bool,
    subscription_until=None,
    servers: Optional[str] = None,
) -> str:
    header = build_profile_header(
        subscription_until,
        user_id,
        active,
    )
    # --------------------------------------------------------
    # Неактивному пользователю серверы не выдаём.
    # --------------------------------------------------------
    if not active:
        return (
            header.rstrip()
            + "\n"
        )
    # --------------------------------------------------------
    # Если servers не передали —
    # загружаем самостоятельно.
    # --------------------------------------------------------
    if servers is None:
        servers = load_servers()
    servers = (
        servers or ""
    ).strip()
    if not servers:
        raise RuntimeError(
            "Список серверов пуст — "
            "обновление отменено"
        )
    return (
        header.rstrip()
        + "\n"
        + servers
        + "\n"
    )
# ============================================================
# СОХРАНЕНИЕ ПОДПИСКИ
# ============================================================
def save_user_subscription(
    user_id: int,
    content=None,
    link=None,
) -> bool:
    try:
        user_id = int(
            user_id
        )
        user = get_user(
            user_id
        ) or {}
        # Постоянная ссылка всегда
        # вычисляется заново из ID.
        #
        # Старая ссылка пользователя
        # никогда не меняется.
        permanent_link = (
            get_subscription_link(
                user_id
            )
        )
        if content is None:
            content = (
                build_subscription_content(
                    user_id,
                    is_subscription_active(
                        user
                    ),
                    user.get(
                        "subscription_until"
                    ),
                )
            )
        save_subscription_content(
            user_id,
            content,
        )
        save_subscription_link(
            user_id,
            permanent_link,
        )
        return True
    except Exception as e:
        logger.error(
            "❌ Ошибка сохранения подписки "
            "%s: %s",
            user_id,
            e,
        )
        return False
# ============================================================
# СОЗДАНИЕ ПОДПИСКИ
# ============================================================
def create_user_subscription(
    user_id: int,
) -> Optional[str]:
    user_id = int(
        user_id
    )
    link = get_subscription_link(
        user_id
    )
    if save_user_subscription(
        user_id,
        link=link,
    ):
        return link
    return None
# ============================================================
# СОВМЕСТИМОСТЬ
# ============================================================
def create_subscription(
    user_id: int,
    days: int = 30,
) -> Optional[str]:
    return create_user_subscription(
        user_id
    )
# ============================================================
# АКТИВАЦИЯ
# ============================================================
def activate_subscription_file(
    user_id: int,
    subscription_until=None,
) -> bool:
    servers = load_servers()
    if not servers:
        raise RuntimeError(
            "Список серверов пуст"
        )
    content = build_subscription_content(
        user_id,
        True,
        subscription_until,
        servers,
    )
    return save_user_subscription(
        user_id,
        content,
        get_subscription_link(
            user_id
        ),
    )
def activate_user_subscription(
    user_id: int,
    subscription_until=None,
) -> bool:
    return activate_subscription_file(
        user_id,
        subscription_until,
    )
# ============================================================
# ОБНОВЛЕНИЕ ОДНОГО ПОЛЬЗОВАТЕЛЯ
# ============================================================
def update_subscription_file(
    user_id: int,
    servers: Optional[str] = None,
) -> bool:
    user_id = int(
        user_id
    )
    user = get_user(
        user_id
    )
    if not user:
        logger.warning(
            "⚠️ Пользователь %s не найден",
            user_id,
        )
        return False
    if servers is None:
        servers = load_servers()
    active = is_subscription_active(
        user
    )
    content = build_subscription_content(
        user_id,
        active,
        user.get(
            "subscription_until"
        ),
        servers,
    )
    return save_user_subscription(
        user_id,
        content,
        get_subscription_link(
            user_id
        ),
    )
# ============================================================
# ИСТЁКШАЯ ПОДПИСКА
# ============================================================
def expire_subscription(
    user_id: int,
) -> bool:
    user = get_user(
        int(user_id)
    ) or {}
    content = build_subscription_content(
        int(user_id),
        False,
        user.get(
            "subscription_until"
        ),
    )
    return save_user_subscription(
        int(user_id),
        content,
        get_subscription_link(
            user_id
        ),
    )
# ============================================================
# ГЛАВНАЯ СИНХРОНИЗАЦИЯ
#
# Именно ЭТУ функцию вызывает кнопка:
# admin_sync_servers
#
# Она:
#
# 1. Один раз скачивает servers.txt
# 2. Проверяет, что список не пуст
# 3. Берёт всех пользователей
# 4. Активным записывает новые серверы
# 5. Неактивным оставляет только header
# 6. Сохраняет subscription_content
# 7. Сохраняет постоянную ссылку
# ============================================================
def sync_servers_update() -> dict:
    logger.info(
        "🔄 IXXY: начинаю обновление серверов"
    )
    # --------------------------------------------------------
    # ШАГ 1 — загружаем серверы ОДИН РАЗ
    # --------------------------------------------------------
    servers = load_servers()
    servers = (
        servers or ""
    ).strip()
    if not servers:
        logger.error(
            "❌ IXXY: servers.txt пуст"
        )
        raise RuntimeError(
            "Список серверов пуст. "
            "Обновление подписок отменено."
        )
    # --------------------------------------------------------
    # Считаем количество строк серверов
    # --------------------------------------------------------
    server_lines = [
        line.strip()
        for line in servers.splitlines()
        if line.strip()
    ]
    total_servers = len(
        server_lines
    )
    logger.info(
        "📡 IXXY: получено серверов: %s",
        total_servers,
    )
    # --------------------------------------------------------
    # ШАГ 2 — получаем всех пользователей
    # --------------------------------------------------------
    users = get_all_users() or []
    total_users = len(
        users
    )
    logger.info(
        "👥 IXXY: пользователей: %s",
        total_users,
    )
    updated = 0
    expired = 0
    skipped = 0
    failed = 0
    # --------------------------------------------------------
    # ШАГ 3 — обновляем каждого пользователя
    #
    # ВАЖНО:
    # servers передаётся напрямую.
    #
    # Поэтому load_servers() здесь НЕ вызывается повторно.
    # --------------------------------------------------------
    for user in users:
        if not isinstance(
            user,
            dict,
        ):
            skipped += 1
            continue
        raw_user_id = user.get(
            "user_id"
        )
        if raw_user_id is None:
            skipped += 1
            continue
        try:
            user_id = int(
                raw_user_id
            )
        except (
            TypeError,
            ValueError,
        ):
            skipped += 1
            continue
        try:
            active = (
                is_subscription_active(
                    user
                )
            )
            # ------------------------------------------------
            # Активная подписка
            # ------------------------------------------------
            if active:
                content = (
                    build_subscription_content(
                        user_id,
                        True,
                        user.get(
                            "subscription_until"
                        ),
                        servers,
                    )
                )
                save_user_subscription(
                    user_id,
                    content,
                    get_subscription_link(
                        user_id
                    ),
                )
                updated += 1
                logger.info(
                    "✅ IXXY: пользователь %s "
                    "обновлён",
                    user_id,
                )
            # ------------------------------------------------
            # Истёкшая / неактивная
            # ------------------------------------------------
            else:
                content = (
                    build_subscription_content(
                        user_id,
                        False,
                        user.get(
                            "subscription_until"
                        ),
                        servers,
                    )
                )
                save_user_subscription(
                    user_id,
                    content,
                    get_subscription_link(
                        user_id
                    ),
                )
                expired += 1
                logger.info(
                    "⛔ IXXY: пользователь %s "
                    "неактивен",
                    user_id,
                )
        except Exception as e:
            failed += 1
            logger.error(
                "❌ IXXY: ошибка обновления "
                "пользователя %s: %s",
                user_id,
                e,
            )
    # --------------------------------------------------------
    # РЕЗУЛЬТАТ
    # --------------------------------------------------------
    result = {
        "total": total_servers,
        "users": total_users,
        "updated": updated,
        "expired": expired,
        "skipped": skipped,
        "failed": failed,
    }
    logger.info(
        "🔄 IXXY: серверы обновлены: %s",
        result,
    )
    return result
# ============================================================
# СОВМЕСТИМОСТЬ СО СТАРЫМ КОДОМ
# ============================================================
def sync_all_active_users() -> dict:
    return sync_servers_update()
def update_user_servers(
    user_id: int,
) -> bool:
    return update_subscription_file(
        user_id
    )
# ============================================================
# AUTO SYNC
# ============================================================
AUTO_SYNC_ENABLED = (
    os.getenv(
        "AUTO_SYNC_ENABLED",
        "0",
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)
try:
    AUTO_SYNC_INTERVAL = max(
        60,
        int(
            os.getenv(
                "AUTO_SYNC_INTERVAL",
                "600",
            )
        ),
    )
except ValueError:
    AUTO_SYNC_INTERVAL = 600
def start_auto_sync():
    import threading
    import time
    def worker():
        while True:
            try:
                sync_servers_update()
            except Exception as e:
                logger.error(
                    "❌ IXXY AUTO SYNC ERROR: %s",
                    e,
                )
            time.sleep(
                AUTO_SYNC_INTERVAL
            )
    thread = threading.Thread(
        target=worker,
        daemon=True,
        name="ixxy-server-sync",
    )
    thread.start()
    return thread
if AUTO_SYNC_ENABLED:
    start_auto_sync()

Главное изменение осталось только в массовой синхронизации: GitHub servers.txt скачивается один раз за запуск sync_servers_update(), а затем один и тот же servers передаётся каждому пользователю. Путь подписки остаётся https://ixxyweb.onrender.com/sub/2ix847xy<ID>.