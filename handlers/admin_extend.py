from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import (
    extend_subscription,
    get_user,
)

from github_update import update_subscription_file

from datetime import datetime


router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# КНОПКА НАЗАД К ПОЛЬЗОВАТЕЛЮ
# ============================================================

def back_to_user_keyboard(user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К пользователю",
                    callback_data=f"admin_user_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В админ-панель",
                    callback_data="admin_back",
                )
            ],
        ]
    )


# ============================================================
# ВЫБОР СРОКА ПРОДЛЕНИЯ
# ============================================================

@router.callback_query(
    F.data.startswith("extend_")
    & ~F.data.startswith("extend_days_")
)
async def choose_extend(
    call: CallbackQuery,
):

    # --------------------------------------------------------
    # ПРОВЕРКА АДМИНА
    # --------------------------------------------------------

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ПОЛУЧАЕМ USER ID
    # --------------------------------------------------------

    try:
        user_id = int(
            call.data.replace(
                "extend_",
                "",
                1,
            )
        )

    except (ValueError, AttributeError):
        await call.answer(
            "❌ Некорректный пользователь.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ПРОВЕРЯЕМ ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    try:
        user = get_user(user_id)

    except Exception as e:
        print(
            "Get user for extension error:",
            repr(e),
        )
        user = None

    if not user:
        await call.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # КЛАВИАТУРА
    # --------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ 7 дней",
                    callback_data=(
                        f"extend_days_{user_id}_7"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 30 дней",
                    callback_data=(
                        f"extend_days_{user_id}_30"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 90 дней",
                    callback_data=(
                        f"extend_days_{user_id}_90"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 180 дней",
                    callback_data=(
                        f"extend_days_{user_id}_180"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 365 дней",
                    callback_data=(
                        f"extend_days_{user_id}_365"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ],
        ]
    )

    # --------------------------------------------------------
    # ТЕКУЩАЯ ДАТА
    # --------------------------------------------------------

    current_date = user.get(
        "subscription_until"
    )

    if current_date:
        current_date = str(
            current_date
        )
    else:
        current_date = "нет"

    # --------------------------------------------------------
    # ПОКАЗЫВАЕМ ВЫБОР
    # --------------------------------------------------------

    text = (
        "⏳ <b>Продление подписки</b>\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"📅 Текущий срок: "
        f"<b>{current_date}</b>\n\n"
        "Выберите, на сколько дней "
        "продлить:"
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
# ПРОДЛЕНИЕ
# ============================================================

@router.callback_query(
    F.data.startswith("extend_days_")
)
async def extend_days(
    call: CallbackQuery,
):

    # --------------------------------------------------------
    # ПРОВЕРКА АДМИНА
    # --------------------------------------------------------

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # РАЗБИРАЕМ CALLBACK
    # --------------------------------------------------------

    try:
        parts = call.data.split("_")

        if len(parts) != 4:
            raise ValueError

        user_id = int(parts[2])
        days = int(parts[3])

    except (
        ValueError,
        TypeError,
        AttributeError,
    ):
        await call.answer(
            "❌ Некорректные данные.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # РАЗРЕШЁННЫЕ СРОКИ
    # --------------------------------------------------------

    allowed_days = {
        7,
        30,
        90,
        180,
        365,
    }

    if days not in allowed_days:
        await call.answer(
            "❌ Такой срок недоступен.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ПРОВЕРЯЕМ ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    try:
        user = get_user(user_id)

    except Exception as e:
        print(
            "Get user before extension error:",
            repr(e),
        )
        user = None

    if not user:
        await call.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # СТАРАЯ ДАТА
    # --------------------------------------------------------

    old_date = user.get(
        "subscription_until"
    )

    if old_date:
        old_date = str(old_date)
    else:
        old_date = "нет"

    # --------------------------------------------------------
    # ПРОДЛЕВАЕМ В БАЗЕ
    # --------------------------------------------------------

    try:
        new_date = extend_subscription(
            user_id,
            days,
        )

    except Exception as e:
        print(
            "Subscription extension error:",
            repr(e),
        )

        await call.answer(
            "❌ Ошибка при продлении.",
            show_alert=True,
        )

        return

    if not new_date:
        await call.answer(
            "❌ Не удалось получить новую дату.",
            show_alert=True,
        )
        return

    # --------------------------------------------------------
    # ОБНОВЛЯЕМ СОДЕРЖИМОЕ ПОДПИСКИ
    # --------------------------------------------------------
    #
    # ВАЖНО:
    # GitHub больше НЕ используется для
    # users/<id>.txt.
    #
    # update_subscription_file()
    # теперь обновляет subscription_content
    # в PostgreSQL.
    #
    # Постоянная ссылка пользователя
    # при этом НЕ меняется.
    # --------------------------------------------------------

    subscription_updated = False

    try:

        update_subscription_file(
            user_id,
            new_date,
        )

        subscription_updated = True

    except Exception as e:

        print(
            "Subscription content update error:",
            repr(e),
        )

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ОБНОВЛЁННОГО ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    try:
        user = get_user(user_id)

    except Exception:
        user = None

    username = "нет"

    if user:

        username = (
            user.get("username")
            or user.get("first_name")
            or "нет"
        )

    # --------------------------------------------------------
    # СТАТУС ОБНОВЛЕНИЯ
    # --------------------------------------------------------

    if subscription_updated:

        subscription_status = (
            "🟢 Содержимое подписки обновлено"
        )

    else:

        subscription_status = (
            "🟡 Подписка продлена в БД,\n"
            "но содержимое подписки "
            "обновить не удалось"
        )

    # --------------------------------------------------------
    # ФОРМАТ НОВОЙ ДАТЫ
    # --------------------------------------------------------

    if isinstance(new_date, datetime):

        new_date_text = new_date.strftime(
            "%d.%m.%Y"
        )

    else:

        new_date_text = str(
            new_date
        )

        try:

            new_date_text = datetime.strptime(
                new_date_text,
                "%Y-%m-%d",
            ).strftime(
                "%d.%m.%Y"
            )

        except Exception:

            pass

    # --------------------------------------------------------
    # РЕЗУЛЬТАТ
    # --------------------------------------------------------

    text = (
        "✅ <b>Подписка успешно продлена</b>\n\n"

        f"👤 Пользователь: "
        f"<b>{username}</b>\n"

        f"🆔 ID: "
        f"<code>{user_id}</code>\n\n"

        f"📅 Было: "
        f"<b>{old_date}</b>\n"

        f"➕ Добавлено: "
        f"<b>{days} дней</b>\n"

        f"📅 Стало: "
        f"<b>{new_date_text}</b>\n\n"

        f"{subscription_status}\n\n"

        "🔗 Постоянная ссылка пользователя "
        "не изменилась."
    )

    try:

        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_to_user_keyboard(
                user_id
            ),
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise

    await call.answer(
        f"✅ +{days} дней"
    )