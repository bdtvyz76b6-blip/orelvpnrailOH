import sqlite3

from datetime import datetime, timedelta


DB = "users.db"



def connect():
    return sqlite3.connect(DB)





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



    conn.commit()
    conn.close()





# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

def add_user(user_id, username):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT OR IGNORE INTO users

        (
        user_id,
        username
        )

        VALUES (?,?)

        """,
        (
            user_id,
            username
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
        user[0]
        for user in get_all_users()
    ]





# =====================
# ВЫБОР ТАРИФА
# =====================

def set_pending_days(user_id, days):

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
        (
            user_id,
        )
    )


    result = cur.fetchone()


    conn.close()


    if result and result[0] > 0:
        return result[0]


    return 30





# =====================
# ПОДПИСКА
# =====================

def activate_subscription(
        user_id,
        link,
        days
):


    conn = connect()
    cur = conn.cursor()


    date = (

        datetime.now()

        +
        timedelta(days=days)

    ).strftime("%Y-%m-%d")



    cur.execute(
        """
        UPDATE users

        SET

        tariff='👑 Орёл VPN',

        link=?,

        subscription_until=?,

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





def activate_trial(
        user_id,
        link
):


    conn = connect()
    cur = conn.cursor()


    date = (

        datetime.now()

        +
        timedelta(days=3)

    ).strftime("%Y-%m-%d")



    cur.execute(
        """
        UPDATE users

        SET

        tariff='🎁 Пробный период',

        link=?,

        subscription_until=?,

        trial_used=1,

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

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT trial_used

        FROM users

        WHERE user_id=?

        """,
        (
            user_id,
        )
    )


    result = cur.fetchone()


    conn.close()


    if result:
        return result[0] == 1


    return False





def get_subscription_link(user_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT link

        FROM users

        WHERE user_id=?

        """,
        (
            user_id,
        )
    )


    result = cur.fetchone()


    conn.close()


    if result:
        return result[0]


    return ""





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


    users = cur.fetchall()


    conn.close()


    return [
        user[0]
        for user in users
    ]





# =====================
# ПРОМОКОДЫ
# =====================

def create_promo(code, days):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT OR REPLACE INTO promocodes

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





def delete_promo(code):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        DELETE FROM promocodes

        WHERE code=?

        """,
        (
            code,
        )
    )


    conn.commit()
    conn.close()





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





def approve_payment(payment_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE payments

        SET status='approved'

        WHERE id=?

        """,
        (
            payment_id,
        )
    )


    conn.commit()
    conn.close()





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
# ОТКЛЮЧЕНИЕ ПОДПИСКИ
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
        bs_active=0,
        subscription_until=''

        WHERE user_id=?
        """,
        (
            user_id,
        )
    )

    conn.commit()
    conn.close()