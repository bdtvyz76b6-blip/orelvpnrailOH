from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from keyboards.admin_keyboard import admin_menu

from database import (
get_all_users,
get_payments,
)

router = Router()

============================================================

ПРОВЕРКА АДМИНА

============================================================

def is_admin(user_id: int) -> bool:
return user_id in ADMIN_IDS

============================================================

АДМИН ПАНЕЛЬ

============================================================

@router.message(Command(“admin”))
async def admin_start(message: Message):

# --------------------------------------------------------
# ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ
# --------------------------------------------------------
if not message.from_user:
    return
if not is_admin(message.from_user.id):
    await message.answer(
        "❌ <b>Нет доступа.</b>\n\n"
        "Эта команда доступна только администраторам.",
        parse_mode="HTML",
    )
    return
# --------------------------------------------------------
# ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЕЙ
# --------------------------------------------------------
try:
    users = get_all_users() or []
except Exception as e:
    print(
        "Admin users statistics error:",
        repr(e),
    )
    users = []
# --------------------------------------------------------
# ПОЛУЧАЕМ ПЛАТЕЖИ
# --------------------------------------------------------
try:
    payments = get_payments() or []
except Exception as e:
    print(
        "Admin payments statistics error:",
        repr(e),
    )
    payments = []
# --------------------------------------------------------
# СТАТИСТИКА
# --------------------------------------------------------
total_users = len(users)
vip_users = 0
trial_users = 0
expired_users = 0
no_subscription_users = 0
for user in users:
    try:
        if isinstance(user, dict):
            subscription = user.get(
                "subscription",
                "none",
            )
        else:
            subscription = user[3]
    except (IndexError, TypeError):
        subscription = "none"
    subscription = str(
        subscription or "none"
    ).lower()
    if subscription == "vip":
        vip_users += 1
    elif subscription == "trial":
        trial_users += 1
    elif subscription == "expired":
        expired_users += 1
    else:
        no_subscription_users += 1
# --------------------------------------------------------
# ПЛАТЕЖИ
# --------------------------------------------------------
pending_payments = 0
successful_payments = 0
for payment in payments:
    try:
        if isinstance(payment, dict):
            status = payment.get(
                "status",
                "pending",
            )
        else:
            status = payment[5]
    except (IndexError, TypeError):
        status = "pending"
    status = str(
        status or "pending"
    ).lower()
    if status == "pending":
        pending_payments += 1
    elif status in (
        "paid",
        "success",
        "completed",
        "approved",
    ):
        successful_payments += 1
# --------------------------------------------------------
# ПАНЕЛЬ
# --------------------------------------------------------
text = (
    "🛠 <b>ixxy VPN — Админ-панель</b>\n\n"
    "📊 <b>Статистика</b>\n"
    f"👥 Пользователей: <b>{total_users}</b>\n"
    f"👑 VIP: <b>{vip_users}</b>\n"
    f"🎁 Пробных: <b>{trial_users}</b>\n"
    f"🔴 Истёкших: <b>{expired_users}</b>\n"
    f"⚪ Без подписки: <b>{no_subscription_users}</b>\n\n"
    "💳 <b>Платежи</b>\n"
    f"⏳ Ожидают: <b>{pending_payments}</b>\n"
    f"✅ Успешных: <b>{successful_payments}</b>\n\n"
    "👇 <b>Выберите действие:</b>"
)
await message.answer(
    text,
    reply_markup=admin_menu(),
    parse_mode="HTML",
)