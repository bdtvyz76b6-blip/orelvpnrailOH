from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import (
    get_all_users,
    get_expired_users,
    get_promocodes,
    connect
)

router = Router()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):

    users = len(get_all_users())
    expired = len(get_expired_users())
    promos = len(get_promocodes())

    db = connect()
    cur = db.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE trial_used = 1"
    )
    trials = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE subscription_until != ''"
    )
    active = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM users WHERE notify = 1"
    )
    notify = cur.fetchone()[0]

    db.close()

    text = (
        "📊 <b>Статистика</b>\n\n"

        f"👥 Пользователей: <b>{users}</b>\n"
        f"🟢 Активных: <b>{active}</b>\n"
        f"🔴 Истекших: <b>{expired}</b>\n"
        f"🎁 Использовали пробник: <b>{trials}</b>\n"
        f"🎟 Промокодов: <b>{promos}</b>\n"
        f"🔔 Уведомления: <b>{notify}</b>"
    )

    await call.message.edit_text(
        text,
        parse_mode="HTML"
    )