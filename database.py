import os
import psycopg2
from psycopg2 import IntegrityError
from datetime import datetime, timedelta, timezone, date


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")

MAX_PROMO_DAYS = 999_999_999_999
MAX_DATE = date(9999, 12, 31)


# =========================================================
# ВРЕМЯ
# =========================================================
#
# Москва = UTC+3
# Москва - 3 часа = UTC+0
#
# Поэтому используем UTC.
# Все даты подписок считаются по этой временной зоне.
# =========================================================

UTC = timezone.utc


def now_msk():
    """
    Время проекта:
    Москва - 3 часа = UTC.
    Возвращает timezone-aware datetime.
    """
    return datetime.now(UTC)


def today_msk():
    """
    Текущая дата проекта.

    Москва - 3 часа = UTC.
    Возвращает обычный date без timezone.
    """
    return now_msk().date()


def today_msk_string():
    """
    Текущая дата проекта в формате YYYY-MM-DD.
    """
    return today_msk().isoformat()


# =========================================================
# CONNECTION
# =========================================================

def connect():

    if not DATABASE_URL:
        raise RuntimeError(
            "❌ DATABASE_URL не задана в Environment Variables"
        )

    conn = psycopg2.connect(DATABASE_URL)

    # PostgreSQL-сессия тоже работает в UTC.
    with conn.cursor() as cur:
        cur.execute(
            "SET TIME ZONE 'UTC'"
        )

    return conn


# =========================================================
# СОЗДАНИЕ БАЗЫ
# =========================================================

def create_table():

    conn = connect()
    cur = conn.cursor()

    try:

        # =====================================================
        # USERS
        # =====================================================

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                subscription TEXT DEFAULT 'none',
                subscription_until TEXT DEFAULT '',
                subscription_link TEXT DEFAULT '',
                uuid TEXT DEFAULT '',
                trial_used INTEGER DEFAULT 0,
                pending_days INTEGER DEFAULT 0,
                notify INTEGER DEFAULT 1,
                accepted_terms INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                subscription_content TEXT DEFAULT ''
            )
        """)

        # =====================================================
        # МИГРАЦИЯ СТАРОЙ БАЗЫ
        # =====================================================

        cur.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS subscription_content TEXT DEFAULT ''
        """)

        # =====================================================
        # PAYMENTS
        # =====================================================

        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT,
                photo TEXT,
                days INTEGER,
                payment_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # =====================================================
        # PROMOCODES
        # =====================================================

        cur.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                days BIGINT
            )
        """)

        # =====================================================
        # ИСПОЛЬЗОВАННЫЕ ПРОМОКОДЫ
        # =====================================================

        cur.execute("""
            CREATE TABLE IF NOT EXISTS promocode_uses (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                code TEXT NOT NULL,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, code)
            )
        """)

        # =====================================================
        # УНИКАЛЬНЫЙ CASHERA PAYMENT ID
        # =====================================================

        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_payments_payment_id_unique
            ON payments(payment_id)
            WHERE payment_id IS NOT NULL
              AND payment_id <> ''
        """)

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# USERS
# =========================================================

def add_user(
    user_id,
    username=None,
    first_name=None
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            INSERT INTO users (
                user_id,
                username,
                first_name
            )
            VALUES (%s, %s, %s)

            ON CONFLICT (user_id)
            DO UPDATE SET
                username=EXCLUDED.username,
                first_name=EXCLUDED.first_name
        """, (
            user_id,
            username,
            first_name
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_user(user_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                user_id,
                username,
                first_name,
                subscription,
                subscription_until,
                subscription_link,
                uuid,
                trial_used,
                pending_days,
                notify,
                accepted_terms,
                created_at
            FROM users
            WHERE user_id=%s
        """, (user_id,))

        return cur.fetchone()

    finally:

        cur.close()
        conn.close()


