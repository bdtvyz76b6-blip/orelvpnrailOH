# ============================================================
# ☂️ IXXY VPN — server updater
#
# ПОСТОЯННАЯ ССЫЛКА:
# https://orelvpnrailoh-1-xyis.onrender.com/sub/2ix847xy<USER_ID>
#
# Пример:
# https://orelvpnrailoh-1-xyis.onrender.com/sub/2ix847xy6312016802
#
# ЛОГИКА:
# 1. Загружаем актуальный servers.txt из GitHub.
# 2. Получаем всех пользователей из БД.
# 3. Активным пользователям записываем актуальные серверы.
# 4. Неактивным пользователям записываем пустую подписку.
# 5. Ссылка пользователя НИКОГДА не меняется.
# ============================================================
import os
import logging
import threading
import time
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
# IXXY — КАНОНИЧЕСКИЙ URL
# ============================================================
PUBLIC_SITE_URL = (
    "https://orelvpnrailoh-1-xyis.onrender.com"
)
SUBSCRIPTION_PREFIX = "2ix847xy"
# ============================================================
# PROFILE CONFIG
# ============================================================
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
        "X-GitHub-Api-Version": "2022-11-28",
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
# ПОСТОЯННАЯ ССЫЛКА ПОЛЬЗОВАТЕЛЯ
# ============================================================
def get_subscription_link(
    user_id: int,
) -> str:
    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}"
        f"{int(user_id)}"
    )
# ============================================================
# ЗАГРУЗКА ФАЙЛА ИЗ GITHUB
# ============================================================
def load_github_file(
    filename: str,
) -> str:
    url = raw_url(filename)
    logger.info(
        "🌐 Загрузка GitHub файла: %s",
        url,
    )
    response = requests.get(
        url,
        headers=github_headers(),
        timeout=20,
    )
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        raise RuntimeError(
            f"GitHub файл {filename} пустой"
        )
    return text
# ============================================================
# ЗАГРУЗКА SERVERS.TXT
# ============================================================
def load_servers() -> str:
    # --------------------------------------------------------
    # 1. Прямой URL
    # --------------------------------------------------------
    if GITHUB_SERVERS_URL:
        try:
            logger.info(
                "🌐 Пробуем GITHUB_SERVERS_URL"
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
                    "✅ Серверы загружены через "
                    "GITHUB_SERVERS_URL"
                )
                return text
        except Exception as e:
            logger.error(
                "❌ GITHUB_SERVERS_URL ошибка: %s",
                e,
            )
    # --------------------------------------------------------
    # 2. GitHub Raw
    # --------------------------------------------------------
    try:
        text = load_github_file(
            SERVERS_FILE
        )
        if text:
            logger.info(
                "✅ Серверы загружены из GitHub: %s",
                SERVERS_FILE,
            )
            return text
    except Exception as e:
        logger.error(
            "❌ Ошибка GitHub servers.txt: %s",
            e,
        )
    # --------------------------------------------------------
    # 3. Локальный файл
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
                text = f.read().strip()
            if text:
                logger.info(
                    "✅ Серверы загружены "
                    "из локального servers.txt"
                )
                return text
    except Exception as e:
        logger.error(
            "❌ Ошибка локального servers.txt: %s",
            e,
        )
    logger.error(
        "❌ Не удалось получить список серверов"
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
    text = str(
        value
    ).strip()
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
# ПРОВЕРКА АКТИВНОСТИ
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
        until > datetime.now(UTC)
    )
