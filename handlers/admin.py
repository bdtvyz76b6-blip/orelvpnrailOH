from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from keyboards.admin_keyboard import admin_menu

from database import (
    get_all_users,
    get_all_payments,
    get_stats,
    subscription_active,
)

from datetime import datetime, timezone


router = Router()


# ============================================================
# АДМИН ПАНЕЛЬ
# ============================================================

@router.message(Command("admin"))
async def admin_start(
    message: Message,
):

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

        print(
            f"❌ Ошибка получения пользователей: {e}"
        )

        users = []

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ПЛАТЕЖИ
    # --------------------------------------------------------

    try:

        payments = get_all_payments() or []

    except Exception as e:

        print(
            f"❌ Ошибка получения платежей: {e}"
        )

        payments = []

    # --------------------------------------------------------
    # СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ
    # --------------------------------------------------------

    total_users = len(users)

    active_users = 0
    expired_users = 0
    no_subscription = 0

    now = datetime.now(
        timezone.utc
    )

    for user in users:

        if not isinstance(
            user,
            dict,
        ):
            continue

        subscription = bool(
            user.get(
                "subscription",
                False,
            )
        )

        subscription_until = user.get(
            "subscription_until"
        )

        # ----------------------------------------------------
        # Активная подписка
        # ----------------------------------------------------

        is_active = False

        if subscription and subscription_until:

            try:

                if (
                    subscription_until.tzinfo
                    is not None
                ):

                    is_active = (
                        subscription_until
                        > now
                    )

                else:

                    is_active = (
                        subscription_until
                        > now.replace(
                            tzinfo=None
                        )
                    )

            except Exception:

                is_active = False

        if is_active:

            active_users += 1

        elif subscription_until:

            expired_users += 1

        else:

            no_subscription += 1

    # --------------------------------------------------------
    # СТАТИСТИКА ПЛАТЕЖЕЙ
    # --------------------------------------------------------

    pending_payments = 0
    completed_payments = 0
    failed_payments = 0

    for payment in payments:

        if not isinstance(
            payment,
            dict,
        ):
            continue

        status = str(
            payment.get(
                "status",
                ""
            )
        ).lower()

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
    # ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА ИЗ DATABASE
    # --------------------------------------------------------

    try:

        stats = get_stats() or {}

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

        revenue = int(
            revenue or 0
        )

    except Exception:

        revenue = 0

    # В БД CasheRa хранится в копейках.
    # Поэтому переводим в рубли.

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