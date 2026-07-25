import sqlite3
import uuid

from datetime import datetime, timedelta


DB = "users.db"


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn



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

        uuid TEXT,

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


    conn.commit()
    conn.close()



# =====================
# UUID
# =====================

def generate_uuid():

    return str(uuid.uuid4())



def get_user_uuid(user_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT uuid
        FROM users
        WHERE user_id=?
        """,
        (user_id,)
    )


    result = cur.fetchone()

    conn.close()


    if result:
        return result["uuid"]

    return None



# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

def add_user(user_id, username=None):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT OR IGNORE INTO users
        (
            user_id,
            username,
            uuid
        )

        VALUES (?,?,?)

        """,
        (
            user_id,
            username,
            generate_uuid()
        )
    )


    if username:

        cur.execute(
            """
            UPDATE users

            SET username=?

            WHERE user_id=?

            """,
            (
                username,
                user_id
            )
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

    cur.execute(
        "SELECT * FROM users"
    )

    users = cur.fetchall()

    conn.close()

    return users



def get_user_ids():

    return [
        user["user_id"]
        for user in get_all_users()
    ]



# =====================
# ССЫЛКИ
# =====================

def save_subscription_link(user_id, link):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users

        SET link=?

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
# ПОДПИСКА
# =====================

def activate_subscription(user_id, link, days):

    conn = connect()
    cur = conn.cursor()


    date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime(
        "%Y-%m-%d"
    )


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
        (
            link,
            date,
            user_id
        )
    )


    conn.commit()
    conn.close()



def activate_trial(user_id, link):

    conn = connect()
    cur = conn.cursor()


    date = (
        datetime.now()
        +
        timedelta(days=3)
    ).strftime(
        "%Y-%m-%d"
    )


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
        (
            link,
            date,
            user_id
        )
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


    return bool(
        result and result["trial_used"] == 1
    )



# =====================
# ОПЛАТЫ
# =====================

def add_payment(user_id, photo, days):

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
        SELECT user_id, days

        FROM payments

        WHERE id=?

        """,
        (payment_id,)
    )


    result = cur.fetchone()

    conn.close()


    return result



# =====================
# УДАЛЕНИЕ ПОДПИСКИ
# =====================

def remove_bs(user_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users

        SET

        tariff='Wi-Fi',

        link='',

        subscription_until='',

        bs_active=0,

        wifi_active=1


        WHERE user_id=?

        """,
        (user_id,)
    )


    conn.commit()
    conn.close()