# ============================================================
# HEADER ПОДПИСКИ
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
            " на сайте IXXY VPN"
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
    # НЕАКТИВНАЯ
    # --------------------------------------------------------
    if not active:
        return (
            header.rstrip()
            + "\n"
        )
    # --------------------------------------------------------
    # АКТИВНАЯ
    # --------------------------------------------------------
    if servers is None:
        servers = load_servers()
    if not servers:
        raise RuntimeError(
            "Список серверов пуст"
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
    uid = int(
        user_id
    )
    try:
        user = get_user(
            uid
        ) or {}
        # ----------------------------------------------------
        # ВСЕГДА КАНОНИЧЕСКАЯ ССЫЛКА
        # ----------------------------------------------------
        permanent_link = (
            get_subscription_link(
                uid
            )
        )
        logger.info(
            "🔗 IXXY subscription %s: %s",
            uid,
            permanent_link,
        )
        # ----------------------------------------------------
        # Если CONTENT не передан
        # ----------------------------------------------------
        if content is None:
            active = is_subscription_active(
                user
            )
            content = build_subscription_content(
                uid,
                active,
                user.get(
                    "subscription_until"
                ),
            )
        if not content:
            raise RuntimeError(
                "CONTENT подписки пустой"
            )
        # ----------------------------------------------------
        # Сохраняем CONTENT
        # ----------------------------------------------------
        save_subscription_content(
            uid,
            content,
        )
        logger.info(
            "💾 CONTENT сохранён для %s",
            uid,
        )
        # ----------------------------------------------------
        # Сохраняем постоянную ссылку
        # ----------------------------------------------------
        save_subscription_link(
            uid,
            permanent_link,
        )
        logger.info(
            "💾 LINK сохранён для %s",
            uid,
        )
        return True
    except Exception as e:
        logger.exception(
            "❌ Ошибка сохранения подписки %s: %s",
            uid,
            e,
        )
        return False
# ============================================================
# СОЗДАНИЕ ПОДПИСКИ
# ============================================================
def create_user_subscription(
    user_id: int,
) -> Optional[str]:
    uid = int(
        user_id
    )
    link = get_subscription_link(
        uid
    )
    if save_user_subscription(
        uid,
        link=link,
    ):
        return link
    return None
# ============================================================
# СТАРАЯ ФУНКЦИЯ
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
    uid = int(
        user_id
    )
    servers = load_servers()
    if not servers:
        logger.error(
            "❌ Нельзя активировать %s: "
            "servers.txt пуст",
            uid,
        )
        return False
    content = build_subscription_content(
        uid,
        True,
        subscription_until,
        servers,
    )
    return save_user_subscription(
        uid,
        content,
        get_subscription_link(
            uid
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
) -> bool:
    uid = int(
        user_id
    )
    logger.info(
        "🔄 Обновление подписки %s",
        uid,
    )
    user = get_user(
        uid
    )
    if not user:
        logger.warning(
            "⚠️ Пользователь %s не найден",
            uid,
        )
        return False
    active = is_subscription_active(
        user
    )
    subscription_until = (
        user.get(
            "subscription_until"
        )
    )
    # --------------------------------------------------------
    # АКТИВНЫЙ
    # --------------------------------------------------------
    if active:
        servers = load_servers()
        if not servers:
            logger.error(
                "❌ servers.txt пуст. "
                "Подписка %s НЕ изменена.",
                uid,
            )
            return False
    # --------------------------------------------------------
    # НЕАКТИВНЫЙ
    # --------------------------------------------------------
    else:
        servers = None
    content = build_subscription_content(
        uid,
        active,
        subscription_until,
        servers,
    )
    return save_user_subscription(
        uid,
        content,
        get_subscription_link(
            uid
        ),
    )
# ============================================================
# ИСТЁКШАЯ ПОДПИСКА
# ============================================================
def expire_subscription(
    user_id: int,
) -> bool:
    uid = int(
        user_id
    )
    user = get_user(
        uid
    ) or {}
    content = build_subscription_content(
        uid,
        False,
        user.get(
            "subscription_until"
        ),
        None,
    )
    return save_user_subscription(
        uid,
        content,
        get_subscription_link(
            uid
        ),
    )
# ============================================================
# СИНХРОНИЗАЦИЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
def sync_all_active_users() -> dict:
    logger.info(
        "================================================"
    )
    logger.info(
        "🔄 IXXY: запуск синхронизации"
    )
    logger.info(
        "================================================"
    )
    # --------------------------------------------------------
    # 1. Загружаем servers.txt ОДИН РАЗ
    # --------------------------------------------------------
    servers = load_servers()
    if not servers:
        logger.error(
            "❌ servers.txt пуст."
        )
        raise RuntimeError(
            "Список серверов пуст. "
            "Синхронизация отменена."
        )
    logger.info(
        "✅ Актуальные серверы получены."
    )
    # --------------------------------------------------------
    # 2. Получаем всех пользователей
    # --------------------------------------------------------
    users = get_all_users() or []
    logger.info(
        "👥 Пользователей в БД: %s",
        len(users),
    )
    updated = 0
    failed = 0
    skipped = 0
    active_count = 0
    inactive_count = 0
    # --------------------------------------------------------
    # 3. Обрабатываем пользователей
    # --------------------------------------------------------
    for user in users:
        if not isinstance(
            user,
            dict,
        ):
            skipped += 1
            continue
        user_id = user.get(
            "user_id"
        )
        if user_id is None:
            skipped += 1
            continue
        try:
            uid = int(
                user_id
            )
        except (
            TypeError,
            ValueError,
        ):
            skipped += 1
            continue
        try:
            # ------------------------------------------------
            # Свежая запись из БД
            # ------------------------------------------------
            db_user = get_user(
                uid
            )
            if not db_user:
                skipped += 1
                logger.warning(
                    "⚠️ %s отсутствует в БД",
                    uid,
                )
                continue
            # ------------------------------------------------
            # Проверяем срок
            # ------------------------------------------------
            active = is_subscription_active(
                db_user
            )
            subscription_until = (
                db_user.get(
                    "subscription_until"
                )
            )
            # ------------------------------------------------
            # АКТИВНЫЙ
            # ------------------------------------------------
            if active:
                active_count += 1
                content = build_subscription_content(
                    uid,
                    True,
                    subscription_until,
                    servers,
                )
                logger.info(
                    "🟢 %s — серверы обновлены",
                    uid,
                )
            # ------------------------------------------------
            # НЕАКТИВНЫЙ
            # ------------------------------------------------
            else:
                inactive_count += 1
                content = build_subscription_content(
                    uid,
                    False,
                    subscription_until,
                    None,
                )
                logger.info(
                    "🔴 %s — подписка неактивна",
                    uid,
                )
            # ------------------------------------------------
            # Сохраняем
            # ------------------------------------------------
            success = save_user_subscription(
                uid,
                content,
                get_subscription_link(
                    uid
                ),
            )
            if success:
                updated += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            logger.exception(
                "❌ Ошибка пользователя %s: %s",
                uid,
                e,
            )
    # --------------------------------------------------------
    # Результат
    # --------------------------------------------------------
    result = {
        "total": len(users),
        "updated": updated,
        "active": active_count,
        "inactive": inactive_count,
        "skipped": skipped,
        "failed": failed,
    }
    logger.info(
        "================================================"
    )
    logger.info(
        "✅ IXXY SYNC ЗАВЕРШЁН"
    )
    logger.info(
        "📊 %s",
        result,
    )
    logger.info(
        "================================================"
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
        "1",
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
except (
    ValueError,
    TypeError,
):
    AUTO_SYNC_INTERVAL = 600
# ============================================================
# AUTO SYNC WORKER
# ============================================================
def start_auto_sync():
    def worker():
        logger.info(
            "🔄 IXXY AUTO SYNC запущен"
        )
        logger.info(
            "⏱ Интервал: %s секунд",
            AUTO_SYNC_INTERVAL,
        )
        while True:
            try:
                result = sync_all_active_users()
                logger.info(
                    "✅ AUTO SYNC: %s",
                    result,
                )
            except Exception as e:
                logger.exception(
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
# ============================================================
# START AUTO SYNC
# ============================================================
if AUTO_SYNC_ENABLED:
    start_auto_sync()