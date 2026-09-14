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


# ============================================================
# TIME
# ============================================================

def now_utc() -> datetime:
    return datetime.now(UTC)


def normalize_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    if hasattr(value, "isoformat"):
        try:
            result = datetime.fromisoformat(
                value.isoformat()
            )
            if result.tzinfo is None:
                result = result.replace(tzinfo=UTC)
            return result.astimezone(UTC)
        except Exception:
            pass

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        formats = (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d.%m.%Y",
        )

        for fmt in formats:
            try:
                result = datetime.strptime(
                    value,
                    fmt,
                )

                if result.tzinfo is None:
                    result = result.replace(
                        tzinfo=UTC
                    )

                return result.astimezone(UTC)

            except ValueError:
                continue

        try:
            result = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if result.tzinfo is None:
                result = result.replace(
                    tzinfo=UTC
                )

            return result.astimezone(UTC)

        except Exception:
            return None

    return None


def format_date(value: Any) -> str:
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

    return dt.date() >= now_utc().date()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect():

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL не задан. "
            "Добавь DATABASE_URL в окружение Render."
        )

    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=10,
    )


# ============================================================
# DATABASE INIT / MIGRATION
# ============================================================

def init_db():

    conn = connect()

    try:

        with conn.cursor() as cur:

            # =================================================
            # USERS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    subscription BOOLEAN NOT NULL DEFAULT FALSE,
                    subscription_until TIMESTAMPTZ,
                    subscription_link TEXT,
                    uuid TEXT,
                    trial_used BOOLEAN NOT NULL DEFAULT FALSE,
                    pending_days INTEGER NOT NULL DEFAULT 0,
                    notify BOOLEAN NOT NULL DEFAULT TRUE,
                    accepted_terms BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    subscription_content TEXT
                )
                """
            )

            # =================================================
            # PAYMENTS
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    payment_id TEXT,
                    external_id TEXT,
                    amount INTEGER NOT NULL DEFAULT 0,
                    days INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    provider TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    paid_at TIMESTAMPTZ
                )
                """
            )

            # =================================================
            # PROMOCODES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS promocodes (
                    code TEXT PRIMARY KEY,
                    days INTEGER NOT NULL,
                    max_uses INTEGER NOT NULL DEFAULT 0,
                    uses INTEGER NOT NULL DEFAULT 0,
                    active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )

            # =================================================
            # PROMOCODE USES
            # =================================================

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS promocode_uses (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    code TEXT NOT NULL,
                    used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, code)
                )
                """
            )

            conn.commit()

            # =================================================
            # USERS.SUBSCRIPTION
            # =================================================

            cur.execute(
                """
                SELECT
                    data_type,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'users'
                  AND column_name = 'subscription'
                """
            )

            subscription_info = cur.fetchone()

            if (
                subscription_info
                and subscription_info[0] != "boolean"
            ):

                logger.warning(
                    "🔄 Миграция users.subscription -> BOOLEAN"
                )

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription DROP DEFAULT
                    """
                )

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription TYPE BOOLEAN
                    USING (
                        CASE
                            WHEN LOWER(
                                TRIM(
                                    subscription::text
                                )
                            ) IN (
                                'true',
                                't',
                                '1',
                                'yes',
                                'on'
                            )
                            THEN TRUE
                            ELSE FALSE
                        END
                    )
                    """
                )

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription
                    SET DEFAULT FALSE
                    """
                )

                conn.commit()

                logger.info(
                    "✅ users.subscription -> BOOLEAN"
                )

            elif (
                subscription_info
                and subscription_info[0] == "boolean"
            ):

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription
                    SET DEFAULT FALSE
                    """
                )

                conn.commit()

            # =================================================
            # USERS.SUBSCRIPTION_UNTIL
            #
            # TEXT -> TIMESTAMPTZ
            # =================================================

            cur.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'users'
                  AND column_name = 'subscription_until'
                """
            )

            until_info = cur.fetchone()

            if (
                until_info
                and until_info[0] != "timestamp with time zone"
            ):

                logger.warning(
                    "🔄 Миграция users.subscription_until -> TIMESTAMPTZ"
                )

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription_until DROP DEFAULT
                    """
                )

                cur.execute(
                    """
                    ALTER TABLE users
                    ALTER COLUMN subscription_until TYPE TIMESTAMPTZ
                    USING (
                        CASE
                            WHEN subscription_until IS NULL
                                THEN NULL

                            WHEN TRIM(
                                subscription_until::text
                            ) = ''
                                THEN NULL

                            WHEN TRIM(
                                subscription_until::text
                            ) ~
                            '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
                                THEN (
                                    TRIM(
                                        subscription_until::text
                                    )::date
                                )::timestamptz

                            WHEN TRIM(
                                subscription_until::text
                            ) ~
                            '^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}$'
                                THEN to_timestamp(
                                    TRIM(
                                        subscription_until::text
                                    ),
                                    'DD.MM.YYYY'
                                )

                            ELSE (
                                TRIM(
                                    subscription_until::text
                                )::timestamptz
                            )
                        END
                    )
                    """
                )

                conn.commit()

                logger.info(
                    "✅ users.subscription_until -> TIMESTAMPTZ"
                )

            # =================================================
            # PAYMENTS COLUMNS
            # =================================================

            cur.execute(
                """
                ALTER TABLE payments
                ADD COLUMN IF NOT EXISTS provider TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE payments
                ADD COLUMN IF NOT EXISTS external_id TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE payments
                ADD COLUMN IF NOT EXISTS status TEXT
                DEFAULT 'pending'
                """
            )

            cur.execute(
                """
                ALTER TABLE payments
                ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ
                """
            )

            # =================================================
            # USERS COLUMNS
            # =================================================

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS subscription_content TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS subscription_link TEXT
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS pending_days
                INTEGER NOT NULL DEFAULT 0
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS notify
                BOOLEAN NOT NULL DEFAULT TRUE
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS accepted_terms
                BOOLEAN NOT NULL DEFAULT FALSE
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS trial_used
                BOOLEAN NOT NULL DEFAULT FALSE
                """
            )

            cur.execute(
                """
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMPTZ NOT NULL DEFAULT NOW()
                """
            )

            # =================================================
            # PAYMENTS DUPLICATES
            #
            # Перед UNIQUE удаляем старые дубликаты.
            # Оставляем самую старую запись.
            # =================================================

            cur.execute(
                """
                DELETE FROM payments p
                USING payments p2
                WHERE p.id > p2.id
                  AND p.payment_id IS NOT NULL
                  AND p.payment_id = p2.payment_id
                """
            )

            # =================================================
            # UNIQUE PAYMENT ID
            # =================================================

            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_payments_payment_id_unique
                ON payments(payment_id)
                """
            )

            # =================================================
            # INDEXES
            # =================================================

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_users_username
                ON users(username)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_users_subscription
                ON users(subscription)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_users_subscription_until
                ON users(subscription_until)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_payments_user_id
                ON payments(user_id)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_payments_status
                ON payments(status)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_payments_provider
                ON payments(provider)
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_payments_external_id
                ON payments(external_id)
                """
            )

            conn.commit()

            # =================================================
            # FINAL SCHEMA LOG
            # =================================================

            cur.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = 'users'
                  AND column_name IN (
                      'subscription',
                      'subscription_until'
                  )
                ORDER BY column_name
                """
            )

            logger.info(
                "📊 USERS SCHEMA: %s",
                cur.fetchall(),
            )

            logger.info(
                "✅ PostgreSQL успешно инициализирован"
            )

    except Exception:

        conn.rollback()

        logger.exception(
            "❌ Ошибка инициализации PostgreSQL"
        )

        raise

    finally:
        conn.close()


create_table = init_db


# ============================================================
# USERS
# ============================================================

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
                    username = COALESCE(
                        EXCLUDED.username,
                        users.username
                    ),
                    first_name = COALESCE(
                        EXCLUDED.first_name,
                        users.first_name
                    )
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


def add_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
):

    return create_user(
        user_id,
        username,
        first_name,
    )


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

            return (
                dict(row)
                if row
                else None
            )

    finally:
        conn.close()


def get_all_users() -> list[dict]:

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


def count_users() -> int:

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                """
            )

            return int(
                cur.fetchone()[0]
            )

    finally:
        conn.close()