def get_all_users():

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT
                user_id,
                username,
                first_name,
                subscription,
                subscription_until,
                subscription_link,
                uuid,
                trial_used,
                pending_days,
                notify,
                accepted_terms,
                created_at
            FROM users
            ORDER BY created_at DESC
        """)

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# SUBSCRIPTION CONTENT
# =========================================================

def save_subscription_content(
    user_id,
    content
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET subscription_content=%s
            WHERE user_id=%s
        """, (
            content,
            user_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_subscription_content(user_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT subscription_content
            FROM users
            WHERE user_id=%s
        """, (user_id,))

        result = cur.fetchone()

        if result:
            return result[0] or ""

        return ""

    finally:

        cur.close()
        conn.close()


# =========================================================
# TERMS
# =========================================================

def has_accepted_terms(user_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT accepted_terms
            FROM users
            WHERE user_id=%s
        """, (user_id,))

        result = cur.fetchone()

        return bool(
            result and result[0] == 1
        )

    finally:

        cur.close()
        conn.close()


def accept_terms(user_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET accepted_terms=1
            WHERE user_id=%s
        """, (user_id,))

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# PENDING DAYS
# =========================================================

def set_pending_days(
    user_id,
    days
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET pending_days=%s
            WHERE user_id=%s
        """, (
            days,
            user_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_pending_days(user_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT pending_days
            FROM users
            WHERE user_id=%s
        """, (user_id,))

        result = cur.fetchone()

        if result:
            return result[0] or 0

        return 0

    finally:

        cur.close()
        conn.close()


# =========================================================
# SUBSCRIPTION LINK
# =========================================================

def save_subscription_link(
    user_id,
    link
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET subscription_link=%s
            WHERE user_id=%s
        """, (
            link,
            user_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_subscription_link(user_id):

    user = get_user(user_id)

    if user:
        return user[5] or ""

    return ""


# =========================================================
# РАЗБОР ДАТЫ ПОДПИСКИ
# =========================================================

def parse_subscription_date(value):
    """
    Безопасно превращает дату подписки в date.

    Поддерживает:
    - YYYY-MM-DD
    - datetime
    - date
    - None
    - пустую строку
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except (
        ValueError,
        TypeError
    ):
        return None


# =========================================================
# РАСЧЁТ ДАТЫ ПОДПИСКИ
# =========================================================

def calculate_subscription_date(
    current_until,
    days
):

    days = int(days)

    if days < 1:
        raise ValueError(
            "Количество дней должно быть больше 0"
        )

    if days > MAX_PROMO_DAYS:
        raise ValueError(
            "Слишком большое количество дней"
        )

    today = today_msk()

    start_date = today

    old_date = parse_subscription_date(
        current_until
    )

    # Если подписка ещё активна,
    # продолжаем её от старой даты.
    if old_date and old_date >= today:
        start_date = old_date

    # Защита от огромных значений.
    if days >= 2_900_000:
        return "9999-12-31"

    try:

        new_date = (
            start_date +
            timedelta(days=days)
        )

        if new_date > MAX_DATE:
            return "9999-12-31"

        return new_date.isoformat()

    except (
        OverflowError,
        ValueError
    ):

        return "9999-12-31"


# =========================================================
# АКТИВАЦИЯ ПОДПИСКИ
# =========================================================

def activate_subscription(
    user_id,
    link,
    days
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT subscription_until
            FROM users
            WHERE user_id=%s
        """, (user_id,))

        user = cur.fetchone()

        current_until = (
            user[0]
            if user
            else ""
        )

        new_date = calculate_subscription_date(
            current_until,
            days
        )

        cur.execute("""
            UPDATE users
            SET
                subscription='vip',
                subscription_until=%s,
                subscription_link=%s,
                pending_days=0
            WHERE user_id=%s
        """, (
            new_date,
            link,
            user_id
        ))

        conn.commit()

        return new_date

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПЛАТНАЯ ПОДПИСКА
# =========================================================

def activate_paid_subscription(
    user_id,
    link,
    days
):

    return activate_subscription(
        user_id=user_id,
        link=link,
        days=days
    )


# =========================================================
# TRIAL
# =========================================================

def check_trial(user_id):

    user = get_user(user_id)

    if not user:
        return False

    return user[7] == 1


def activate_trial(
    user_id,
    link
):

    new_date = (
        today_msk()
        + timedelta(days=3)
    ).isoformat()

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET
                subscription='trial',
                subscription_until=%s,
                subscription_link=%s,
                trial_used=1
            WHERE user_id=%s
        """, (
            new_date,
            link,
            user_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# PAYMENTS
# =========================================================

def add_payment(
    user_id,
    photo,
    days
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            INSERT INTO payments (
                user_id,
                photo,
                days
            )
            VALUES (%s, %s, %s)
            RETURNING id
        """, (
            user_id,
            photo,
            days
        ))

        payment_id = cur.fetchone()[0]

        conn.commit()

        return payment_id

    finally:

        cur.close()
        conn.close()


def get_payment(payment_id):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT *
            FROM payments
            WHERE id=%s
        """, (payment_id,))

        return cur.fetchone()

    finally:

        cur.close()
        conn.close()


def get_payments():

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT *
            FROM payments
            ORDER BY id DESC
        """)

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# CASHERA PAYMENT ID
# =========================================================

def save_payment_id(
    user_id,
    payment_id
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE payments
            SET payment_id=%s
            WHERE id=(
                SELECT id
                FROM payments
                WHERE user_id=%s
                  AND (
                      payment_id IS NULL
                      OR payment_id=''
                  )
                ORDER BY id DESC
                LIMIT 1
            )
        """, (
            str(payment_id),
            user_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_payment_by_payment_id(
    payment_id
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT *
            FROM payments
            WHERE payment_id=%s
            LIMIT 1
        """, (
            str(payment_id),
        ))

        return cur.fetchone()

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПРОВЕРКА ПОВТОРНОГО CASHERA WEBHOOK
# =========================================================

def payment_already_paid(
    payment_id
):

    if not payment_id:
        return False

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT id
            FROM payments
            WHERE payment_id=%s
              AND status='paid'
            LIMIT 1
        """, (
            str(payment_id),
        ))

        return cur.fetchone() is not None

    finally:

        cur.close()
        conn.close()


# =========================================================
# ОТМЕТИТЬ CASHERA ПЛАТЁЖ ОПЛАЧЕННЫМ
# =========================================================

def mark_payment_paid(
    payment_id
):

    if not payment_id:
        return False

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE payments
            SET status='paid'
            WHERE payment_id=%s
              AND status!='paid'
        """, (
            str(payment_id),
        ))

        changed = cur.rowcount

        conn.commit()

        return changed > 0

    finally:

        cur.close()
        conn.close()


# =========================================================
# БЕЗОПАСНАЯ ОБРАБОТКА ОПЛАЧЕННОГО ПЛАТЕЖА
# =========================================================

def process_paid_payment(
    payment_id
):

    if not payment_id:
        raise ValueError(
            "payment_id не указан"
        )

    conn = connect()
    cur = conn.cursor()

    try:

        # Блокируем платёж.
        cur.execute("""
            SELECT
                id,
                user_id,
                days,
                status
            FROM payments
            WHERE payment_id=%s
            FOR UPDATE
        """, (
            str(payment_id),
        ))

        payment = cur.fetchone()

        if not payment:
            raise ValueError(
                "Платёж не найден"
            )

        db_payment_id = payment[0]
        user_id = payment[1]
        days = int(payment[2] or 0)
        status = payment[3]

        # Если webhook пришёл повторно,
        # второй раз подписку не продлеваем.
        if status == "paid":

            cur.execute("""
                SELECT subscription_until
                FROM users
                WHERE user_id=%s
            """, (user_id,))

            user = cur.fetchone()

            conn.commit()

            return {
                "payment_id": db_payment_id,
                "user_id": user_id,
                "days": days,
                "status": "paid",
                "already_paid": True,
                "new_date": (
                    user[0]
                    if user
                    else ""
                )
            }

        # Блокируем пользователя.
        cur.execute("""
            SELECT subscription_until
            FROM users
            WHERE user_id=%s
            FOR UPDATE
        """, (user_id,))

        user = cur.fetchone()

        if not user:
            raise ValueError(
                f"Пользователь {user_id} не найден"
            )

        current_until = user[0] or ""

        new_date = calculate_subscription_date(
            current_until,
            days
        )

        # Активируем подписку.
        cur.execute("""
            UPDATE users
            SET
                subscription='vip',
                subscription_until=%s,
                pending_days=0
            WHERE user_id=%s
        """, (
            new_date,
            user_id
        ))

        # Помечаем платёж оплаченным.
        cur.execute("""
            UPDATE payments
            SET status='paid'
            WHERE id=%s
        """, (
            db_payment_id,
        ))

        conn.commit()

        return {
            "payment_id": db_payment_id,
            "user_id": user_id,
            "days": days,
            "status": "paid",
            "already_paid": False,
            "new_date": new_date
        }

    except Exception:

        conn.rollback()
        raise

    finally:

        cur.close()
        conn.close()


# =========================================================
# STARS
# =========================================================

def add_stars_payment(
    user_id,
    amount,
    days,
    payment_id
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            INSERT INTO payments (
                user_id,
                days,
                payment_id,
                status
            )
            VALUES (%s, %s, %s, %s)
        """, (
            user_id,
            days,
            str(payment_id),
            "paid"
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# ОТКЛЮЧЕНИЕ
# =========================================================

def disable_subscription(
    user_id
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE users
            SET
                subscription='none',
                subscription_until='',
                subscription_link=''
            WHERE user_id=%s
        """, (user_id,))

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# СТАТУС ПЛАТЕЖА
# =========================================================

def update_payment_status(
    payment_id,
    status
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            UPDATE payments
            SET status=%s
            WHERE id=%s
        """, (
            status,
            payment_id
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_user_payments(
    user_id
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT *
            FROM payments
            WHERE user_id=%s
            ORDER BY id DESC
        """, (user_id,))

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПРОМОКОДЫ
# =========================================================

def add_promocode(
    code,
    days
):

    code = str(code).strip().upper()
    days = int(days)

    if (
        days < 1
        or days > MAX_PROMO_DAYS
    ):

        raise ValueError(
            f"Количество дней должно быть "
            f"от 1 до {MAX_PROMO_DAYS}"
        )

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            INSERT INTO promocodes (
                code,
                days
            )
            VALUES (%s, %s)

            ON CONFLICT (code)
            DO UPDATE SET
                days=EXCLUDED.days
        """, (
            code,
            days
        ))

        conn.commit()

    finally:

        cur.close()
        conn.close()


def get_promocode(
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT days
            FROM promocodes
            WHERE code=%s
        """, (code,))

        result = cur.fetchone()

        if result:
            return result[0]

        return 0

    finally:

        cur.close()
        cur.close() if False else None
        conn.close()


