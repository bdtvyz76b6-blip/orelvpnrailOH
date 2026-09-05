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

    try:
        current_date = user[4] or "нет"
    except (IndexError, TypeError):
        current_date = "нет"

    # --------------------------------------------------------
    # ПОКАЗЫВАЕМ ВЫБОР
    # --------------------------------------------------------

    text = (
        "⏳ <b>Продление подписки</b>\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"📅 Текущий срок: <b>{current_date}</b>\n\n"
        "Выберите, на сколько дней продлить:"
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

    try:
        old_date = user[4] or "нет"
    except (IndexError, TypeError):
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
    # ОБНОВЛЯЕМ GITHUB
    # --------------------------------------------------------

    github_updated = False

    try:
        github_date = datetime.strptime(
            str(new_date),
            "%Y-%m-%d",
        ).strftime("%d.%m.%Y")

        update_subscription_file(
            user_id,
            github_date,
        )

        github_updated = True

    except Exception as e:
        print(
            "GitHub update error:",
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
        try:
            username = user[1] or "нет"
        except (IndexError, TypeError):
            username = "нет"

    # --------------------------------------------------------
    # СТАТУС GITHUB
    # --------------------------------------------------------

    if github_updated:
        github_status = (
            "🟢 Файл подписки обновлён"
        )
    else:
        github_status = (
            "🟡 Подписка продлена в БД,\n"
            "но GitHub обновить не удалось"
        )

    # --------------------------------------------------------
    # РЕЗУЛЬТАТ
    # --------------------------------------------------------

    text = (
        "✅ <b>Подписка успешно продлена</b>\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"📅 Было: <b>{old_date}</b>\n"
        f"➕ Добавлено: <b>{days} дней</b>\n"
        f"📅 Стало: <b>{new_date}</b>\n\n"
        f"{github_status}"
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