def update_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
):

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE users
                SET
                    username = COALESCE(
                        %s,
                        username
                    ),
                    first_name = COALESCE(
                        %s,
                        first_name
                    )
                WHERE user_id = %s
                """,
                (
                    username,
                    first_name,
                    int(user_id),
                ),
            )

            conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# SUBSCRIPTIONS
# ============================================================

def check_user_subscription(
    user_id: int,
) -> bool:

    user = get_user(user_id)

    if not user:
        return False

    until = user.get(
        "subscription_until"
    )

    active = subscription_active(
        until
    )

    current_status = bool(
        user.get(
            "subscription",
            False,
        )
    )

    if active and not current_status:

        _set_subscription_status(
            user_id,
            True,
        )

    elif not active and current_status:

        _set_subscription_status(
            user_id,
            False,
        )

    return active


def is_subscription_active(
    user_id: int,
) -> bool:

    return check_user_subscription(
        user_id
    )


def get_subscription_until(
    user_id: int,
) -> Optional[datetime]:

    user = get_user(user_id)

    if not user:
        return None

    return normalize_datetime(
        user.get(
            "subscription_until"
        )
    )


def _set_subscription_status(
    user_id: int,
    status: bool,
):

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE users
                SET subscription = %s
                WHERE user_id = %s
                """,
                (
                    bool(status),
                    int(user_id),
                ),
            )

            conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def extend_subscription(
    user_id: int,
    days: int,
) -> datetime:

    days = int(days)

    if days <= 0:
        raise ValueError(
            "Количество дней должно быть больше 0"
        )

    conn = connect()

    try:

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            cur.execute(
                """
                SELECT subscription_until
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (int(user_id),),
            )

            user = cur.fetchone()

            if not user:

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
                        NULL
                    )
                    """,
                    (int(user_id),),
                )

                current_until = None

            else:

                current_until = normalize_datetime(
                    user.get(
                        "subscription_until"
                    )
                )

            current_time = now_utc()

            if (
                current_until
                and current_until > current_time
            ):
                base = current_until
            else:
                base = current_time

            new_until = (
                base + timedelta(days=days)
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

            return new_until

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка продления подписки %s",
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

    new_until = extend_subscription(
        user_id,
        days,
    )

    if subscription_link:
        save_subscription_link(
            user_id,
            subscription_link,
        )

    return new_until


def deactivate_subscription(
    user_id: int,
):

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE users
                SET subscription = FALSE
                WHERE user_id = %s
                """,
                (int(user_id),),
            )

            conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def disable_subscription(
    user_id: int,
):

    return deactivate_subscription(
        user_id
    )


# ============================================================
# EXPIRED
# ============================================================

def expire_old_subscriptions() -> int:

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE users
                SET subscription = FALSE
                WHERE subscription = TRUE
                  AND (
                      subscription_until IS NULL
                      OR subscription_until <= NOW()
                  )
                """
            )

            changed = cur.rowcount

            conn.commit()

            return int(changed)

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка проверки истёкших подписок"
        )

        raise

    finally:
        conn.close()