# =========================================================
# ПРОМОКОД — 1 РАЗ
# =========================================================

def use_promocode(
    user_id,
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    try:

        # -------------------------------------------------
        # Пользователь
        # -------------------------------------------------

        cur.execute("""
            SELECT subscription_until
            FROM users
            WHERE user_id=%s
            FOR UPDATE
        """, (user_id,))

        user = cur.fetchone()

        if not user:

            conn.rollback()

            return {
                "success": False,
                "reason": "user_not_found"
            }

        # -------------------------------------------------
        # Промокод
        # -------------------------------------------------

        cur.execute("""
            SELECT days
            FROM promocodes
            WHERE code=%s
        """, (code,))

        promo = cur.fetchone()

        if not promo:

            conn.rollback()

            return {
                "success": False,
                "reason": "not_found"
            }

        days = int(promo[0])

        # -------------------------------------------------
        # Проверка дней
        # -------------------------------------------------

        if (
            days < 1
            or days > MAX_PROMO_DAYS
        ):

            conn.rollback()

            return {
                "success": False,
                "reason": "invalid_days"
            }

        # -------------------------------------------------
        # Проверяем использование
        # -------------------------------------------------

        cur.execute("""
            SELECT id
            FROM promocode_uses
            WHERE user_id=%s
              AND code=%s
        """, (
            user_id,
            code
        ))

        already_used = cur.fetchone()

        if already_used:

            conn.rollback()

            return {
                "success": False,
                "reason": "already_used"
            }

        # -------------------------------------------------
        # Новая дата
        # -------------------------------------------------

        new_date = calculate_subscription_date(
            user[0],
            days
        )

        # -------------------------------------------------
        # Обновляем подписку
        # -------------------------------------------------

        cur.execute("""
            UPDATE users
            SET
                subscription='vip',
                subscription_until=%s
            WHERE user_id=%s
        """, (
            new_date,
            user_id
        ))

        # -------------------------------------------------
        # Записываем использование
        # -------------------------------------------------

        cur.execute("""
            INSERT INTO promocode_uses (
                user_id,
                code
            )
            VALUES (%s, %s)
        """, (
            user_id,
            code
        ))

        conn.commit()

        return {
            "success": True,
            "reason": "success",
            "days": days,
            "date": new_date
        }

    except IntegrityError:

        conn.rollback()

        return {
            "success": False,
            "reason": "already_used"
        }

    except Exception as e:

        conn.rollback()

        print(
            f"❌ USE PROMO ERROR: {e}"
        )

        return {
            "success": False,
            "reason": "error"
        }

    finally:

        cur.close()
        conn.close()


# =========================================================
# ВСЕ ПРОМОКОДЫ
# =========================================================

def get_promocodes():

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT code, days
            FROM promocodes
            ORDER BY code
        """)

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# УДАЛИТЬ ПРОМОКОД
# =========================================================

def delete_promocode(
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            DELETE FROM promocodes
            WHERE code=%s
        """, (code,))

        conn.commit()

    finally:

        cur.close()
        conn.close()


