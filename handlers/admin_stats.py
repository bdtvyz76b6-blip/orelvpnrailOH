from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS

from database import (
    get_all_users,
    get_expired_users,
    get_promocodes,
    get_payments,
)

router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ПОЛЯ USER
# ============================================================

def user_field(user, index: int, key: str, default=""):
    if isinstance(user, dict):
        return user.get(key, default)

    try:
        return user[index]
    except (IndexError, TypeError):
        return default


# ============================================================
# БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ПОЛЯ PAYMENT
# ============================================================

def payment_field(payment, index: int, key: str, default=""):
    if isinstance(payment, dict):
        return payment.get(key, default)

    try:
        return payment[index]
    except (IndexError, TypeError):
        return default


# ============================================================
# ПАРСИНГ ДАТЫ
# ============================================================

def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    return None


# ============================================================
# КЛАВИАТУРА
# ============================================================

def stats_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                ),
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data="admin_payments"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Промокоды",
                    callback_data="admin_promos"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back"
                )
            ],
        ]
    )


# ============================================================
# СТАТИСТИКА
# ============================================================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):

    if not call.from_user:
        return

    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    # --------------------------------------------------------
    # ПОЛЬЗОВАТЕЛИ
    # --------------------------------------------------------

    try:
        users_list = get_all_users() or []
    except Exception as e:
        print("Admin stats users error:", repr(e))
        users_list = []

    total_users = len(users_list)

    vip_users = 0
    trial_users = 0
    expired_users = 0
    none_users = 0

    users_today = 0
    users_7_days = 0
    users_30_days = 0

    now = datetime.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    for user in users_list:

        subscription = str(
            user_field(
                user,
                3,
                "subscription",
                "none"
            ) or "none"
        ).lower().strip()

        # ----------------------------------------------------
        # ТАРИФ
        # ----------------------------------------------------

        if subscription == "vip":
            vip_users += 1

        elif subscription == "trial":
            trial_users += 1

        elif subscription == "expired":
            expired_users += 1

        else:
            none_users += 1

        # ----------------------------------------------------
        # ДАТА РЕГИСТРАЦИИ
        # ----------------------------------------------------

        created_at = user_field(
            user,
            11,
            "created_at",
            None
        )

        created_at = parse_datetime(created_at)

        if created_at:

            if created_at.date() == today:
                users_today += 1

            if created_at >= week_ago:
                users_7_days += 1

            if created_at >= month_ago:
                users_30_days += 1

    # --------------------------------------------------------
    # ПРОМОКОДЫ
    # --------------------------------------------------------

    try:
        promos_list = get_promocodes() or []
        promo_count = len(promos_list)
    except Exception as e:
        print("Admin stats promos error:", repr(e))
        promo_count = 0

    # --------------------------------------------------------
    # ПЛАТЕЖИ
    # --------------------------------------------------------

    try:
        payments_list = get_payments() or []
    except Exception as e:
        print("Admin stats payments error:", repr(e))
        payments_list = []

    total_payments = len(payments_list)

    pending_payments = 0
    successful_payments = 0
    failed_payments = 0

    for payment in payments_list:

        status = str(
            payment_field(
                payment,
                5,
                "status",
                "pending"
            ) or "pending"
        ).lower().strip()

        if status == "pending":
            pending_payments += 1

        elif status in (
            "paid",
            "success",
            "successful",
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

    # --------------------------------------------------------
    # АКТИВНЫЕ
    # --------------------------------------------------------

    active_users = vip_users + trial_users

    # --------------------------------------------------------
    # ФОРМИРУЕМ ТЕКСТ
    # --------------------------------------------------------

    text = (
        "📊 <b>Статистика ixxy VPN</b>\n"
        "\n"

        "👥 <b>Пользователи</b>\n"
        f"├ Всего: <b>{total_users}</b>\n"
        f"├ 👑 VIP: <b>{vip_users}</b>\n"
        f"├ 🎁 Trial: <b>{trial_users}</b>\n"
        f"├ 🟢 Активных: <b>{active_users}</b>\n"
        f"├ 🔴 Истекших: <b>{expired_users}</b>\n"
        f"└ ⚪ Без подписки: <b>{none_users}</b>\n"
        "\n"

        "📈 <b>Регистрации</b>\n"
        f"├ Сегодня: <b>{users_today}</b>\n"
        f"├ За 7 дней: <b>{users_7_days}</b>\n"
        f"└ За 30 дней: <b>{users_30_days}</b>\n"
        "\n"

        "💳 <b>Платежи</b>\n"
        f"├ Всего: <b>{total_payments}</b>\n"
        f"├ ✅ Успешных: <b>{successful_payments}</b>\n"
        f"├ ⏳ Ожидают: <b>{pending_payments}</b>\n"
        f"└ ❌ Неуспешных: <b>{failed_payments}</b>\n"
        "\n"

        "🎟 <b>Промокоды</b>\n"
        f"└ Всего: <b>{promo_count}</b>\n"
        "\n"

        "💰 <b>Доход:</b> недоступен\n"
        "📡 <b>Трафик:</b> нет телеметрии\n"
    )

    try:
        await call.message.edit_text(
            text,
            reply_markup=stats_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print("Admin stats message error:", repr(e))

    await call.answer()