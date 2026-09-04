import os
import psycopg2
from psycopg2 import IntegrityError
from datetime import datetime, timedelta


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL", "")

MAX_PROMO_DAYS = 999_999_999_999
MAX_DATE = datetime(9999, 12, 31)


def connect():
    if not DATABASE_URL:
        raise RuntimeError(
            "❌ DATABASE_URL не задана в Environment Variables"
        )

    return psycopg2.connect(DATABASE_URL)


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
            DO NOTHING
        """, (
            user_id,
            username,
            first_name
        ))

        cur.execute("""
            UPDATE users
            SET
                username=%s,
                first_name=%s
            WHERE user_id=%s
        """, (
            username,
            first_name,
            user_id
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

    now = datetime.now()

    start_date = now

    if current_until:

        try:

            old_date = datetime.strptime(
                str(current_until),
                "%Y-%m-%d"
            )

            # Если текущая подписка ещё активна,
            # добавляем дни к её окончанию.

            if old_date.date() >= now.date():

                start_date = old_date

        except Exception:

            start_date = now

    # Огромные значения переводим
    # на максимальную дату.

    if days >= 2_900_000:

        return "9999-12-31"

    try:

        new_date = (
            start_date +
            timedelta(days=days)
        )

        if new_date > MAX_DATE:

            return "9999-12-31"

        return new_date.strftime(
            "%Y-%m-%d"
        )

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

        # Получаем текущую дату окончания

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

        # Рассчитываем новую дату

        date = calculate_subscription_date(
            current_until,
            days
        )

        # Активируем VIP

        cur.execute("""
            UPDATE users
            SET
                subscription='vip',
                subscription_until=%s,
                subscription_link=%s,
                pending_days=0
            WHERE user_id=%s
        """, (
            date,
            link,
            user_id
        ))

        conn.commit()

        return date

    finally:

        cur.close()
        conn.close()


# =========================================================
# УДОБНАЯ ФУНКЦИЯ ДЛЯ ПЛАТНОЙ ПОДПИСКИ
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

    date = (
        datetime.now()
        + timedelta(days=3)
    ).strftime("%Y-%m-%d")

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
            date,
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

        result = cur.fetchone()

        return result is not None

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
            payment_id,
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

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

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

    if not until:
        return False

    try:

        expire_date = datetime.strptime(
            str(until),
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        return expire_date >= today

    except Exception:

        return False


# =========================================================
# АВТООТКЛЮЧЕНИЕ
# =========================================================

def check_expired_subscriptions():

    conn = connect()
    cur = conn.cursor()

    try:

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

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

    if not until:
        return 0

    try:

        expire_date = datetime.strptime(
            str(until),
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        days = (
            expire_date - today
        ).days

        return max(days, 0)

    except Exception:

        return 0


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

    if not until:
        return False

    try:

        expire_date = datetime.strptime(
            str(until),
            "%Y-%m-%d"
        ).date()

        today = datetime.now().date()

        if expire_date < today:

            disable_subscription(
                user_id
            )

            return False

        return True

    except Exception:

        return False


# =========================================================
# ИНИЦИАЛИЗАЦИЯ
# =========================================================

try:

    create_table()

except Exception as e:

    print(
        f"⚠️ Ошибка создания таблиц: {e}"
    )