# =========================================================
# ИСПОЛЬЗОВАЛ ЛИ
# =========================================================

def has_used_promocode(
    user_id,
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT id
            FROM promocode_uses
            WHERE user_id=%s
              AND code=%s
        """, (
            user_id,
            code
        ))

        return cur.fetchone() is not None

    finally:

        cur.close()
        conn.close()


# =========================================================
# ID ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# =========================================================

def get_user_ids():

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT user_id
            FROM users
        """)

        return [
            row[0]
            for row in cur.fetchall()
        ]

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПРОСРОЧЕННЫЕ
# =========================================================

def get_expired_users():

    conn = connect()
    cur = conn.cursor()

    try:

        today = today_msk_string()

        cur.execute("""
            SELECT *
            FROM users
            WHERE subscription_until != ''
              AND subscription_until < %s
        """, (today,))

        return cur.fetchall()

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПРОДЛЕНИЕ ПОДПИСКИ
# =========================================================

def extend_subscription(
    user_id,
    days
):

    conn = connect()
    cur = conn.cursor()

    try:

        cur.execute("""
            SELECT subscription_until
            FROM users
            WHERE user_id=%s
            FOR UPDATE
        """, (user_id,))

        result = cur.fetchone()

        current_until = (
            result[0]
            if result
            else ""
        )

        new_date = calculate_subscription_date(
            current_until,
            days
        )

        cur.execute("""
            UPDATE users
            SET
                subscription='vip',
                subscription_until=%s
            WHERE user_id=%s
        """, (
            new_date,
            user_id
        ))

        conn.commit()

        return new_date

    finally:

        cur.close()
        conn.close()


