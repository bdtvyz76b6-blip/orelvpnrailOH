import sqlite3

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
        tariff TEXT DEFAULT 'Wi-Fi',
        link TEXT DEFAULT '',
        wifi_active INTEGER DEFAULT 1,
        bs_active INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()



# =====================
# ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ
# =====================

def add_user(user_id, username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username)
    VALUES (?, ?)
    """,
    (user_id, username))

    conn.commit()
    conn.close()



# =====================
# ПОЛУЧИТЬ ЮЗЕРА
# =====================

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



# =====================
# ВСЕ ПОЛЬЗОВАТЕЛИ
# =====================

def get_all_users():

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users"
    )

    users = cur.fetchall()

    conn.close()

    return users



# =====================
# АКТИВАЦИЯ ОБХОД Б/С
# =====================

def activate_bs(user_id, link):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET tariff='Обход Б/С',
        link=?,
        bs_active=1
    WHERE user_id=?
    """,
    (link, user_id))

    conn.commit()
    conn.close()



# =====================
# ВЫДАТЬ ТАРИФ
# =====================

def set_tariff(user_id, tariff, link):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET tariff=?,
        link=?
    WHERE user_id=?
    """,
    (tariff, link, user_id))

    conn.commit()
    conn.close()



# =====================
# УБРАТЬ ОБХОД Б/С
# =====================

def remove_bs(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET tariff='Wi-Fi',
        link='',
        bs_active=0
    WHERE user_id=?
    """,
    (user_id,))

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
        "SELECT COUNT(*) FROM users WHERE bs_active=1"
    )
    bs = cur.fetchone()[0]


    cur.execute(
        "SELECT COUNT(*) FROM users WHERE wifi_active=1"
    )
    wifi = cur.fetchone()[0]


    conn.close()


    return {
        "total": total,
        "bs": bs,
        "wifi": wifi
    }



# =====================
# УДАЛИТЬ ЮЗЕРА
# =====================

def delete_user(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM users WHERE user_id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()