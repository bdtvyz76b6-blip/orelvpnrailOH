from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from keyboards.admin_keyboard import admin_menu

from database import (
    get_all_users,
    get_all_payments,
)


router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# ПРОВЕРКА АКТИВНОСТИ ПОДПИСКИ
# ============================================================

def is_subscription_active(user: dict) -> bool:
    if not isinstance(user, dict):
        return False

    # В БД subscription теперь BOOLEAN
    if user.get("subscription") is not True:
        return False

    subscription_until = user.get("subscription_until")

    if not subscription_until:
        return False

    if isinstance(subscription_until, str):
        try:
            subscription_until = datetime.fromisoformat(
                subscription_until.replace("Z", "+00:00")
            )
        except ValueError:
            return False

    if not isinstance(subscription_until, datetime):
        return False

    if subscription_until.tzinfo is None:
        subscription_until = subscription_until.replace(
            tzinfo=timezone.utc
        )

    return subscription_until > datetime.now(timezone.utc)


# ============================================================
# АДМИН ПАНЕЛЬ
# ============================================================

@router.message(Command("admin"))
async def admin_start(message: Message):

    if not message.from_user:
        return

    # --------------------------------------------------------
    # ПРОВЕРКА АДМИНА
    # --------------------------------------------------------

    if not is_admin(message.from_user.id):
        await message.answer(
            "❌ <b>Нет доступа.</b>\n\n"
            "Эта команда доступна только администраторам.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # ПОЛЬЗОВАТЕЛИ
    # --------------------------------------------------------

    try:
        users = get_all_users() or []
    except Exception as e:
        print(
            "❌ Admin get_all_users error:",
            repr(e),
        )
        users = []

    # --------------------------------------------------------
    # ПЛАТЕЖИ
    # --------------------------------------------------------

    try:
        payments = get_all_payments() or []
    except Exception as e:
        print(
            "❌ Admin get_all_payments error:",
            repr(e),
        )
        payments = []

    # ========================================================
    # СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
    # ========================================================