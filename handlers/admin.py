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

АДМИН ПАНЕЛЬ

============================================================

@router.message(Command(“admin”))
async def admin_start(message: Message):

# --------------------------------------------------------
# ПРОВЕРКА АДМИНА
# --------------------------------------------------------
if not message.from_user:
    return
if message.from_user.id not in ADMIN_IDS:
    await message.answer(
        "❌ <b>Доступ запрещён</b>\n\n"
        "У тебя нет доступа к панели администратора.",
        parse_mode="HTML",
    )
    return
# --------------------------------------------------------
# ПОЛУЧАЕМ СТАТИСТИКУ
# --------------------------------------------------------
try:
    users = get_all_users() or []
except Exception:
    users = []
try:
    payments = get_payments() or []
except Exception:
    payments = []
total_users = len(users)
active_users = 0
trial_users = 0
expired_users = 0
no_subscription = 0
for user in users:
    # Поддержка tuple и dict
    if isinstance(user, dict):
        subscription = user.get("subscription", "none")
    else:
        try:
            # В текущей структуре subscription находится
            # после first_name.
            subscription = user[3]
        except (IndexError, TypeError):
            subscription = "none"
    subscription = str(subscription or "none").lower()
    if subscription == "vip":
        active_users += 1
    elif subscription == "trial":
        trial_users += 1
    elif subscription in ("none", "expired", ""):
        if subscription == "expired":
            expired_users += 1
        else:
            no_subscription += 1
pending_payments = 0
completed_payments = 0
for payment in payments:
    if isinstance(payment, dict):
        status = payment.get("status", "pending")
    else:
        try:
            # В стандартной структуре status находится
            # после payment_id.
            status = payment[5]
        except (IndexError, TypeError):
            status = "pending"
    status = str(status or "pending").lower()
    if status == "pending":
        pending_payments += 1
    elif status in ("paid", "success", "completed", "approved"):
        completed_payments += 1
# --------------------------------------------------------
# АДМИНСКОЕ МЕНЮ
# --------------------------------------------------------
text = (
    "🛠 <b>Панель администратора</b>\n\n"
    
    "📊 <b>Общая статистика</b>\n"
    f"👥 Пользователей: <b>{total_users}</b>\n"
    f"👑 Активных VIP: <b>{active_users}</b>\n"
    f"🎁 Пробных: <b>{trial_users}</b>\n"
    f"🔴 Истёкших: <b>{expired_users}</b>\n"
    f"⚪ Без подписки: <b>{no_subscription}</b>\n\n"
    "💳 <b>Платежи</b>\n"
    f"⏳ Ожидают: <b>{pending_payments}</b>\n"
    f"✅ Успешных: <b>{completed_payments}</b>\n\n"
    "👇 <b>Выбери нужный раздел:</b>"
)
await message.answer(
    text,
    parse_mode="HTML",
    reply_markup=admin_menu(),
)