import sqlite3

from datetime import datetime, timedelta


# =====================
# DATABASE
# =====================

DB = "/data/users.db"


def connect():

    return sqlite3.connect(DB)


# =====================
# СОЗДАНИЕ БАЗЫ
# =====================

def create_table():

    conn = connect()
    cur = conn.cursor()

    # =====================
    # USERS
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,

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

        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================
    # PAYMENTS
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        photo TEXT,

        days INTEGER,

        payment_id TEXT,

        status TEXT DEFAULT 'pending',

        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)

    # =====================
    # PROMOCODES
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (

        code TEXT PRIMARY KEY,

        days INTEGER

    )
    """)

    # =====================
    # ИСПОЛЬЗОВАННЫЕ ПРОМОКОДЫ
    # =====================

    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocode_uses (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,

        code TEXT NOT NULL,

        used_at TEXT DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(user_id, code)

    )
    """)

    conn.commit()
    conn.close()


# =====================
# USERS
# =====================

def add_user(
    user_id,
    username=None,
    first_name=None
):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (
        user_id,
        username,
        first_name
    )

    VALUES (?,?,?)

    """,
    (
        user_id,
        username,
        first_name
    ))

    # Обновляем имя и username,
    # если пользователь уже существует
    cur.execute("""
    UPDATE users

    SET
        username=?,
        first_name=?

    WHERE user_id=?

    """,
    (
        username,
        first_name,
        user_id
    ))

    conn.commit()
    conn.close()


def get_user(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result


def get_all_users():

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM users
        ORDER BY created_at DESC
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


# =====================
# TERMS
# =====================

def has_accepted_terms(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT accepted_terms
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    if result and result[0] == 1:

        return True

    return False


def accept_terms(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users

        SET accepted_terms=1

        WHERE user_id=?

        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =====================
# PENDING DAYS
# =====================

def set_pending_days(
    user_id,
    days
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users

        SET pending_days=?

        WHERE user_id=?

        """,
        (
            days,
            user_id
        )
    )

    conn.commit()
    conn.close()


