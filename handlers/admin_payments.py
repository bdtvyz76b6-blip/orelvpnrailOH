from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import (
    get_all_payments,
    get_payment,
    get_user,
)


router = Router()


# ============================================================
# НАСТРОЙКИ
# ============================================================

PAYMENTS_PER_PAGE = 10


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# СТАТУС ПЛАТЕЖА
# ============================================================

def format_payment_status(status) -> str:
    status = str(status or "pending").lower().strip()

    statuses = {
        "pending": "⏳ Ожидает",
        "paid": "✅ Оплачен",
        "success": "✅ Оплачен",
        "completed": "✅ Завершён",
        "approved": "✅ Подтверждён",
        "failed": "❌ Ошибка",
        "cancelled": "🚫 Отменён",
        "canceled": "🚫 Отменён",
        "rejected": "🚫 Отклонён",
    }

    return statuses.get(
        status,
        f"❔ {status}",
    )


# ============================================================
# ФОРМАТ ДАТЫ
# ============================================================

def format_datetime(value) -> str:
    if not value:
        return "нет"

    try:
        if isinstance(value, datetime):

            dt = value

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            return dt.astimezone(
                timezone.utc
            ).strftime(
                "%d.%m.%Y %H:%M"
            )

        text = str(value).strip()

        try:
            dt = datetime.fromisoformat(
                text.replace(
                    "Z",
                    "+00:00",
                )
            )

            if dt.tzinfo is None:
                dt = dt.replace(
                    tzinfo=timezone.utc
                )

            return dt.astimezone(
                timezone.utc
            ).strftime(
                "%d.%m.%Y %H:%M"
            )

        except ValueError:
            return text

    except Exception:
        return str(value)


# ============================================================
# СПОСОБ ОПЛАТЫ
# ============================================================

def format_provider(provider) -> str:
    provider = str(
        provider or ""
    ).lower().strip()

    if provider == "stars":
        return "⭐ Telegram Stars"

    if provider in (
        "cashera",
        "sbp",
    ):
        return "💳 СБП / CasheRa"

    if provider:
        return provider

    return "не указан"


# ============================================================
# СУММА
# ============================================================

def format_amount(payment: dict) -> str:
    amount = payment.get("amount")

    if amount is None:
        return "не указана"

    try:
        amount = int(amount)

    except (TypeError, ValueError):
        return str(amount)

    provider = str(
        payment.get("provider") or ""
    ).lower().strip()

    # CasheRa — копейки
    if provider == "cashera":
        return f"{amount / 100:.2f} ₽"

    # Telegram Stars — XTR
    if provider == "stars":
        return f"{amount} ⭐"

    return str(amount)


# ============================================================
# КЛАВИАТУРА ПЛАТЕЖЕЙ
# ============================================================

def payments_keyboard(
    payments,
    page: int,
):
    buttons = []

    start = page * PAYMENTS_PER_PAGE
    end = start + PAYMENTS_PER_PAGE

    page_payments = payments[
        start:end
    ]

    for payment in page_payments:

        if not isinstance(payment, dict):
            continue

        payment_id = payment.get("id")

        if payment_id is None:
            continue

        days = payment.get("days") or 0

        status_text = format_payment_status(
            payment.get("status")
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"💳 #{payment_id} · "
                        f"{days} дн. · "
                        f"{status_text}"
                    ),
                    callback_data=(
                        f"payment_info_{payment_id}"
                    ),
                )
            ]
        )

    # ========================================================
    # ПАГИНАЦИЯ
    # ========================================================

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=(
                    f"admin_payments_page_{page - 1}"
                ),
            )
        )

    total_pages = max(
        1,
        (
            len(payments)
            + PAYMENTS_PER_PAGE
            - 1
        )
        // PAYMENTS_PER_PAGE,
    )

    navigation.append(
        InlineKeyboardButton(
            text=(
                f"{page + 1}/{total_pages}"
            ),
            callback_data="noop",
        )
    )

    if end < len(payments):

        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"admin_payments_page_{page + 1}"
                ),
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=(
                    f"admin_payments_page_{page}"
                ),
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# ПОКАЗ ПЛАТЕЖЕЙ
# ============================================================

