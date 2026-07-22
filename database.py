import sqlite3

DB = "users.db"


def connect():
    return sqlite3.connect(DB)


def create_table():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,
        username TEXT,

        wifi_active INTEGER DEFAULT 1,
        bs_active INTEGER DEFAULT 0,

        wifi_link TEXT DEFAULT '',
        bs_link TEXT DEFAULT '',

        created_at TEXT DEFAULT CURRENT_TIMESTAMP

    )
    """)

    conn.commit()
    conn.close()



def add_user(user_id, username):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO users
    (user_id, username)

    VALUES (?, ?)
    """,
    (
        user_id,
        username
    ))

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



def activate_bs(user_id, link):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users

    SET
    bs_active=1,
    bs_link=?

    WHERE user_id=?
    """,
    (
        link,
        user_id
    ))

    conn.commit()
    conn.close()



def remove_bs(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE users

    SET
    bs_active=0,
    bs_link=''

    WHERE user_id=?
    """,
    (user_id,))

    conn.commit()
    conn.close()