check_expired_subscriptions = (
    expire_old_subscriptions
)


def get_expired_users() -> list[dict]:

    conn = connect()

    try:

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            cur.execute(
                """
                SELECT *
                FROM users
                WHERE subscription = TRUE
                  AND (
                      subscription_until IS NULL
                      OR subscription_until <= NOW()
                  )
                ORDER BY subscription_until ASC
                """
            )

            return [
                dict(row)
                for row in cur.fetchall()
            ]

    finally:
        conn.close()


# ============================================================
# SUBSCRIPTION CONTENT
# ============================================================

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

            return (
                row[0]
                if row
                else None
            )

    finally:
        conn.close()


def save_subscription_link(
    user_id: int,
    link: str,
):

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
                    link,
                    int(user_id),
                ),
            )

            conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def get_subscription_link(
    user_id: int,
) -> Optional[str]:

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT subscription_link
                FROM users
                WHERE user_id = %s
                """,
                (int(user_id),),
            )

            row = cur.fetchone()

            return (
                row[0]
                if row
                else None
            )

    finally:
        conn.close()


# ============================================================
# TRIAL
# ============================================================

def use_trial(
    user_id: int,
    days: int = 1,
) -> bool:

    days = int(days)

    if days <= 0:
        return False

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
                FOR UPDATE
                """,
                (int(user_id),),
            )

            user = cur.fetchone()

            if not user:

                cur.execute(
                    """
                    INSERT INTO users (
                        user_id,
                        trial_used
                    )
                    VALUES (%s, FALSE)
                    """,
                    (int(user_id),),
                )

                user = {
                    "trial_used": False,
                    "subscription_until": None,
                }

            if bool(
                user.get(
                    "trial_used",
                    False,
                )
            ):

                conn.rollback()
                return False

            current_until = normalize_datetime(
                user.get(
                    "subscription_until"
                )
            )

            current_time = now_utc()

            if (
                current_until
                and current_until > current_time
            ):

                new_until = (
                    current_until
                    + timedelta(days=days)
                )

            else:

                new_until = (
                    current_time
                    + timedelta(days=days)
                )

            cur.execute(
                """
                UPDATE users
                SET
                    trial_used = TRUE,
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

            return True

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка выдачи пробного периода %s",
            user_id,
        )

        raise

    finally:
        conn.close()


def check_trial(
    user_id: int,
) -> bool:

    user = get_user(user_id)

    if not user:
        return False

    return bool(
        user.get(
            "trial_used",
            False,
        )
    )


def activate_trial(
    user_id: int,
    days=3,
    subscription_link: Optional[str] = None,
) -> bool:

    if isinstance(days, str):
        subscription_link = days
        days = 3

    result = use_trial(
        user_id,
        int(days),
    )

    if result and subscription_link:

        save_subscription_link(
            user_id,
            subscription_link,
        )

    return result


# ============================================================
# PROMOCODES
# ============================================================

def create_promocode(
    code: str,
    days: int,
    max_uses: int = 0,
) -> bool:

    code = str(code).strip().upper()
    days = int(days)
    max_uses = int(max_uses)

    if not code or days <= 0:
        return False

    if days > MAX_PROMO_DAYS:
        days = MAX_PROMO_DAYS

    if max_uses < 0:
        max_uses = 0

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
                  AND active = TRUE
                """,
                (code,),
            )

            row = cur.fetchone()

            return (
                dict(row)
                if row
                else None
            )

    finally:
        conn.close()


