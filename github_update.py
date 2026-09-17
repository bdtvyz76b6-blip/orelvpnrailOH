# ============================================================
# ☂️ IXXY VPN — server updater
#
# Permanent subscription URLs:
# https://ixxyweb.onrender.com/sub/2ix847xy<USER_ID>
#
# GitHub is used only as an optional source of servers.
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

PUBLIC_SITE_URL = "https://ixxyweb.onrender.com"

SUBSCRIPTION_PREFIX = "2ix847xy"

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
# GITHUB — ТОЛЬКО ИСТОЧНИК СПИСКА СЕРВЕРОВ
# ============================================================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
    "",
).strip()

GITHUB_OWNER = os.getenv(
    "GITHUB_OWNER",
    "bdtvyz76b6-blip",
)

GITHUB_REPO = os.getenv(
    "GITHUB_REPO",
    "vpn-sub",
)

GITHUB_BRANCH = os.getenv(
    "GITHUB_BRANCH",
    "main",
)

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
# GITHUB RAW URL
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
# ПОСТОЯННАЯ ССЫЛКА ПОДПИСКИ
# ============================================================

def get_subscription_link(
    user_id: int,
) -> str:

    return (
        "https://ixxyweb.onrender.com/sub/"
        f"2ix847xy{int(user_id)}"
    )

# ============================================================
# ЗАГРУЗКА ФАЙЛА С GITHUB
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
# ЗАГРУЗКА СПИСКА СЕРВЕРОВ
# ============================================================

def load_servers() -> str:

    # --------------------------------------------------------
    # 1. Прямая ссылка GITHUB_SERVERS_URL
    # --------------------------------------------------------

    if GITHUB_SERVERS_URL:

        try:

            response = requests.get(
                GITHUB_SERVERS_URL,
                headers=github_headers(),
                timeout=20,
            )

            response.raise_for_status()

            text = response.text.strip()

            if text:
                return text

        except Exception as e:

            logger.error(
                "Ошибка GITHUB_SERVERS_URL: %s",
                e,
            )

    # --------------------------------------------------------
    # 2. servers.txt в GitHub
    # --------------------------------------------------------

    try:

        text = load_github_file(
            SERVERS_FILE
        )

        if text:
            return text

    except Exception as e:

        logger.error(
            "Ошибка загрузки серверов из GitHub: %s",
            e,
        )

    # --------------------------------------------------------
    # 3. Локальный servers.txt
    # --------------------------------------------------------

    try:

        if os.path.exists(
            LOCAL_SERVERS_FILE
        ):

            with open(
                LOCAL_SERVERS_FILE,
                "r",
                encoding="utf-8",
            ) as f:

                return f.read().strip()

    except Exception as e:

        logger.error(
            "Ошибка локального servers.txt: %s",
            e,
        )

    return ""

# ============================================================
# NO SERVERS
# ============================================================

def load_no_servers() -> str:
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

        except ValueError:

            continue

    return None

# ============================================================
# DATE → UNIX TIMESTAMP
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
# ПРОВЕРКА АКТИВНОСТИ ПОДПИСКИ
# ============================================================

def is_subscription_active(
    user: dict,
) -> bool:

    if not isinstance(
        user,
        dict,
    ):
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
# HEADER ПОДПИСКИ
# ============================================================

def build_profile_header(
    subscription_until=None,
    user_id=None,
    active=True,
) -> str:

    # Сначала вычисляем значения.
    # Так мы избегаем сложных вложенных f-string.

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
# СОЗДАНИЕ CONTENT ПОДПИСКИ
# ============================================================

def build_subscription_content(
    user_id: int,
    active: bool,
    subscription_until=None,
) -> str:

    header = build_profile_header(
        subscription_until,
        user_id,
        active,
    )

    # Если подписка неактивна —
    # серверы пользователю не выдаём.

    if not active:

        return (
            header
            + "\n"
        )

    servers = load_servers()

    if not servers:

        raise RuntimeError(
            "Список серверов пуст — "
            "обновление отменено"
        )

    return (
        header.rstrip()
        + "\n"
        + servers.strip()
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

        user = get_user(
            int(user_id)
        ) or {}

        # Всегда используем только
        # каноническую постоянную ссылку.

        link = get_subscription_link(
            user_id
        )

        if content is None:

            content = (
                build_subscription_content(
                    int(user_id),

                    is_subscription_active(
                        user
                    ),

                    user.get(
                        "subscription_until"
                    ),
                )
            )

        save_subscription_content(
            int(user_id),
            content,
        )

        save_subscription_link(
            int(user_id),
            link,
        )

        return True

    except Exception as e:

        logger.error(
            "Ошибка сохранения подписки %s: %s",
            user_id,
            e,
        )

        return False

# ============================================================
# СОЗДАНИЕ ПОСТОЯННОЙ ПОДПИСКИ
# ============================================================

def create_user_subscription(
    user_id: int,
) -> Optional[str]:

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
# СТАРАЯ ФУНКЦИЯ ДЛЯ СОВМЕСТИМОСТИ
# ============================================================

def create_subscription(
    user_id: int,
    days: int = 30,
) -> Optional[str]:

    return create_user_subscription(
        user_id
    )

# ============================================================
# АКТИВАЦИЯ ПОДПИСКИ
# ============================================================

def activate_subscription_file(
    user_id: int,
    subscription_until=None,
) -> bool:

    content = build_subscription_content(
        user_id,
        True,
        subscription_until,
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
# ОБНОВЛЕНИЕ ПОДПИСКИ ОДНОГО ПОЛЬЗОВАТЕЛЯ
# ============================================================

def update_subscription_file(
    user_id: int,
) -> bool:

    user = get_user(
        int(user_id)
    )

    if not user:
        return False

    content = build_subscription_content(
        int(user_id),

        is_subscription_active(
            user
        ),

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
# ОБНОВИТЬ СЕРВЕРЫ У ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

def sync_all_active_users() -> dict:

    servers = load_servers()

    if not servers:

        raise RuntimeError(
            "Список серверов пуст. "
            "Обновление отменено."
        )

    users = get_all_users() or []

    updated = 0
    failed = 0
    skipped = 0

    for user in users:

        if (
            not isinstance(
                user,
                dict,
            )
            or user.get(
                "user_id"
            ) is None
        ):

            skipped += 1
            continue

        uid = int(
            user["user_id"]
        )

        try:

            content = (
                build_subscription_content(
                    uid,

                    is_subscription_active(
                        user
                    ),

                    user.get(
                        "subscription_until"
                    ),
                )
            )

            success = (
                save_user_subscription(
                    uid,
                    content,
                    get_subscription_link(
                        uid
                    ),
                )
            )

            if success:

                updated += 1

            else:

                failed += 1

        except Exception as e:

            failed += 1

            logger.error(
                "Ошибка обновления %s: %s",
                uid,
                e,
            )

    result = {
        "total": len(users),
        "updated": updated,
        "skipped": skipped,
        "failed": failed,
    }

    logger.info(
        "🔄 IXXY: серверы обновлены: %s",
        result,
    )

    return result

# ============================================================
# СОВМЕСТИМОСТЬ
# ============================================================

def sync_servers_update() -> dict:

    return sync_all_active_users()

def update_user_servers(
    user_id: int,
) -> bool:

    return update_subscription_file(
        user_id
    )

# ============================================================
# АВТОСИНХРОНИЗАЦИЯ
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

                sync_all_active_users()

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