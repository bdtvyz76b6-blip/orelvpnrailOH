import sqlite3
from datetime import datetime, timedelta

DB = "users.db"


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    return column_name in columns


def _ensure_column(conn, table_name: str, column_sql: str, column_name: str):
    if not _column_exists(conn, table_name, column_name):
        cur = conn.cursor()
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")


# =====================
# СОЗДАНИЕ ТАБЛИЦ
# =====================

def create_table():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,
        username TEXT,

        tariff TEXT DEFAULT 'Wi-Fi',
        link TEXT DEFAULT '',
        subscription_until TEXT DEFAULT '',

        trial_used INTEGER DEFAULT 0,
        pending_days INTEGER DEFAULT 0,

        wifi_active INTEGER DEFAULT 1,
        bs_active INTEGER DEFAULT 0,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (

        code TEXT PRIMARY KEY,
        days INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        photo TEXT,
        days INTEGER DEFAULT 30,
        status TEXT DEFAULT 'pending'
    )
    """)

    # Миграция старой базы: добавляем недостающие поля, если база была создана раньше
    _ensure_column(conn, "users", "username TEXT", "username")
    _ensure_column(conn, "users", "tariff TEXT DEFAULT 'Wi-Fi'", "tariff")
    _ensure_column(conn, "users", "link TEXT DEFAULT ''", "link")
    _ensure_column(conn, "users", "subscription_until TEXT DEFAULT ''", "subscription_until")
    _ensure_column(conn, "users", "trial_used INTEGER DEFAULT 0", "trial_used")
    _ensure_column(conn, "users", "pending_days INTEGER DEFAULT 0", "pending_days")
    _ensure_column(conn, "users", "wifi_active INTEGER DEFAULT 1", "wifi_active")
    _ensure_column(conn, "users", "bs_active INTEGER DEFAULT 0", "bs_active")
    _ensure_column(conn, "users", "created_at TEXT", "created_at")

    conn.commit()
    conn.close()


# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

def add_user(user_id, username=None):
    conn = connect()
    cur = conn.cursor()

    # Создаём пользователя, если его ещё нет
    cur.execute(
        """
        INSERT OR IGNORE INTO users (user_id, username)
        VALUES (?, ?)
        """,
        (user_id, username)
    )

    # Если пользователь уже есть — обновляем только username
    # Ничего больше не трогаем, чтобы не сбрасывать тариф и ссылку
    if username is not None:
        cur.execute(
            """
            UPDATE users
            SET username=?
            WHERE user_id=?
            """,
            (username, user_id)
        )

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

    user = cur.fetchone()
    conn.close()
    return user


def get_all_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    users = cur.fetchall()

    conn.close()
    return users


def get_user_ids():
    return [user["user_id"] for user in get_all_users()]


# =====================
# ССЫЛКА
# =====================

def save_subscription_link(user_id, link):
    add_user(user_id)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET link=?
        WHERE user_id=?
        """,
        (link, user_id)
    )

    conn.commit()
    conn.close()


def get_subscription_link(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT link
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    if result:
        return result["link"] or ""

    return ""


# =====================
# ВЫБОР ТАРИФА
# =====================

def set_pending_days(user_id, days):
    add_user(user_id)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET pending_days=?
        WHERE user_id=?
        """,
        (days, user_id)
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

    if result and result["pending_days"] and result["pending_days"] > 0:
        return result["pending_days"]

    return 30


# =====================
# ПОДПИСКА
# =====================

def activate_subscription(user_id, link, days):
    add_user(user_id)

    conn = connect()
    cur = conn.cursor()

    date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    cur.execute(
        """
        UPDATE users
        SET
            tariff='👑 Орёл VPN',
            link=?,
            subscription_until=?,
            bs_active=1,
            wifi_active=0,
            pending_days=0
        WHERE user_id=?
        """,
        (link, date, user_id)
    )

    conn.commit()
    conn.close()


def activate_trial(user_id, link):
    add_user(user_id)

    conn = connect()
    cur = conn.cursor()

    date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    cur.execute(
        """
        UPDATE users
        SET
            tariff='🎁 Пробный период',
            link=?,
            subscription_until=?,
            trial_used=1,
            bs_active=1,
            wifi_active=0
        WHERE user_id=?
        """,
        (link, date, user_id)
    )

    conn.commit()
    conn.close()


def check_trial(user_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT trial_used
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    return bool(result and result["trial_used"] == 1)


def get_expired_users():
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id
        FROM users
        WHERE subscription_until != ''
        AND subscription_until <= date('now')
        """
    )

    users = cur.fetchall()
    conn.close()

    return [row["user_id"] for row in users]


# =====================
# ОПЛАТЫ
# =====================

def add_payment(user_id, photo, days):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO payments (user_id, photo, days)
        VALUES (?, ?, ?)
        """,
        (user_id, photo, days)
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
        SELECT user_id, days
        FROM payments
        WHERE id=?
        """,
        (payment_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result


def approve_payment(payment_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE payments
        SET status='approved'
        WHERE id=?
        """,
        (payment_id,)
    )

    conn.commit()
    conn.close()


def get_payments():
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM payments
        WHERE status='pending'
        """
    )

    data = cur.fetchall()
    conn.close()

    return data


# =====================
# ПРОМОКОДЫ
# =====================

def create_promo(code, days):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO promocodes (code, days)
        VALUES (?, ?)
        """,
        (code, days)
    )

    conn.commit()
    conn.close()


def get_promos():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT * FROM promocodes")

    data = cur.fetchall()
    conn.close()

    return data


def delete_promo(code):
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
# СТАТИСТИКА
# =====================

def get_stats():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE bs_active=1
        """
    )
    active = cur.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "active": active
    }


# =====================
# УДАЛИТЬ ПОДПИСКУ
# =====================

def remove_bs(user_id):
    add_user(user_id)

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET
            tariff='Wi-Fi',
            link='',
            bs_active=0,
            wifi_active=1,
            subscription_until=''
        WHERE user_id=?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


# =====================
# ИНИЦИАЛИЗАЦИЯ
# =====================

create_table()