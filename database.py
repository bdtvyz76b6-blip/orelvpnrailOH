import sqlite3
from datetime import datetime, timedelta


DB = "users.db"


def connect():
    return sqlite3.connect(DB)



# =====================
# СОЗДАНИЕ БАЗЫ
# =====================

def create_table():

    conn = connect()
    cur = conn.cursor()


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

        notify INTEGER DEFAULT 1,

        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        amount INTEGER,

        currency TEXT,

        days INTEGER,

        payment_id TEXT,

        status TEXT DEFAULT 'pending',

        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS promocodes (

        code TEXT PRIMARY KEY,

        days INTEGER

    )
    """)



    conn.commit()
    conn.close()





# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

def add_user(user_id, username=None, first_name=None):

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
        "SELECT * FROM users ORDER BY created_at DESC"
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
# ССЫЛКА ПОДПИСКИ
# =====================

def save_subscription_link(user_id, link):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    UPDATE users

    SET subscription_link=?

    WHERE user_id=?

    """,
    (
        link,
        user_id
    ))


    conn.commit()
    conn.close()





def get_subscription_link(user_id):

    user = get_user(user_id)

    if user:
        return user[5]

    return ""





# =====================
# АКТИВАЦИЯ VIP
# =====================

def activate_subscription(
        user_id,
        link,
        days
):

    conn = connect()
    cur = conn.cursor()


    user = get_user(user_id)


    start = datetime.now()


    if user and user[4]:

        try:
            old_date = datetime.strptime(
                user[4],
                "%Y-%m-%d"
            )

            if old_date > start:
                start = old_date

        except:
            pass



    new_date = (
        start + timedelta(days=days)
    ).strftime("%Y-%m-%d")



    cur.execute("""
    UPDATE users

    SET

    subscription='vip',

    subscription_until=?,

    subscription_link=?


    WHERE user_id=?

    """,
    (
        new_date,
        link,
        user_id
    ))


    conn.commit()
    conn.close()





# =====================
# ПРОБНИК
# =====================

def activate_trial(user_id, link):

    date = (
        datetime.now()
        +
        timedelta(days=3)
    ).strftime("%Y-%m-%d")


    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    UPDATE users

    SET

    subscription='trial',

    subscription_until=?,

    subscription_link=?,

    trial_used=1


    WHERE user_id=?

    """,
    (
        date,
        link,
        user_id
    ))


    conn.commit()
    conn.close()





def check_trial(user_id):

    user = get_user(user_id)

    if not user:
        return False


    return user[7] == 1





# =====================
# ОТКЛЮЧЕНИЕ
# =====================

def disable_subscription(user_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    UPDATE users

    SET

    subscription='none',

    subscription_until='',

    subscription_link=''


    WHERE user_id=?

    """,
    (user_id,))


    conn.commit()
    conn.close()





# =====================
# ПРОСРОЧКИ
# =====================

def get_expired_users():

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    SELECT user_id

    FROM users

    WHERE subscription_until!=''

    AND subscription_until <= date('now')

    """)


    users = cur.fetchall()

    conn.close()


    return [
        x[0]
        for x in users
    ]





# =====================
# STARS ПЛАТЕЖИ
# =====================

def add_stars_payment(
        user_id,
        amount,
        days,
        payment_id
):

    conn = connect()
    cur = conn.cursor()


    cur.execute("""
    INSERT INTO payments
    (
        user_id,
        amount,
        currency,
        days,
        payment_id,
        status
    )

    VALUES (?,?,?,?,?,?)

    """,
    (
        user_id,
        amount,
        "XTR",
        days,
        payment_id,
        "paid"
    ))


    conn.commit()
    conn.close()





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


    result = cur.fetchall()

    conn.close()

    return result





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


    cur.execute(
        "SELECT COUNT(*) FROM users"
    )

    total = cur.fetchone()[0]


    cur.execute(
        """
        SELECT COUNT(*)

        FROM users

        WHERE subscription!='none'

        """
    )

    active = cur.fetchone()[0]


    conn.close()


    return {

        "total": total,

        "active": active

    }