# =========================================================
# ПРОВЕРКА ПОДПИСКИ
# =========================================================

def subscription_active(
    user_id
):

    user = get_user(user_id)

    if not user:
        return False

    until = user[4]

    expire_date = parse_subscription_date(
        until
    )

    if not expire_date:
        return False

    today = today_msk()

    return expire_date >= today


# =========================================================
# АВТООТКЛЮЧЕНИЕ
# =========================================================

def check_expired_subscriptions():

    conn = connect()
    cur = conn.cursor()

    try:

        today = today_msk_string()

        cur.execute("""
            UPDATE users
            SET
                subscription='none',
                subscription_link=''
            WHERE subscription_until != ''
              AND subscription_until < %s
              AND subscription != 'none'
        """, (today,))

        changed = cur.rowcount

        conn.commit()

        return changed

    finally:

        cur.close()
        conn.close()


# =========================================================
# ОСТАТОК ДНЕЙ
# =========================================================

def get_days_left(
    user_id
):

    user = get_user(user_id)

    if not user:
        return 0

    until = user[4]

    expire_date = parse_subscription_date(
        until
    )

    if not expire_date:
        return 0

    today = today_msk()

    days = (
        expire_date - today
    ).days

    return max(days, 0)


# =========================================================
# ПРОВЕРКА ПРИ ВХОДЕ
# =========================================================

def check_user_subscription(
    user_id
):

    user = get_user(user_id)

    if not user:
        return False

    until = user[4]

    expire_date = parse_subscription_date(
        until
    )

    if not expire_date:
        return False

    today = today_msk()

    if expire_date < today:

        disable_subscription(
            user_id
        )

        return False

    return True


# =========================================================
# ИНИЦИАЛИЗАЦИЯ
# =========================================================

try:

    create_table()

except Exception as e:

    print(
        f"⚠️ Ошибка создания таблиц: {e}"
    )