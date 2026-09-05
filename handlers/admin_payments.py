from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import (
    get_payments,
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
# ПОЛУЧЕНИЕ ПОЛЯ ПЛАТЕЖА
# ============================================================

def payment_field(payment, index, default=None):
    try:
        if isinstance(payment, dict):
            keys = [
                "id",
                "user_id",
                "days",
                "photo",
                "payment_id",
                "status",
                "created_at",
            ]

            if index < len(keys):
                return payment.get(
                    keys[index],
                    default,
                )

            return default

        return payment[index]

    except (IndexError, KeyError, TypeError):
        return default


# ============================================================
# СТАТУС ПЛАТЕЖА
# ============================================================

def format_payment_status(status):
    status = str(
        status or "pending"
    ).lower()

    statuses = {
        "pending": "⏳ Ожидает",
        "paid": "✅ Оплачен",
        "success": "✅ Оплачен",
        "completed": "✅ Завершён",
        "approved": "✅ Подтверждён",
        "failed": "❌ Ошибка",
        "cancelled": "🚫 Отменён",
        "canceled": "🚫 Отменён",
    }

    return statuses.get(
        status,
        f"❔ {status}",
    )


# ============================================================
# КЛАВИАТУРА ПЛАТЕЖЕЙ
# ============================================================

def payments_keyboard(
    payments,
    page,
):
    buttons = []

    start = page * PAYMENTS_PER_PAGE
    end = start + PAYMENTS_PER_PAGE

    page_payments = payments[start:end]

    for payment in page_payments:
        payment_id = payment_field(
            payment,
            0,
            0,
        )

        user_id = payment_field(
            payment,
            1,
            0,
        )

        days = payment_field(
            payment,
            2,
            0,
        )

        status = payment_field(
            payment,
            5,
            "pending",
        )

        status_text = format_payment_status(
            status
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

    # --------------------------------------------------------
    # ПАГИНАЦИЯ
    # --------------------------------------------------------

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
            text=f"{page + 1}/{total_pages}",
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
# СПИСОК ПЛАТЕЖЕЙ
# ============================================================

async def show_payments(
    call: CallbackQuery,
    page: int = 0,
):
    try:
        payments = get_payments() or []

    except Exception as e:
        print(
            "Admin payments error:",
            repr(e),
        )

        await call.message.edit_text(
            "❌ Не удалось получить платежи."
        )

        return

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

    # --------------------------------------------------------
    # НЕТ ПЛАТЕЖЕЙ
    # --------------------------------------------------------

    if not payments:
        await call.message.edit_text(
            "💳 <b>История платежей</b>\n\n"
            "Платежей пока нет.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="admin_back",
                        )
                    ]
                ]
            ),
        )

        return

    # --------------------------------------------------------
    # СТАТИСТИКА
    # --------------------------------------------------------

    pending = 0
    successful = 0
    failed = 0

    for payment in payments:
        status = str(
            payment_field(
                payment,
                5,
                "pending",
            )
            or "pending"
        ).lower()

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
        ):
            failed += 1

    text = (
        "💳 <b>История платежей</b>\n\n"
        f"📦 Всего: <b>{len(payments)}</b>\n"
        f"⏳ Ожидают: <b>{pending}</b>\n"
        f"✅ Успешных: <b>{successful}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>\n\n"
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
        if "message is not modified" not in str(e):
            raise


# ============================================================
# ОТКРЫТИЕ ПЛАТЕЖЕЙ
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
    F.data.startswith("admin_payments_page_")
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

    except (ValueError, AttributeError):
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
    F.data.startswith("payment_info_")
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

    try:
        payment_id = int(
            call.data.replace(
                "payment_info_",
                "",
                1,
            )
        )

    except (ValueError, AttributeError):
        await call.answer(
            "❌ Некорректный платёж.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ПЛАТЕЖИ
    # --------------------------------------------------------

    try:
        payments = get_payments() or []

    except Exception as e:
        print(
            "Payment lookup error:",
            repr(e),
        )

        await call.answer(
            "❌ Ошибка базы данных.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ИЩЕМ ПЛАТЁЖ
    # --------------------------------------------------------

    payment = None

    for item in payments:
        item_id = payment_field(
            item,
            0,
            None,
        )

        try:
            if int(item_id) == payment_id:
                payment = item
                break

        except (ValueError, TypeError):
            continue

    if not payment:
        await call.answer(
            "❌ Платёж не найден.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ДАННЫЕ ПЛАТЕЖА
    # --------------------------------------------------------

    user_id = payment_field(
        payment,
        1,
        0,
    )

    days = payment_field(
        payment,
        2,
        0,
    )

    payment_external_id = payment_field(
        payment,
        4,
        "",
    )

    status = payment_field(
        payment,
        5,
        "pending",
    )

    created_at = payment_field(
        payment,
        6,
        "",
    )

    status_text = format_payment_status(
        status
    )

    # --------------------------------------------------------
    # ДАННЫЕ ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    user = None

    try:
        user = get_user(
            int(user_id)
        )

    except Exception as e:
        print(
            "Payment user lookup error:",
            repr(e),
        )

    username = "нет"
    first_name = "нет"

    if user:
        try:
            username = user[1] or "нет"
        except (IndexError, TypeError):
            pass

        try:
            first_name = user[2] or "нет"
        except (IndexError, TypeError):
            pass

    # --------------------------------------------------------
    # ФОРМАТ ДАТЫ
    # --------------------------------------------------------

    created_text = str(
        created_at or "нет"
    )

    try:
        if hasattr(created_at, "strftime"):
            created_text = created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # ID ПЛАТЕЖА
    # --------------------------------------------------------

    external_id_text = (
        str(payment_external_id)
        if payment_external_id
        else "нет"
    )

    # --------------------------------------------------------
    # ИНФОРМАЦИЯ
    # --------------------------------------------------------

    text = (
        "💳 <b>Информация о платеже</b>\n\n"
        f"🧾 Платёж: <b>#{payment_id}</b>\n"
        f"👤 Пользователь: "
        f"<b>{first_name}</b>\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🔗 Username: "
        f"@{username if username != 'нет' else 'нет'}\n\n"
        f"📦 Срок: <b>{days} дней</b>\n"
        f"📊 Статус: <b>{status_text}</b>\n"
        f"🕐 Создан: <b>{created_text}</b>\n"
        f"🔑 ID оплаты: "
        f"<code>{external_id_text}</code>\n\n"
        "💰 Способ: <b>СБП</b>\n"
        "ℹ️ Сумма: <b>недоступна в текущей БД</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Пользователь",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К платежам",
                    callback_data="admin_payments",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Админ-панель",
                    callback_data="admin_back",
                )
            ],
        ]
    )

    try:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await call.answer()


# ============================================================
# NO-OP КНОПКА
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