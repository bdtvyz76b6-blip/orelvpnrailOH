from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from keyboards.admin_keyboard import admin_menu

from database import (
    get_all_users,
    get_all_payments,
    get_stats,
)

from datetime import datetime, timezone


router = Router()


# ============================================================
# АДМИН ПАНЕЛЬ
# ============================================================

@router.message(Command("admin"))
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
    # ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЕЙ
    # --------------------------------------------------------

    try:
        users = get_all_users() or []
    except Exception as e:
        print(f"❌ Ошибка получения пользователей: {e}")
        users = []

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ПЛАТЕЖИ
    # --------------------------------------------------------

    try:
        payments = get_all_payments() or []
    except Exception as e:
        print(f"❌ Ошибка получения платежей: {e}")
        payments = []

    # --------------------------------------------------------
    # СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
    # --------------------------------------------------------

    total_users = len(users)

    active_users = 0
    expired_users = 0
    no_subscription = 0

    now = datetime.now(timezone.utc)

    for user in users:

        if not isinstance(user, dict):
            continue

        # PostgreSQL BOOLEAN
        subscription = bool(
            user.get("subscription", False)
        )

        subscription_until = user.get(
            "subscription_until"
        )

        # ----------------------------------------------------
        # Нет даты окончания
        # ----------------------------------------------------

        if not subscription_until:
            no_subscription += 1
            continue

        # ----------------------------------------------------
        # Приводим дату к datetime
        # ----------------------------------------------------

        try:

            if isinstance(
                subscription_until,
                datetime,
            ):

                until = subscription_until

            else:

                until = datetime.fromisoformat(
                    str(subscription_until)
                    .replace("Z", "+00:00")
                )

            # Если дата без timezone — считаем её UTC
            if until.tzinfo is None:

                until = until.replace(
                    tzinfo=timezone.utc
                )

            else:

                until = until.astimezone(
                    timezone.utc
                )

        except Exception as e:

            print(
                "⚠️ Ошибка обработки "
                f"subscription_until: {e}"
            )

            # Если дата есть, но прочитать её нельзя,
            # считаем подписку истёкшей.
            expired_users += 1
            continue

        # ----------------------------------------------------
        # АКТИВНАЯ ПОДПИСКА
        # ----------------------------------------------------

        if subscription and until > now:

            active_users += 1

        else:

            expired_users += 1

    # --------------------------------------------------------
    # СТАТИСТИКА ПЛАТЕЖЕЙ
    # --------------------------------------------------------

    pending_payments = 0
    completed_payments = 0
    failed_payments = 0

    for payment in payments:

        if not isinstance(payment, dict):
            continue

        status = str(
            payment.get("status", "")
        ).strip().lower()

        if status == "pending":

            pending_payments += 1

        elif status in (
            "paid",
            "success",
            "completed",
            "approved",
        ):

            completed_payments += 1

        elif status in (
            "failed",
            "cancelled",
            "canceled",
            "rejected",
        ):

            failed_payments += 1

    # --------------------------------------------------------
    # ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА
    # --------------------------------------------------------

    try:

        stats = get_stats() or {}

        if not isinstance(stats, dict):
            stats = {}

    except Exception as e:

        print(
            f"⚠️ Ошибка get_stats: {e}"
        )

        stats = {}

    # --------------------------------------------------------
    # ДОХОД
    # --------------------------------------------------------

    revenue = stats.get(
        "revenue",
        0,
    )

    try:

        revenue = float(
            revenue or 0
        )

    except Exception:

        revenue = 0.0

    # CasheRA хранит сумму в копейках.
    revenue_rub = revenue / 100

    # --------------------------------------------------------
    # АДМИНСКОЕ МЕНЮ
    # --------------------------------------------------------

    text = (
        "🛠 <b>Панель администратора</b>\n\n"

        "☂️ <b>ixxy VPN</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "📊 <b>Пользователи</b>\n"
        f"👥 Всего: <b>{total_users}</b>\n"
        f"🟢 Активных: <b>{active_users}</b>\n"
        f"🔴 Истёкших: <b>{expired_users}</b>\n"
        f"⚪ Без подписки: <b>{no_subscription}</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "💳 <b>Платежи</b>\n"
        f"⏳ Ожидают: <b>{pending_payments}</b>\n"
        f"✅ Успешных: <b>{completed_payments}</b>\n"
        f"❌ Отклонённых: <b>{failed_payments}</b>\n\n"

        "💰 Доход: "
        f"<b>{revenue_rub:.2f} ₽</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "👇 <b>Выбери нужный раздел:</b>"
    )

    # --------------------------------------------------------
    # ОТПРАВКА
    # --------------------------------------------------------

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=admin_menu(),
    )