def get_all_promocodes() -> list[dict]:

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

            changed = cur.rowcount

            conn.commit()

            return changed > 0

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def use_promocode(
    user_id: int,
    code: str,
) -> tuple[bool, str, int]:

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
                  AND active = TRUE
                FOR UPDATE
                """,
                (code,),
            )

            promo = cur.fetchone()

            if not promo:

                conn.rollback()

                return (
                    False,
                    "Промокод не найден или уже отключён.",
                    0,
                )

            max_uses = int(
                promo.get("max_uses") or 0
            )

            uses = int(
                promo.get("uses") or 0
            )

            if (
                max_uses > 0
                and uses >= max_uses
            ):

                conn.rollback()

                return (
                    False,
                    "Лимит использований промокода исчерпан.",
                    0,
                )

            cur.execute(
                """
                SELECT id
                FROM promocode_uses
                WHERE user_id = %s
                  AND code = %s
                """,
                (
                    int(user_id),
                    code,
                ),
            )

            if cur.fetchone():

                conn.rollback()

                return (
                    False,
                    "Вы уже использовали этот промокод.",
                    0,
                )

            days = int(
                promo["days"]
            )

            cur.execute(
                """
                SELECT subscription_until
                FROM users
                WHERE user_id = %s
                FOR UPDATE
                """,
                (int(user_id),),
            )

            user = cur.fetchone()

            if not user:

                cur.execute(
                    """
                    INSERT INTO users (
                        user_id
                    )
                    VALUES (%s)
                    """,
                    (int(user_id),),
                )

                current_until = None

            else:

                current_until = normalize_datetime(
                    user["subscription_until"]
                )

            current_time = now_utc()

            if (
                current_until
                and current_until > current_time
            ):

                new_until = (
                    current_until
                    + timedelta(days=days)
                )

            else:

                new_until = (
                    current_time
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

            return (
                True,
                f"Промокод активирован: +{days} дн.",
                days,
            )

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        return (
            False,
            "Вы уже использовали этот промокод.",
            0,
        )

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка использования промокода %s "
            "пользователем %s",
            code,
            user_id,
        )

        raise

    finally:
        conn.close()


def use_promocode_legacy(
    user_id: int,
    code: str,
):
    return use_promocode(
        user_id,
        code,
    )


# ============================================================
# PAYMENTS
# ============================================================

def create_payment(
    user_id: int,
    payment_id: str,
    amount: int,
    days: int,
    provider: str = "cashera",
    external_id: Optional[str] = None,
) -> bool:

    payment_id = str(payment_id).strip()

    if not payment_id:
        raise ValueError(
            "payment_id не может быть пустым"
        )

    conn = connect()

    try:

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            # Проверяем существующий платёж.
            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_id = %s
                """,
                (payment_id,),
            )

            existing = cur.fetchone()

            if existing:

                logger.info(
                    "💳 Платёж уже существует: %s",
                    payment_id,
                )

                conn.rollback()

                return False

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
                    'pending',
                    %s
                )
                """,
                (
                    int(user_id),
                    payment_id,
                    external_id,
                    int(amount),
                    int(days),
                    provider,
                ),
            )

            conn.commit()

            logger.info(
                "💾 Платёж сохранён: %s",
                payment_id,
            )

            return True

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        logger.info(
            "💳 Платёж уже существует: %s",
            payment_id,
        )

        return False

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка создания платежа %s",
            payment_id,
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
                """,
                (str(payment_id),),
            )

            row = cur.fetchone()

            return (
                dict(row)
                if row
                else None
            )

    finally:
        conn.close()


