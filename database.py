import sqlite3


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
        (user_id, username)
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
        "SELECT * FROM users WHERE user_id=?",
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

    users = get_all_users()

    return [
        user[0]
        for user in users
    ]





# =====================
# ТАРИФЫ
# =====================

def set_tariff(user_id, tariff, link):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users
        SET tariff=?,
        link=?
        WHERE user_id=?
        """,
        (
            tariff,
            link,
            user_id
        )
    )


    conn.commit()
    conn.close()




def activate_bs(user_id, link):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users

        SET tariff='Обход Б/С',
        link=?,
        bs_active=1

        WHERE user_id=?
        """,
        (
            link,
            user_id
        )
    )


    conn.commit()
    conn.close()




def remove_bs(user_id):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        UPDATE users

        SET tariff='Wi-Fi',
        link='',
        bs_active=0

        WHERE user_id=?
        """,
        (user_id,)
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
        "SELECT COUNT(*) FROM users WHERE wifi_active=1"
    )

    wifi = cur.fetchone()[0]


    cur.execute(
        "SELECT COUNT(*) FROM users WHERE bs_active=1"
    )

    bs = cur.fetchone()[0]


    conn.close()


    return {

        "total": total,
        "wifi": wifi,
        "bs": bs

    }





# =====================
# ПРОМОКОДЫ
# =====================

def create_promo(code, days):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT OR REPLACE INTO promocodes
        (code, days)

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
        "DELETE FROM promocodes WHERE code=?",
        (code,)
    )


    conn.commit()
    conn.close()





# =====================
# ОПЛАТЫ
# =====================

def add_payment(user_id, photo):

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        INSERT INTO payments
        (user_id, photo)

        VALUES (?,?)
        """,
        (
            user_id,
            photo
        )
    )


    conn.commit()
    conn.close()




def get_payments():

    conn = connect()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT * FROM payments
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
        (payment_id,)
    )


    conn.commit()
    conn.close()