async def show_payments(
    call: CallbackQuery,
    page: int = 0,
):

    if not call.message:
        return

    # --------------------------------------------------------
    # БАЗА
    # --------------------------------------------------------

    try:

        payments = get_all_payments() or []

    except Exception as e:

        print(
            "❌ Admin payments error:",
            repr(e),
        )

        await call.message.edit_text(
            "❌ <b>Не удалось получить платежи.</b>",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # ТОЛЬКО DICT
    # --------------------------------------------------------

    payments = [
        payment
        for payment in payments
        if isinstance(payment, dict)
    ]

    # --------------------------------------------------------
    # НОВЫЕ ПЛАТЕЖИ СВЕРХУ
    # --------------------------------------------------------

    try:

        payments.sort(
            key=lambda x: (
                x.get("created_at")
                is not None,
                x.get("created_at"),
            ),
            reverse=True,
        )

    except Exception as e:

        print(
            "⚠️ Payment sorting error:",
            repr(e),
        )

    # --------------------------------------------------------
    # СТРАНИЦА
    # --------------------------------------------------------

    if page < 0:
        page = 0

    total_pages = max(
        1,
        (
            len(payments)
            + PAYMENTS_PER_PAGE
            - 1
        )
        // PAYMENTS_PER_PAGE,
    )

    if page >= total_pages:
        page = total_pages - 1

    # ========================================================
    # НЕТ ПЛАТЕЖЕЙ
    # ========================================================

    if not payments:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔄 Обновить",
                        callback_data="admin_payments",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_back",
                    )
                ],
            ]
        )

        await call.message.edit_text(
            "💳 <b>История платежей</b>\n\n"
            "Платежей пока нет.",
            parse_mode="HTML",
            reply_markup=keyboard,
        )

        return

    # ========================================================
    # СТАТИСТИКА
    # ========================================================

    pending = 0
    successful = 0
    failed = 0

    for payment in payments:

        status = str(
            payment.get("status")
            or "pending"
        ).lower().strip()

        if status == "pending":

            pending += 1

        elif status in (
            "paid",
            "success",
            "completed",
            "approved",
        ):

            successful += 1

        elif status in (
            "failed",
            "cancelled",
            "canceled",
            "rejected",
        ):

            failed += 1

    # ========================================================
    # ТЕКСТ
    # ========================================================

    text = (
        "💳 <b>История платежей</b>\n\n"

        f"📦 Всего: "
        f"<b>{len(payments)}</b>\n"

        f"⏳ Ожидают: "
        f"<b>{pending}</b>\n"

        f"✅ Успешных: "
        f"<b>{successful}</b>\n"

        f"❌ Ошибок: "
        f"<b>{failed}</b>\n\n"

        f"📄 Страница: "
        f"<b>{page + 1}/{total_pages}</b>"
    )

    try:

        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=payments_keyboard(
                payments,
                page,
            ),
        )

    except TelegramBadRequest as e:

        if (
            "message is not modified"
            not in str(e).lower()
        ):
            raise


# ============================================================
# ОТКРЫТЬ ПЛАТЕЖИ
# ============================================================

@router.callback_query(
    F.data == "admin_payments"
)
async def admin_payments(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )

        return

    await call.answer()

    await show_payments(
        call,
        page=0,
    )


# ============================================================
# ПАГИНАЦИЯ
# ============================================================

@router.callback_query(
    F.data.startswith(
        "admin_payments_page_"
    )
)
async def admin_payments_page(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )

        return

    try:

        page = int(
            call.data.replace(
                "admin_payments_page_",
                "",
                1,
            )
        )

    except (
        ValueError,
        AttributeError,
    ):

        await call.answer(
            "❌ Некорректная страница.",
            show_alert=True,
        )

        return

    await call.answer()

    await show_payments(
        call,
        page=page,
    )


# ============================================================
# ИНФОРМАЦИЯ О ПЛАТЕЖЕ
# ============================================================