def get_payment_by_payment_id(
    payment_id: str,
) -> Optional[dict]:

    return get_payment(
        payment_id
    )


def get_payment_by_external_id(
    external_id: str,
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
                WHERE external_id = %s
                """,
                (str(external_id),),
            )

            row = cur.fetchone()

            return (
                dict(row)
                if row
                else None
            )

    finally:
        conn.close()


def complete_payment(
    payment_id: str,
) -> bool:

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE payments
                SET
                    status = 'paid',
                    paid_at = COALESCE(
                        paid_at,
                        NOW()
                    )
                WHERE payment_id = %s
                  AND status != 'paid'
                """,
                (str(payment_id),),
            )

            changed = cur.rowcount

            conn.commit()

            return changed > 0

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def update_payment_status(
    payment_id: str,
    status: str,
):

    status = str(
        status
    ).strip().lower()

    conn = connect()

    try:

        with conn.cursor() as cur:

            if status == "paid":

                cur.execute(
                    """
                    UPDATE payments
                    SET
                        status = 'paid',
                        paid_at = COALESCE(
                            paid_at,
                            NOW()
                        )
                    WHERE payment_id = %s
                    """,
                    (str(payment_id),),
                )

            else:

                cur.execute(
                    """
                    UPDATE payments
                    SET status = %s
                    WHERE payment_id = %s
                    """,
                    (
                        status,
                        str(payment_id),
                    ),
                )

            conn.commit()

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


