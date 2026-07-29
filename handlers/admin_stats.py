from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import (
    get_all_users,
    get_expired_users,
    get_promocodes
)

router = Router()


@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):

    users = len(get_all_users())

    expired = len(get_expired_users())

    promos = len(get_promocodes())


    active = users - expired


    text = (
        "📊 Статистика\n\n"
        f"👥 Всего пользователей: {users}\n"
        f"🟢 Активных: {active}\n"
        f"🔴 Истекших: {expired}\n"
        f"🎟 Промокодов: {promos}"
    )


    await call.message.edit_text(
        text
    )