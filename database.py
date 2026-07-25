import sqlite3

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


    # Пользователи
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,

        username TEXT DEFAULT '',

        first_name TEXT DEFAULT '',


        tariff TEXT DEFAULT 'Wi-Fi',

        link TEXT DEFAULT '',


        subscription_until TEXT DEFAULT '',


        status TEXT DEFAULT 'active',


        servers_count INTEGER DEFAULT 5,


        devices_limit INTEGER DEFAULT 1,

        devices_count INTEGER DEFAULT 0,


        trial_used INTEGER DEFAULT 0,


        pending_days INTEGER DEFAULT 0,


        wifi_active INTEGER DEFAULT 1,

        bs_active INTEGER DEFAULT 0,


        notify_3_days INTEGER DEFAULT 0,

        notify_expired INTEGER DEFAULT 0,


        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    # Платежи
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER,


        photo TEXT,


        days INTEGER DEFAULT 30,


        amount INTEGER DEFAULT 0,


        status TEXT DEFAULT 'pending',


        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    # Промокоды
    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (

        code TEXT PRIMARY KEY,


        days INTEGER,


        used INTEGER DEFAULT 0,


        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    # Уведомления
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        user_id INTEGER,


        type TEXT,


        sent INTEGER DEFAULT 0,


        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    conn.commit()
    conn.close()



# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

def add_user(user_id, username="", first_name=""):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
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
# ССЫЛКА
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

    user = get_user(user_id)


    if user:

        return user["link"]


    return ""



# =====================
# ПОДПИСКА
# =====================

def activate_subscription(user_id, link, days):

    date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime(
        "%Y-%m-%d"
    )


    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users

        SET

        tariff='👑 Орёл VPN VIP',

        link=?,

        subscription_until=?,

        status='active',

        bs_active=1,

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

        tariff='🎁 Пробный период',

        link=?,

        subscription_until=?,

        trial_used=1,

        status='active',

        bs_active=1


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

    user = get_user(user_id)


    return bool(
        user and user["trial_used"] == 1
    )



def get_expired_users():

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT user_id

        FROM users

        WHERE subscription_until!=''

        AND subscription_until <= date('now')

        """
    )


    data = cur.fetchall()


    conn.close()


    return [
        x["user_id"]
        for x in data
    ]



# =====================
# ПЛАТЕЖИ
# =====================

def add_payment(user_id, photo, days, amount=0):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT INTO payments

        (
            user_id,
            photo,
            days,
            amount
        )

        VALUES (?,?,?,?)

        """,
        (
            user_id,
            photo,
            days,
            amount
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


    payment = cur.fetchone()


    conn.close()


    return payment



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



def get_promos():

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        "SELECT * FROM promocodes"
    )


    data = cur.fetchall()


    conn.close()


    return data



# =====================
# СТАТИСТИКА
# =====================

def get_stats():

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    total = cur.fetchone()[0]


    cur.execute(
        """
        SELECT COUNT(*)

        FROM users

        WHERE status='active'

        """
    )

    active = cur.fetchone()[0]


    conn.close()


    return {

        "total": total,

        "active": active

    }



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


        status='expired',


        bs_active=0,


        wifi_active=1


        WHERE user_id=?

        """,
        (user_id,)
    )


    conn.commit()
    conn.close()