def get_pending_days(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT pending_days
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    if result:

        return result[0]

    return 0


# =====================
# SUBSCRIPTION LINK
# =====================

def save_subscription_link(
    user_id,
    link
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users

        SET subscription_link=?

        WHERE user_id=?

        """,
        (
            link,
            user_id
        )
    )

    conn.commit()
    conn.close()


def get_subscription_link(user_id):

    user = get_user(user_id)

    if user:

        return user[5]

    return ""


# =====================
# АКТИВАЦИЯ ПОДПИСКИ
# =====================

def activate_subscription(
    user_id,
    link,
    days
):

    conn = connect()
    cur = conn.cursor()

    start = datetime.now()

    user = get_user(user_id)

    if user and user[4]:

        try:

            old = datetime.strptime(
                user[4],
                "%Y-%m-%d"
            )

            if old > start:

                start = old

        except Exception:

            pass

    date = (
        start +
        timedelta(days=days)
    ).strftime(
        "%Y-%m-%d"
    )

    cur.execute(
        """
        UPDATE users

        SET
            subscription='vip',
            subscription_until=?,
            subscription_link=?,
            pending_days=0

        WHERE user_id=?

        """,
        (
            date,
            link,
            user_id
        )
    )

    conn.commit()
    conn.close()


# =====================
# TRIAL
# =====================

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
        +
        timedelta(days=3)
    ).strftime(
        "%Y-%m-%d"
    )

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users

        SET
            subscription=?,
            subscription_until=?,
            subscription_link=?,
            trial_used=1

        WHERE user_id=?

        """,
        (
            "trial",
            date,
            link,
            user_id
        )
    )

    conn.commit()
    conn.close()


# =====================
# PAYMENTS
# =====================

def add_payment(
    user_id,
    photo,
    days
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO payments
        (
            user_id,
            photo,
            days
        )

        VALUES (?,?,?)

        """,
        (
            user_id,
            photo,
            days
        )
    )

    payment_id = cur.lastrowid

    conn.commit()
    conn.close()

    return payment_id


def get_payment(payment_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM payments
        WHERE id=?
        """,
        (payment_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result


def get_payments():

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM payments
        ORDER BY id DESC
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


# =====================
# STARS
# =====================

def add_stars_payment(
    user_id,
    amount,
    days,
    payment_id
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO payments
        (
            user_id,
            days,
            payment_id,
            status
        )

        VALUES (?,?,?,?)

        """,
        (
            user_id,
            days,
            payment_id,
            "paid"
        )
    )

    conn.commit()
    conn.close()


# =====================
# ОТКЛЮЧЕНИЕ
# =====================

def disable_subscription(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users

        SET
            subscription='none',
            subscription_until='',
            subscription_link=''

        WHERE user_id=?

        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =====================
# СТАТУС ПЛАТЕЖА
# =====================

def update_payment_status(
    payment_id,
    status
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE payments

        SET status=?

        WHERE id=?

        """,
        (
            status,
            payment_id
        )
    )

    conn.commit()
    conn.close()


def get_user_payments(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM payments
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (
            user_id,
        )
    )

    result = cur.fetchall()

    conn.close()

    return result


# =====================
# ПРОМОКОДЫ
# =====================

def add_promocode(
    code,
    days
):

    code = str(code).strip().upper()
    days = int(days)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO promocodes
        (
            code,
            days
        )

        VALUES (?,?)

        """,
        (
            code,
            days
        )
    )

    conn.commit()
    conn.close()


def get_promocode(code):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT days

        FROM promocodes

        WHERE code=?

        """,
        (
            code,
        )
    )

    result = cur.fetchone()

    conn.close()

    if result:

        return result[0]

    return 0


# =====================
# ПРОМОКОД — 1 РАЗ
# =====================

def use_promocode(
    user_id,
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    try:

        # =====================
        # ПРОВЕРЯЕМ ПОЛЬЗОВАТЕЛЯ
        # =====================

        cur.execute(
            """
            SELECT subscription_until
            FROM users
            WHERE user_id=?
            """,
            (user_id,)
        )

        user = cur.fetchone()

        if not user:

            conn.rollback()

            return {
                "success": False,
                "reason": "user_not_found"
            }

        # =====================
        # ПРОВЕРЯЕМ ПРОМОКОД
        # =====================

        cur.execute(
            """
            SELECT days
            FROM promocodes
            WHERE code=?
            """,
            (code,)
        )

        promo = cur.fetchone()

        if not promo:

            conn.rollback()

            return {
                "success": False,
                "reason": "not_found"
            }

        days = int(promo[0])

        # =====================
        # ПРОВЕРЯЕМ ИСПОЛЬЗОВАНИЕ
        # =====================

        cur.execute(
            """
            SELECT id
            FROM promocode_uses
            WHERE user_id=?
            AND code=?
            """,
            (
                user_id,
                code
            )
        )

        already_used = cur.fetchone()

        if already_used:

            conn.rollback()

            return {
                "success": False,
                "reason": "already_used"
            }

        # =====================
        # ТЕКУЩАЯ ДАТА
        # =====================

        now = datetime.now()

        current_until = user[0]

        start_date = now

        if current_until:

            try:

                old_date = datetime.strptime(
                    current_until,
                    "%Y-%m-%d"
                )

                # Если подписка ещё действует,
                # добавляем дни к её окончанию
                if old_date > now:

                    start_date = old_date

            except Exception:

                start_date = now

        # =====================
        # НОВАЯ ДАТА
        # =====================

        new_date = (
            start_date +
            timedelta(days=days)
        ).strftime(
            "%Y-%m-%d"
        )

        # =====================
        # ОБНОВЛЯЕМ ПОДПИСКУ
        # =====================

        cur.execute(
            """
            UPDATE users

            SET
                subscription='vip',
                subscription_until=?

            WHERE user_id=?

            """,
            (
                new_date,
                user_id
            )
        )

        # =====================
        # ЗАПИСЫВАЕМ ИСПОЛЬЗОВАНИЕ
        # =====================

        cur.execute(
            """
            INSERT INTO promocode_uses
            (
                user_id,
                code
            )

            VALUES (?,?)

            """,
            (
                user_id,
                code
            )
        )

        conn.commit()

        return {
            "success": True,
            "reason": "success",
            "days": days,
            "date": new_date
        }

    except sqlite3.IntegrityError:

        # Защита от ситуации,
        # когда два запроса одновременно
        # пытаются использовать один промокод

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

        conn.close()


# =====================
# ВСЕ ПРОМОКОДЫ
# =====================

def get_promocodes():

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT code, days
        FROM promocodes
        ORDER BY code
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


# =====================
# УДАЛИТЬ ПРОМОКОД
# =====================

def delete_promocode(code):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM promocodes
        WHERE code=?
        """,
        (code,)
    )

    conn.commit()
    conn.close()


# =====================
# ИСПОЛЬЗОВАЛ ЛИ
# =====================

def has_used_promocode(
    user_id,
    code
):

    code = str(code).strip().upper()

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM promocode_uses

        WHERE user_id=?
        AND code=?

        """,
        (
            user_id,
            code
        )
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


# =====================
# ID ВСЕХ ПОЛЬЗОВАТЕЛЕЙ
# =====================

def get_user_ids():

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        """
    )

    result = [
        row[0]
        for row in cur.fetchall()
    ]

    conn.close()

    return result


# =====================
# ПРОСРОЧЕННЫЕ
# =====================

def get_expired_users():

    conn = connect()
    cur = conn.cursor()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cur.execute(
        """
        SELECT *
        FROM users

        WHERE subscription_until != ''

        AND subscription_until < ?

        """,
        (today,)
    )

    result = cur.fetchall()

    conn.close()

    return result


# =====================
# ПРОДЛЕНИЕ ПОДПИСКИ
# =====================

def extend_subscription(
    user_id,
    days
):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT subscription_until
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    if result and result[0]:

        try:

            old_date = datetime.strptime(
                result[0],
                "%Y-%m-%d"
            )

            if old_date < datetime.now():

                old_date = datetime.now()

        except Exception:

            old_date = datetime.now()

    else:

        old_date = datetime.now()

    new_date = (
        old_date +
        timedelta(days=days)
    ).strftime(
        "%Y-%m-%d"
    )

    cur.execute(
        """
        UPDATE users

        SET
            subscription='vip',
            subscription_until=?

        WHERE user_id=?

        """,
        (
            new_date,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return new_date


# =====================
# ПРОВЕРКА ПОДПИСКИ
# =====================

def subscription_active(user_id):

    user = get_user(user_id)

    if not user:

        return False

    until = user[4]

    if not until:

        return False

    try:

        date = datetime.strptime(
            until,
            "%Y-%m-%d"
        )

        return date > datetime.now()

    except Exception:

        return False


# =====================
# АВТООТКЛЮЧЕНИЕ
# =====================

def check_expired_subscriptions():

    conn = connect()
    cur = conn.cursor()

    now = datetime.now().strftime(
        "%Y-%m-%d"
    )

    cur.execute(
        """
        UPDATE users

        SET
            subscription='none',
            subscription_link=''

        WHERE subscription_until < ?

        AND subscription != 'none'

        """,
        (
            now,
        )
    )

    conn.commit()
    conn.close()


# =====================
# ОСТАТОК ДНЕЙ
# =====================

def get_days_left(user_id):

    user = get_user(user_id)

    if not user:

        return 0

    if not user[4]:

        return 0

    try:

        date = datetime.strptime(
            user[4],
            "%Y-%m-%d"
        )

        days = (
            date - datetime.now()
        ).days

        if days < 0:

            return 0

        return days

    except Exception:

        return 0


# =====================
# ПРОВЕРКА ПРИ ВХОДЕ
# =====================

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

        date = datetime.strptime(
            until,
            "%Y-%m-%d"
        )

        if date <= datetime.now():

            disable_subscription(
                user_id
            )

            return False

        return True

    except Exception:

        return False