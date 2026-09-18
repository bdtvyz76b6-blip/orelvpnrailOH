import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
MAX_PROMO_DAYS = int(
    os.getenv("MAX_PROMO_DAYS", "999999999999")
)
UTC = timezone.utc
# =========================================================
# IXXY
# =========================================================
PUBLIC_SITE_URL = (
    "https://orelvpnrailoh-1-xyis.onrender.com"
)
SUBSCRIPTION_PREFIX = "2ix847xy"
def get_canonical_subscription_link(
    user_id: int,
) -> str:
    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}{int(user_id)}"
    )
# =========================================================
# DATETIME
# =========================================================
def now_utc() -> datetime:
    return datetime.now(UTC)
def normalize_datetime(
    value: Any,
) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            value = value.replace(
                "Z",
                "+00:00",
            )
            dt = datetime.fromisoformat(
                value
            )
            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=UTC
                )
            return dt.astimezone(UTC)
        except Exception:
            logger.exception(
                "Не удалось разобрать datetime: %r",
                value,
            )
            return None
    return None
def format_date(
    value: Any,
) -> str:
    dt = normalize_datetime(value)
    if not dt:
        return "—"
    return dt.strftime("%d.%m.%Y")
def subscription_active(
    subscription_until: Any,
) -> bool:
    dt = normalize_datetime(
        subscription_until
    )
    if not dt:
        return False
    return dt > now_utc()
# =========================================================
# DATABASE
# =========================================================
def connect():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL не задан"
        )
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        connect_timeout=15,
    )
def init_db():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    subscription BOOLEAN DEFAULT FALSE,
                    subscription_until TIMESTAMPTZ,
                    subscription_link TEXT,
                    uuid TEXT,
                    trial_used BOOLEAN DEFAULT FALSE,
                    pending_days INTEGER DEFAULT 0,
                    notify BOOLEAN DEFAULT TRUE,
                    accepted_terms BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    subscription_content TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    payment_id TEXT,
                    external_id TEXT,
                    amount INTEGER,
                    days INTEGER,
                    status TEXT,
                    provider TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    paid_at TIMESTAMPTZ
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    days BIGINT NOT NULL,
                    max_uses BIGINT DEFAULT 0,
                    uses BIGINT DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS promocode_uses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    code TEXT NOT NULL,
                    used_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(user_id, code)
                )
                """
            )
            # -------------------------------------------------
            # MIGRATIONS
            # -------------------------------------------------
            columns = {
                "username": "TEXT",
                "first_name": "TEXT",
                "subscription": "BOOLEAN DEFAULT FALSE",
                "subscription_until": "TIMESTAMPTZ",
                "subscription_link": "TEXT",
                "uuid": "TEXT",
                "trial_used": "BOOLEAN DEFAULT FALSE",
                "pending_days": "INTEGER DEFAULT 0",
                "notify": "BOOLEAN DEFAULT TRUE",
                "accepted_terms": "BOOLEAN DEFAULT FALSE",
                "created_at": "TIMESTAMPTZ DEFAULT NOW()",
                "subscription_content": "TEXT",
            }
            for column, definition in columns.items():
                cur.execute(
                    """
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = 'users'
                      AND column_name = %s
                    """,
                    (column,),
                )
                exists = cur.fetchone()
                if not exists:
                    cur.execute(
                        f"""
                        ALTER TABLE users
                        ADD COLUMN {column} {definition}
                        """
                    )
            conn.commit()
            logger.info(
                "База данных успешно инициализирована"
            )
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка инициализации базы данных"
        )
        raise
    finally:
        conn.close()
# =========================================================
# USERS
# =========================================================
def create_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    user_id,
                    username,
                    first_name
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
                """,
                (
                    int(user_id),
                    username,
                    first_name,
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка создания пользователя %s",
            user_id,
        )
        raise
    finally:
        conn.close()
def get_user(
    user_id: int,
) -> Optional[dict]:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
def get_all_users() -> list:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                ORDER BY created_at DESC
                """
            )
            return [
                dict(row)
                for row in cur.fetchall()
            ]
    finally:
        conn.close()
def search_users(
    query: str,
) -> list:
    query = str(query).strip()
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                WHERE
                    CAST(user_id AS TEXT) ILIKE %s
                    OR COALESCE(username, '') ILIKE %s
                    OR COALESCE(first_name, '') ILIKE %s
                ORDER BY created_at DESC
                """,
                (
                    f"%{query}%",
                    f"%{query}%",
                    f"%{query}%",
                ),
            )
            return [
                dict(row)
                for row in cur.fetchall()
            ]
    finally:
        conn.close()
