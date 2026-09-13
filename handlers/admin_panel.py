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
    if not user.get("subscription"):
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
            "Admin get_all_users error:",
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
            "Admin get_all_payments error:",
            repr(e),
        )
        payments = []

    # ========================================================
    # СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
    # ========================================================

    total_users = len(users)

    active_users = 0
    trial_users = 0
    expired_users = 0
    no_subscription_users = 0

    for user in users:

        if not isinstance(user, dict):
            continue

        # ----------------------------------------------------
        # АКТИВНАЯ ПОДПИСКА
        # ----------------------------------------------------

        if is_subscription_active(user):
            active_users += 1

        # ----------------------------------------------------
        # ПРОБНЫЙ ПЕРИОД
        # ----------------------------------------------------

        if user.get("trial_used"):
            trial_users += 1

        # ----------------------------------------------------
        # ИСТЁКШАЯ ПОДПИСКА
        # ----------------------------------------------------

        subscription_until = user.get(
            "subscription_until"
        )

        if (
            subscription_until
            and not is_subscription_active(user)
        ):
            expired_users += 1

        # ----------------------------------------------------
        # БЕЗ ПОДПИСКИ
        # ----------------------------------------------------

        if (
            not user.get("subscription")
            and not subscription_until
        ):
            no_subscription_users += 1

    # ========================================================
    # СТАТИСТИКА ПЛАТЕЖЕЙ
    # ========================================================

    pending_payments = 0
    successful_payments = 0
    failed_payments = 0

    for payment in payments:

        if not isinstance(payment, dict):
            continue

        status = str(
            payment.get("status") or "pending"
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

        elif status in (
            "failed",
            "cancelled",
            "canceled",
            "rejected",
        ):
            failed_payments += 1

    # ========================================================
    # ТЕКСТ
    # ========================================================

    text = (
        "🛠 <b>☂️ ixxy VPN — Админ-панель</b>\n\n"

        "📊 <b>Пользователи</b>\n"
        f"👥 Всего: <b>{total_users}</b>\n"
        f"🟢 Активных подписок: <b>{active_users}</b>\n"
        f"🎁 Использовали пробник: <b>{trial_users}</b>\n"
        f"🔴 Истёкших: <b>{expired_users}</b>\n"
        f"⚪ Без подписки: <b>{no_subscription_users}</b>\n\n"

        "💳 <b>Платежи</b>\n"
        f"⏳ Ожидают: <b>{pending_payments}</b>\n"
        f"✅ Успешных: <b>{successful_payments}</b>\n"
        f"❌ Неуспешных: <b>{failed_payments}</b>\n\n"

        "👇 <b>Выберите действие:</b>"
    )

    # ========================================================
    # ОТПРАВКА
    # ========================================================

    await message.answer(
        text,
        reply_markup=admin_menu(),
        parse_mode="HTML",
    )