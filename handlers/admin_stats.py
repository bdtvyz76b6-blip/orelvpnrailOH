from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import ADMIN_IDS

from database import (
    get_all_users,
    get_all_promocodes,
    get_all_payments,
)

router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# ДАТА
# ============================================================

UTC = timezone.utc


def normalize_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

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
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users",
                ),
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data="admin_payments",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Промокоды",
                    callback_data="admin_promos",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
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
            show_alert=True,
        )
        return

    # ========================================================
    # ПОЛЬЗОВАТЕЛИ
    # ========================================================

    try:
        users_list = get_all_users() or []
    except Exception as e:
        print(
            "❌ Admin stats users error:",
            repr(e),
        )
        users_list = []

    total_users = len(users_list)

    active_users = 0
    expired_users = 0
    no_subscription_users = 0
    trial_users = 0

    users_today = 0
    users_7_days = 0
    users_30_days = 0

    now = datetime.now(UTC)

    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    for user in users_list:

        if not isinstance(user, dict):
            continue

        # ----------------------------------------------------
        # ПОДПИСКА
        # ----------------------------------------------------

        subscription = bool(
            user.get(
                "subscription",
                False,
            )
        )

        subscription_until = normalize_datetime(
            user.get(
                "subscription_until"
            )
        )

        if (
            subscription
            and subscription_until
            and subscription_until > now
        ):
            active_users += 1

        elif (
            subscription_until
            and subscription_until <= now
        ):
            expired_users += 1

        elif not subscription:
            no_subscription_users += 1

        # ----------------------------------------------------
        # TRIAL
        # ----------------------------------------------------

        if bool(
            user.get(
                "trial_used",
                False,
            )
        ):
            trial_users += 1

        # ----------------------------------------------------
        # РЕГИСТРАЦИЯ
        # ----------------------------------------------------

        created_at = normalize_datetime(
            user.get(
                "created_at"
            )
        )

        if created_at:

            if created_at.date() == today:
                users_today += 1

            if created_at >= week_ago:
                users_7_days += 1

            if created_at >= month_ago:
                users_30_days += 1

    # ========================================================
    # ПРОМОКОДЫ
    # ========================================================

    try:
        promos_list = (
            get_all_promocodes()
            or []
        )

        promo_count = len(
            promos_list
        )

        active_promos = sum(
            1
            for promo in promos_list
            if bool(
                promo.get(
                    "active",
                    False,
                )
            )
        )

    except Exception as e:

        print(
            "❌ Admin stats promos error:",
            repr(e),
        )

        promo_count = 0
        active_promos = 0

    # ========================================================
    # ПЛАТЕЖИ
    # ========================================================

    try:
        payments_list = (
            get_all_payments(10000)
            or []
        )

    except Exception as e:

        print(
            "❌ Admin stats payments error:",
            repr(e),
        )

        payments_list = []

    total_payments = len(
        payments_list
    )

    pending_payments = 0
    successful_payments = 0
    failed_payments = 0

    revenue = 0

    for payment in payments_list:

        if not isinstance(payment, dict):
            continue

        status = str(
            payment.get(
                "status",
                "pending",
            )
            or "pending"
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

            try:
                revenue += int(
                    payment.get(
                        "amount",
                        0,
                    )
                    or 0
                )
            except (
                ValueError,
                TypeError,
            ):
                pass

        elif status in (
            "failed",
            "cancelled",
            "canceled",
            "rejected",
        ):

            failed_payments += 1

    # ========================================================
    # ФОРМИРУЕМ ТЕКСТ
    # ========================================================

    text = (
        "📊 <b>Статистика ixxy VPN</b>\n"
        "\n"

        "👥 <b>Пользователи</b>\n"
        f"├ Всего: <b>{total_users}</b>\n"
        f"├ 🟢 Активных: <b>{active_users}</b>\n"
        f"├ 🔴 Истекших: <b>{expired_users}</b>\n"
        f"├ ⚪ Без подписки: <b>{no_subscription_users}</b>\n"
        f"└ 🎁 Использовали Trial: <b>{trial_users}</b>\n"
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
        f"├ Всего: <b>{promo_count}</b>\n"
        f"└ 🟢 Активных: <b>{active_promos}</b>\n"
        "\n"

        f"💰 <b>Доход:</b> {revenue} ₽\n"
        "📡 <b>Трафик:</b> нет телеметрии\n"
    )

    # ========================================================
    # ОТПРАВКА
    # ========================================================

    try:

        await call.message.edit_text(
            text,
            reply_markup=stats_keyboard(),
            parse_mode="HTML",
        )

    except Exception as e:

        print(
            "❌ Admin stats message error:",
            repr(e),
        )

    await call.answer()