@router.callback_query(
    F.data.startswith(
        "payment_info_"
    )
)
async def payment_info(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )

        return

    if not call.data:

        await call.answer(
            "❌ Некорректный платёж.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ID ПЛАТЕЖА
    # --------------------------------------------------------

    try:

        payment_id = int(
            call.data.replace(
                "payment_info_",
                "",
                1,
            )
        )

    except (
        ValueError,
        AttributeError,
    ):

        await call.answer(
            "❌ Некорректный платёж.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ПЛАТЁЖ
    # --------------------------------------------------------

    try:

        payment = get_payment(
            payment_id
        )

    except Exception as e:

        print(
            "❌ Payment lookup error:",
            repr(e),
        )

        await call.answer(
            "❌ Ошибка базы данных.",
            show_alert=True,
        )

        return

    if not payment:

        await call.answer(
            "❌ Платёж не найден.",
            show_alert=True,
        )

        return

    if not isinstance(payment, dict):

        await call.answer(
            "❌ Некорректные данные платежа.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ДАННЫЕ
    # --------------------------------------------------------

    user_id = payment.get(
        "user_id"
    )

    days = payment.get(
        "days"
    ) or 0

    external_id = (
        payment.get("payment_id")
        or payment.get("external_id")
        or "нет"
    )

    status = payment.get(
        "status"
    ) or "pending"

    provider = payment.get(
        "provider"
    ) or ""

    created_at = payment.get(
        "created_at"
    )

    paid_at = payment.get(
        "paid_at"
    )

    status_text = format_payment_status(
        status
    )

    provider_text = format_provider(
        provider
    )

    amount_text = format_amount(
        payment
    )

    # --------------------------------------------------------
    # ПОЛЬЗОВАТЕЛЬ
    # --------------------------------------------------------

    user = None

    try:

        if user_id is not None:

            user = get_user(
                int(user_id)
            )

    except Exception as e:

        print(
            "⚠️ Payment user lookup error:",
            repr(e),
        )

    username = "нет"
    first_name = "нет"

    if isinstance(user, dict):

        username = (
            user.get("username")
            or "нет"
        )

        first_name = (
            user.get("first_name")
            or "нет"
        )

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    if username != "нет":

        username_text = (
            f"@{username}"
            if not str(username).startswith("@")
            else str(username)
        )

    else:

        username_text = "нет"

    # --------------------------------------------------------
    # ТЕКСТ
    # --------------------------------------------------------

    text = (
        "💳 <b>Информация о платеже</b>\n\n"

        f"🧾 Платёж: "
        f"<b>#{payment_id}</b>\n"

        f"👤 Пользователь: "
        f"<b>{first_name}</b>\n"

        f"🆔 Telegram ID: "
        f"<code>{user_id or 'нет'}</code>\n"

        f"🔗 Username: "
        f"<b>{username_text}</b>\n\n"

        f"📦 Срок: "
        f"<b>{days} дней</b>\n"

        f"💰 Сумма: "
        f"<b>{amount_text}</b>\n"

        f"💳 Способ: "
        f"<b>{provider_text}</b>\n"

        f"📊 Статус: "
        f"<b>{status_text}</b>\n\n"

        f"🕐 Создан: "
        f"<b>{format_datetime(created_at)}</b>\n"

        f"✅ Оплачен: "
        f"<b>{format_datetime(paid_at)}</b>\n\n"

        f"🔑 ID оплаты:\n"
        f"<code>{external_id}</code>"
    )

    # ========================================================
    # КНОПКИ
    # ========================================================

    keyboard_buttons = []

    if user_id is not None:

        keyboard_buttons.append(
            [
                InlineKeyboardButton(
                    text="👤 Пользователь",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ]
        )

    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ К платежам",
                callback_data="admin_payments",
            )
        ]
    )

    keyboard_buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Админ-панель",
                callback_data="admin_back",
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_buttons
    )

    # ========================================================
    # ПОКАЗ
    # ========================================================

    if call.message:

        try:

            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        except TelegramBadRequest as e:

            if (
                "message is not modified"
                not in str(e).lower()
            ):
                raise

    await call.answer()


# ============================================================
# NO-OP
# ============================================================

@router.callback_query(
    F.data == "noop"
)
async def payment_noop(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )

        return

    await call.answer()