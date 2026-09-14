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

from datetime import datetime, timezone


router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# ФОРМАТ ДАТЫ
# ============================================================

def format_date(value) -> str:
    if not value:
        return "нет"

    try:
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")

        text = str(value).strip()

        # ISO datetime
        try:
            parsed = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )
            return parsed.strftime("%d.%m.%Y")
        except Exception:
            pass

        # Только дата
        try:
            parsed = datetime.strptime(
                text,
                "%Y-%m-%d",
            )
            return parsed.strftime("%d.%m.%Y")
        except Exception:
            pass

        return text

    except Exception:
        return str(value)


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
    # ПРОВЕРКА CALLBACK
    # --------------------------------------------------------

    if not call.data:
        await call.answer(
            "❌ Некорректные данные.",
            show_alert=True,
        )
        return

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
    # ПОЛЬЗОВАТЕЛЬ
    # --------------------------------------------------------

    try:
        user = get_user(user_id)

    except Exception as e:
        print(
            "❌ Get user for extension error:",
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
                    callback_data=f"extend_days_{user_id}_7",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 30 дней",
                    callback_data=f"extend_days_{user_id}_30",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 90 дней",
                    callback_data=f"extend_days_{user_id}_90",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 180 дней",
                    callback_data=f"extend_days_{user_id}_180",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ 365 дней",
                    callback_data=f"extend_days_{user_id}_365",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"admin_user_{user_id}",
                )
            ],
        ]
    )

    # --------------------------------------------------------
    # ТЕКУЩАЯ ДАТА
    # --------------------------------------------------------

    current_date = format_date(
        user.get("subscription_until")
    )

    # --------------------------------------------------------
    # ТЕКСТ
    # --------------------------------------------------------

    text = (
        "⏳ <b>Продление подписки</b>\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"📅 Текущий срок: <b>{current_date}</b>\n\n"
        "Выберите, на сколько дней продлить:"
    )

    # --------------------------------------------------------
    # ОТПРАВКА
    # --------------------------------------------------------

    if not call.message:
        await call.answer()
        return

    try:

        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e).lower():
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
    # CALLBACK
    # Формат:
    # extend_days_USER_ID_DAYS
    # --------------------------------------------------------

    if not call.data:
        await call.answer(
            "❌ Некорректные данные.",
            show_alert=True,
        )
        return

    try:

        parts = call.data.split("_")

        if len(parts) != 4:
            raise ValueError

        if parts[0] != "extend":
            raise ValueError

        if parts[1] != "days":
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
    # ПОЛЬЗОВАТЕЛЬ
    # --------------------------------------------------------

    try:

        user = get_user(user_id)

    except Exception as e:

        print(
            "❌ Get user before extension error:",
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

    old_date = format_date(
        user.get("subscription_until")
    )

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
            "❌ Subscription extension error:",
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
    # ОБНОВЛЯЕМ SUBSCRIPTION CONTENT
    # --------------------------------------------------------
    #
    # ВАЖНО:
    # update_subscription_file() принимает
    # ТОЛЬКО user_id.
    #
    # Новая дата уже записана в БД.
    # Функция сама получает актуального
    # пользователя и subscription_until.
    #
    # Постоянная ссылка НЕ меняется.
    # --------------------------------------------------------

    subscription_updated = False

    try:

        update_subscription_file(
            user_id
        )

        subscription_updated = True

    except Exception as e:

        print(
            "❌ Subscription content update error:",
            repr(e),
        )

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ОБНОВЛЁННОГО ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    try:

        updated_user = get_user(
            user_id
        )

    except Exception as e:

        print(
            "⚠️ Get updated user error:",
            repr(e),
        )

        updated_user = None

    # --------------------------------------------------------
    # ИМЯ
    # --------------------------------------------------------

    username = "нет"

    if updated_user:

        username = (
            updated_user.get("username")
            or updated_user.get("first_name")
            or "нет"
        )

    # --------------------------------------------------------
    # НОВАЯ ДАТА
    # --------------------------------------------------------

    new_date_text = format_date(
        new_date
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

    # --------------------------------------------------------
    # ПОКАЗЫВАЕМ РЕЗУЛЬТАТ
    # --------------------------------------------------------

    if call.message:

        try:

            await call.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=back_to_user_keyboard(
                    user_id
                ),
            )

        except TelegramBadRequest as e:

            if "message is not modified" not in str(e).lower():
                raise

    await call.answer(
        f"✅ +{days} дней"
    )