def get_all_payments(
    limit: int = 100,
) -> list[dict]:

    conn = connect()

    try:

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            cur.execute(
                """
                SELECT *
                FROM payments
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (int(limit),),
            )

            return [
                dict(row)
                for row in cur.fetchall()
            ]

    finally:
        conn.close()


# ============================================================
# PROCESS PAID PAYMENT
# ============================================================

def process_paid_payment(
    payment_id: str,
) -> Optional[dict]:

    """
    Главная функция после успешной оплаты.

    Делает:
    1. Находит платёж.
    2. Блокирует его.
    3. Если уже paid — ничего повторно не начисляет.
    4. Берёт количество дней.
    5. Прибавляет дни к текущей подписке.
    6. Ставит платёж в paid.
    """

    conn = connect()

    try:

        with conn.cursor(
            cursor_factory=RealDictCursor
        ) as cur:

            # ------------------------------------------------
            # Блокируем платёж
            # ------------------------------------------------

            cur.execute(
                """
                SELECT *
                FROM payments
                WHERE payment_id = %s
                FOR UPDATE
                """,
                (str(payment_id),),
            )

            payment = cur.fetchone()

            if not payment:

                conn.rollback()

                logger.warning(
                    "Платёж не найден: %s",
                    payment_id,
                )

                return None

            # ------------------------------------------------
            # Защита от повторного webhook
            # ------------------------------------------------

            if str(
                payment.get("status", "")
            ).lower() in (
                "paid",
                "success",
                "successful",
                "completed",
                "approved",
            ):

                logger.info(
                    "ℹ️ Платёж уже обработан: %s",
                    payment_id,
                )

                conn.rollback()

                return {
                    "already_paid": True,
                    **dict(payment),
                }

            # ------------------------------------------------
            # Данные платежа
            # ------------------------------------------------

            user_id = int(
                payment["user_id"]
            )

            days = int(
                payment["days"]
            )

            if days <= 0:

                conn.rollback()

                raise ValueError(
                    "У платежа некорректное количество дней"
                )

            # ------------------------------------------------
            # Блокируем пользователя
            # ------------------------------------------------

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

            if not user:

                cur.execute(
                    """
                    INSERT INTO users (
                        user_id,
                        subscription
                    )
                    VALUES (
                        %s,
                        FALSE
                    )
                    """,
                    (user_id,),
                )

                current_until = None

            else:

                current_until = normalize_datetime(
                    user["subscription_until"]
                )

            # ------------------------------------------------
            # Считаем новую дату
            # ------------------------------------------------

            current_time = now_utc()

            if (
                current_until
                and current_until > current_time
            ):

                base = current_until

            else:

                base = current_time

            new_until = (
                base + timedelta(days=days)
            )

            # ------------------------------------------------
            # Выдаём подписку
            # ------------------------------------------------

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
                    user_id,
                ),
            )

            # ------------------------------------------------
            # Помечаем платёж
            # ------------------------------------------------

            cur.execute(
                """
                UPDATE payments
                SET
                    status = 'paid',
                    paid_at = COALESCE(
                        paid_at,
                        NOW()
                    )
                WHERE payment_id = %s
                """,
                (str(payment_id),),
            )

            conn.commit()

            logger.info(
                "✅ Платёж обработан: user=%s days=%s until=%s",
                user_id,
                days,
                new_until,
            )

            return {
                "already_paid": False,
                "user_id": user_id,
                "days": days,
                "subscription_until": new_until,
                "payment_id": str(payment_id),
                "provider": payment.get(
                    "provider"
                ),
            }

    except Exception:

        conn.rollback()

        logger.exception(
            "Ошибка обработки оплаченного платежа %s",
            payment_id,
        )

        raise

    finally:
        conn.close()


# ============================================================
# NOTIFICATIONS
# ============================================================

def set_notify(
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
        raise

    finally:
        conn.close()


def get_notify(
    user_id: int,
) -> bool:

    user = get_user(user_id)

    if not user:
        return True

    return bool(
        user.get(
            "notify",
            True,
        )
    )


# ============================================================
# TERMS
# ============================================================

def set_accepted_terms(
    user_id: int,
    accepted: bool = True,
):

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
        raise

    finally:
        conn.close()


def accepted_terms(
    user_id: int,
) -> bool:

    user = get_user(user_id)

    if not user:
        return False

    return bool(
        user.get(
            "accepted_terms",
            False,
        )
    )


def has_accepted_terms(
    user_id: int,
) -> bool:

    return accepted_terms(
        user_id
    )


def accept_terms(
    user_id: int,
) -> bool:

    set_accepted_terms(
        user_id,
        True,
    )

    return True


# ============================================================
# PENDING DAYS
# ============================================================

def set_pending_days(
    user_id: int,
    days: int,
):

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
        raise

    finally:
        conn.close()


def get_pending_days(
    user_id: int,
) -> int:

    user = get_user(user_id)

    if not user:
        return 0

    return int(
        user.get(
            "pending_days",
            0,
        ) or 0
    )


# ============================================================
# STATISTICS
# ============================================================

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
                  AND subscription_until >= NOW()
                """
            )

            active_users = int(
                cur.fetchone()[0]
            )

            cur.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE subscription_until IS NOT NULL
                  AND subscription_until < NOW()
                """
            )

            expired_users = int(
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
                WHERE LOWER(status) IN (
                    'paid',
                    'success',
                    'successful',
                    'completed',
                    'approved'
                )
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
                WHERE LOWER(status) IN (
                    'paid',
                    'success',
                    'successful',
                    'completed',
                    'approved'
                )
                """
            )

            revenue = int(
                cur.fetchone()[0] or 0
            )

            return {
                "total_users": total_users,
                "active_users": active_users,
                "expired_users": expired_users,
                "trial_users": trial_users,
                "paid_payments": paid_payments,
                "revenue": revenue,
            }

    finally:
        conn.close()


# ============================================================
# SEARCH
# ============================================================

def search_users(
    query: str,
    limit: int = 50,
) -> list[dict]:

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
                    CAST(user_id AS TEXT)
                        ILIKE %s
                    OR COALESCE(username, '')
                        ILIKE %s
                    OR COALESCE(first_name, '')
                        ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (
                    f"%{query}%",
                    f"%{query}%",
                    f"%{query}%",
                    int(limit),
                ),
            )

            return [
                dict(row)
                for row in cur.fetchall()
            ]

    finally:
        conn.close()


# ============================================================
# DELETE USER
# ============================================================

def delete_user(
    user_id: int,
):

    conn = connect()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                DELETE FROM promocode_uses
                WHERE user_id = %s
                """,
                (int(user_id),),
            )

            cur.execute(
                """
                DELETE FROM payments
                WHERE user_id = %s
                """,
                (int(user_id),),
            )

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
        raise

    finally:
        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO
    )

    init_db()

    print(
        "☂️ ixxy VPN PostgreSQL database OK"
    )