def delete_user(
    user_id: int,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка удаления пользователя %s",
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# SUBSCRIPTION LINKS
# =========================================================
def save_subscription_link(
    user_id: int,
    link: Optional[str] = None,
):
    canonical_link = (
        get_canonical_subscription_link(
            user_id
        )
    )
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET subscription_link = %s
                WHERE user_id = %s
                """,
                (
                    canonical_link,
                    int(user_id),
                ),
            )
            conn.commit()
            return canonical_link
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка сохранения ссылки подписки user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
def get_subscription_link(
    user_id: int,
) -> str:
    return get_canonical_subscription_link(
        user_id
    )
# =========================================================
# SUBSCRIPTION CONTENT
# =========================================================
def save_subscription_content(
    user_id: int,
    content: str,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET subscription_content = %s
                WHERE user_id = %s
                """,
                (
                    content,
                    int(user_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка сохранения subscription_content user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
def get_subscription_content(
    user_id: int,
) -> Optional[str]:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT subscription_content
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                return None
            return row[0]
    finally:
        conn.close()
# =========================================================
# SUBSCRIPTIONS
# =========================================================
def extend_subscription(
    user_id: int,
    days: int,
):
    days = int(days)
    if days <= 0:
        return
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT subscription_until
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """
                    INSERT INTO users (
                        user_id,
                        subscription,
                        subscription_until
                    )
                    VALUES (
                        %s,
                        TRUE,
                        %s
                    )
                    """,
                    (
                        int(user_id),
                        now_utc()
                        + timedelta(days=days),
                    ),
                )
            else:
                current = normalize_datetime(
                    row[0]
                )
                current_now = now_utc()
                if (
                    current
                    and current > current_now
                ):
                    new_until = (
                        current
                        + timedelta(days=days)
                    )
                else:
                    new_until = (
                        current_now
                        + timedelta(days=days)
                    )
                cur.execute(
                    """
                    UPDATE users
                    SET
                        subscription = TRUE,
                        subscription_until = %s
                    WHERE user_id = %s
                    """,
                    (
                        new_until,
                        int(user_id),
                    ),
                )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка продления подписки user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
def activate_subscription(
    user_id: int,
    days: int,
    subscription_link: Optional[str] = None,
):
    create_user(user_id)
    extend_subscription(
        user_id,
        days,
    )
    save_subscription_link(
        user_id
    )
def activate_trial(
    user_id: int,
    days: int = 3,
    subscription_link: Optional[str] = None,
):
    create_user(user_id)
    if use_trial(user_id):
        extend_subscription(
            user_id,
            days,
        )
        save_subscription_link(
            user_id
        )
        return True
    return False
def revoke_subscription(
    user_id: int,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET
                    subscription = FALSE,
                    subscription_until = NULL
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка отключения подписки user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
def disable_subscription(
    user_id: int,
):
    return revoke_subscription(user_id)
def check_expired_subscriptions() -> int:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET subscription = FALSE
                WHERE subscription = TRUE
                  AND subscription_until IS NOT NULL
                  AND subscription_until <= %s
                """,
                (now_utc(),),
            )
            count = cur.rowcount
            conn.commit()
            return count
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка проверки истёкших подписок"
        )
        raise
    finally:
        conn.close()
def get_expired_users() -> list:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                WHERE
                    subscription_until IS NOT NULL
                    AND subscription_until <= %s
                ORDER BY subscription_until ASC
                """,
                (now_utc(),),
            )
            return [
                dict(row)
                for row in cur.fetchall()
            ]
    finally:
        conn.close()
# =========================================================
# TRIAL
# =========================================================
def use_trial(
    user_id: int,
) -> bool:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT trial_used
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    """
                    INSERT INTO users (
                        user_id,
                        trial_used
                    )
                    VALUES (%s, TRUE)
                    """,
                    (int(user_id),),
                )
                conn.commit()
                return True
            if row[0]:
                conn.rollback()
                return False
            cur.execute(
                """
                UPDATE users
                SET trial_used = TRUE
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка активации trial user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# PROMOCODES
# =========================================================
def create_promocode(
    code: str,
    days: int,
    max_uses: int = 0,
) -> bool:
    code = str(code).strip().upper()
    days = int(days)
    max_uses = int(max_uses)
    if not code:
        return False
    if days <= 0:
        return False
    if days > MAX_PROMO_DAYS:
        return False
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO promocodes (
                    code,
                    days,
                    max_uses,
                    uses,
                    active
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    0,
                    TRUE
                )
                ON CONFLICT (code)
                DO UPDATE SET
                    days = EXCLUDED.days,
                    max_uses = EXCLUDED.max_uses,
                    active = TRUE
                """,
                (
                    code,
                    days,
                    max_uses,
                ),
            )
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка создания промокода %s",
            code,
        )
        raise
    finally:
        conn.close()
