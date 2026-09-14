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

UTC = timezone.utc


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    try:
        return int(user_id) in ADMIN_IDS
    except (TypeError, ValueError):
        return False


# ============================================================
# ДАТА
# ============================================================

def normalize_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)

            return parsed.astimezone(UTC)

        except (ValueError, TypeError):
            return None

    return None


# ============================================================
# БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ЗНАЧЕНИЯ
# ============================================================

def get_value(data, key, default=None):
    if not isinstance(data, dict):
        return default

    return data.get(key, default)


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

    now = datetime.now(UTC)

    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

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

    for user in users_list:

        if not isinstance(user, dict):
            continue

        # ----------------------------------------------------
        # ПОДПИСКА
        # ----------------------------------------------------

        subscription = get_value(
            user,
            "subscription",
            False,
        )

        # В актуальной БД subscription = BOOLEAN.
        # True = подписка включена.
        subscription = subscription is True

        subscription_until = normalize_datetime(
            get_value(
                user,
                "subscription_until",
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

        else:
            no_subscription_users += 1

        # ----------------------------------------------------
        # TRIAL
        # ----------------------------------------------------

        if bool(
            get_value(
                user,
                "trial_used",
                False,
            )
        ):
            trial_users += 1

        # ----------------------------------------------------
        # РЕГИСТРАЦИЯ
        # ----------------------------------------------------

        created_at = normalize_datetime(
            get_value(
                user,
                "created_at",
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
        promos_list = get_all_promocodes() or []

        promo_count = len(promos_list)

        active_promos = 0

        for promo in promos_list:

            if not isinstance(promo, dict):
                continue

            if bool(
                get_value(
                    promo,
                    "active",
                    False,
                )
            ):
                active_promos += 1

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

    total_payments = len(payments_list)

    pending_payments = 0
    successful_payments = 0
    failed_payments = 0

    revenue = 0

    successful_statuses = {
        "paid",
        "success",
        "successful",
        "completed",
        "approved",
    }

    failed_statuses = {
        "failed",
        "cancelled",
        "canceled",
        "rejected",
        "error",
    }

    pending_statuses = {
        "pending",
        "processing",
        "waiting",
        "created",
    }

    for payment in payments_list:

        if not isinstance(payment, dict):
            continue

        status = str(
            get_value(
                payment,
                "status",
                "pending",
            )
            or "pending"
        ).lower().strip()

        if status in pending_statuses:

            pending_payments += 1

        elif status in successful_statuses:

            successful_payments += 1

            try:
                amount = int(
                    get_value(
                        payment,
                        "amount",
                        0,
                    )
                    or 0
                )

                # CashEra хранит сумму в копейках.
                # Stars — в XTR, поэтому Stars не
                # смешиваем с рублёвым доходом.
                payment_method = str(
                    get_value(
                        payment,
                        "payment_method",
                        get_value(
                            payment,
                            "method",
                            "",
                        ),
                    )
                    or ""
                ).lower()

                if payment_method not in (
                    "stars",
                    "telegram_stars",
                    "xtr",
                ):
                    revenue += amount

            except (
                ValueError,
                TypeError,
            ):
                pass

        elif status in failed_statuses:

            failed_payments += 1

    # ========================================================
    # РУБЛИ
    # ========================================================

    revenue_rub = revenue / 100

    if revenue_rub.is_integer():
        revenue_text = f"{int(revenue_rub)} ₽"
    else:
        revenue_text = f"{revenue_rub:.2f} ₽"

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

        f"💰 <b>Доход СБП:</b> {revenue_text}\n"
        "⭐ <b>Stars:</b> учитываются отдельно\n"
        "📡 <b>Трафик:</b> нет телеметрии\n"
    )

    # ========================================================
    # ОТПРАВКА
    # ========================================================

    try:

        if call.message:
            await call.message.edit_text(
                text,
                reply_markup=stats_keyboard(),
                parse_mode="HTML",
            )

    except Exception as e:

        error_text = str(e).lower()

        if "message is not modified" not in error_text:
            print(
                "❌ Admin stats message error:",
                repr(e),
            )

    await call.answer()