def get_promocode(
    code: str,
) -> Optional[dict]:
    code = str(code).strip().upper()
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM promocodes
                WHERE code = %s
                """,
                (code,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
def get_all_promocodes() -> list:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM promocodes
                ORDER BY created_at DESC
                """
            )
            return [
                dict(row)
                for row in cur.fetchall()
            ]
    finally:
        conn.close()
def deactivate_promocode(
    code: str,
) -> bool:
    code = str(code).strip().upper()
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE promocodes
                SET active = FALSE
                WHERE code = %s
                """,
                (code,),
            )
            changed = cur.rowcount > 0
            conn.commit()
            return changed
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка отключения промокода %s",
            code,
        )
        raise
    finally:
        conn.close()
def promocode_available(
    code: str,
) -> bool:
    promo = get_promocode(code)
    if not promo:
        return False
    if not promo["active"]:
        return False
    max_uses = int(
        promo["max_uses"] or 0
    )
    uses = int(
        promo["uses"] or 0
    )
    if max_uses > 0 and uses >= max_uses:
        return False
    return True
def use_promocode(
    user_id: int,
    code: str,
) -> Optional[int]:
    code = str(code).strip().upper()
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM promocodes
                WHERE code = %s
                FOR UPDATE
                """,
                (code,),
            )
            promo = cur.fetchone()
            if not promo:
                conn.rollback()
                return None
            if not promo["active"]:
                conn.rollback()
                return None
            max_uses = int(
                promo["max_uses"] or 0
            )
            uses = int(
                promo["uses"] or 0
            )
            if (
                max_uses > 0
                and uses >= max_uses
            ):
                conn.rollback()
                return None
            cur.execute(
                """
                SELECT 1
                FROM promocode_uses
                WHERE user_id = %s
                  AND code = %s
                """,
                (
                    int(user_id),
                    code,
                ),
            )
            already_used = cur.fetchone()
            if already_used:
                conn.rollback()
                return None
            cur.execute(
                """
                INSERT INTO promocode_uses (
                    user_id,
                    code
                )
                VALUES (%s, %s)
                """,
                (
                    int(user_id),
                    code,
                ),
            )
            cur.execute(
                """
                UPDATE promocodes
                SET uses = uses + 1
                WHERE code = %s
                """,
                (code,),
            )
            conn.commit()
            return int(promo["days"])
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка использования промокода %s user=%s",
            code,
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# PAYMENTS
# =========================================================
def create_payment(
    user_id: int,
    payment_id: Optional[str],
    amount: int,
    days: int,
    status: str = "pending",
    provider: str = "cashera",
    external_id: Optional[str] = None,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO payments (
                    user_id,
                    payment_id,
                    external_id,
                    amount,
                    days,
                    status,
                    provider
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    int(user_id),
                    payment_id,
                    external_id,
                    int(amount),
                    int(days),
                    status,
                    provider,
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка создания платежа"
        )
        raise
    finally:
        conn.close()
def get_payment(
    payment_id: str,
) -> Optional[dict]:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (str(payment_id),),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()
def get_payment_by_payment_id(
    payment_id: str,
) -> Optional[dict]:
    return get_payment(payment_id)
def update_payment_status(
    payment_id: str,
    status: str,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE payments
                SET
                    status = %s,
                    paid_at = CASE
                        WHEN %s = 'paid'
                        THEN COALESCE(
                            paid_at,
                            %s
                        )
                        ELSE paid_at
                    END
                WHERE payment_id = %s
                """,
                (
                    status,
                    status,
                    now_utc(),
                    str(payment_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка обновления платежа %s",
            payment_id,
        )
        raise
    finally:
        conn.close()
def process_paid_payment(
    payment_id: str,
) -> Optional[dict]:
    conn = connect()
    try:
        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:
            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_id = %s
                ORDER BY id DESC
                LIMIT 1
                FOR UPDATE
                """,
                (str(payment_id),),
            )
            payment = cur.fetchone()
            if not payment:
                conn.rollback()
                return None
            if payment["status"] == "paid":
                conn.rollback()
                return dict(payment)
            user_id = int(
                payment["user_id"]
            )
            days = int(
                payment["days"] or 0
            )
            cur.execute(
                """
                SELECT subscription_until
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (user_id,),
            )
            user = cur.fetchone()
            current_now = now_utc()
            if user:
                current_until = (
                    normalize_datetime(
                        user["subscription_until"]
                    )
                )
            else:
                current_until = None
            if (
                current_until
                and current_until > current_now
            ):
                new_until = (
                    current_until
                    + timedelta(days=days)
                )
            else:
                new_until = (
                    current_now
                    + timedelta(days=days)
                )
            cur.execute(
                """
                INSERT INTO users (
                    user_id,
                    subscription,
                    subscription_until,
                    subscription_link
                )
                VALUES (
                    %s,
                    TRUE,
                    %s,
                    %s
                )
                ON CONFLICT (user_id)
                DO UPDATE SET
                    subscription = TRUE,
                    subscription_until = EXCLUDED.subscription_until,
                    subscription_link = EXCLUDED.subscription_link
                """,
                (
                    user_id,
                    new_until,
                    get_canonical_subscription_link(
                        user_id
                    ),
                ),
            )
            cur.execute(
                """
                UPDATE payments
                SET
                    status = 'paid',
                    paid_at = COALESCE(
                        paid_at,
                        %s
                    )
                WHERE payment_id = %s
                """,
                (
                    current_now,
                    str(payment_id),
                ),
            )
            conn.commit()
            result = dict(payment)
            result["status"] = "paid"
            result["subscription_until"] = (
                new_until
            )
            result["subscription_link"] = (
                get_canonical_subscription_link(
                    user_id
                )
            )
            return result
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка обработки оплаченного платежа %s",
            payment_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# NOTIFICATIONS
# =========================================================
def get_notification_setting(
    user_id: int,
) -> bool:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT notify
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                return True
            return bool(row[0])
    finally:
        conn.close()
def set_notification(
    user_id: int,
    enabled: bool,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET notify = %s
                WHERE user_id = %s
                """,
                (
                    bool(enabled),
                    int(user_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка настройки уведомлений user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# TERMS
# =========================================================
def get_accepted_terms(
    user_id: int,
) -> bool:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT accepted_terms
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                return False
            return bool(row[0])
    finally:
        conn.close()
def set_accepted_terms(
    user_id: int,
    accepted: bool = True,
):
    create_user(user_id)
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET accepted_terms = %s
                WHERE user_id = %s
                """,
                (
                    bool(accepted),
                    int(user_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка сохранения accepted_terms user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# PENDING DAYS
# =========================================================
def get_pending_days(
    user_id: int,
) -> int:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pending_days
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )
            row = cur.fetchone()
            if not row:
                return 0
            return int(row[0] or 0)
    finally:
        conn.close()
def set_pending_days(
    user_id: int,
    days: int,
):
    create_user(user_id)
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET pending_days = %s
                WHERE user_id = %s
                """,
                (
                    int(days),
                    int(user_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка pending_days user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
def add_pending_days(
    user_id: int,
    days: int,
):
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET pending_days =
                    COALESCE(pending_days, 0)
                    + %s
                WHERE user_id = %s
                """,
                (
                    int(days),
                    int(user_id),
                ),
            )
            conn.commit()
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка добавления pending_days user=%s",
            user_id,
        )
        raise
    finally:
        conn.close()
# =========================================================
# STATISTICS
# =========================================================
def get_stats() -> dict:
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                """
            )
            total_users = int(
                cur.fetchone()[0]
            )
            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE subscription = TRUE
                  AND subscription_until > %s
                """,
                (now_utc(),),
            )
            active_users = int(
                cur.fetchone()[0]
            )
            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE trial_used = TRUE
                """
            )
            trial_users = int(
                cur.fetchone()[0]
            )
            cur.execute(
                """
                SELECT COUNT(*)
                FROM payments
                WHERE status = 'paid'
                """
            )
            paid_payments = int(
                cur.fetchone()[0]
            )
            cur.execute(
                """
                SELECT COALESCE(
                    SUM(amount),
                    0
                )
                FROM payments
                WHERE status = 'paid'
                """
            )
            revenue = int(
                cur.fetchone()[0] or 0
            )
            return {
                "total_users": total_users,
                "active_users": active_users,
                "trial_users": trial_users,
                "paid_payments": paid_payments,
                "revenue": revenue,
            }
    finally:
        conn.close()
# =========================================================
# CANONICAL URL MIGRATION
# =========================================================
def migrate_subscription_links():
    conn = connect()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET subscription_link =
                    %s || user_id::text
                WHERE user_id IS NOT NULL
                """,
                (
                    f"{PUBLIC_SITE_URL}/sub/"
                    f"{SUBSCRIPTION_PREFIX}",
                ),
            )
            changed = cur.rowcount
            conn.commit()
            logger.info(
                "Исправлено ссылок IXXY: %s",
                changed,
            )
            return changed
    except Exception:
        conn.rollback()
        logger.exception(
            "Ошибка миграции ссылок"
        )
        raise
    finally:
        conn.close()
# =========================================================
# COMPATIBILITY
# =========================================================
create_table = init_db