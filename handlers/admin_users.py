from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import (
    get_all_users,
    get_user,
    get_subscription_link
)

from github_update import (
    sync_servers_update
)


router = Router()


# =====================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =====================

@router.callback_query(F.data == "admin_users")
async def show_users(call: CallbackQuery):

    # =====================
    # ПРОВЕРКА АДМИНА
    # =====================

    if call.from_user.id not in ADMIN_IDS:

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # =====================
    # ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЕЙ
    # =====================

    users = get_all_users()

    if not users:

        try:

            await call.message.edit_text(
                "👥 Пользователей пока нет"
            )

        except TelegramBadRequest:
            pass

        await call.answer()

        return

    # =====================
    # КНОПКИ
    # =====================

    buttons = []

    for user in users[:20]:

        user_id = user[0]

        username = (
            user[1]
            or "без username"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"👤 {username}",
                    callback_data=f"admin_user_{user_id}"
                )
            ]
        )

    # =====================
    # НАЗАД
    # =====================

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_back"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    # =====================
    # ПОКАЗЫВАЕМ
    # =====================

    try:

        await call.message.edit_text(
            "👥 Пользователи:",
            reply_markup=keyboard
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):

            raise

    await call.answer()


# =====================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# =====================

@router.callback_query(
    F.data.startswith("admin_user_")
)
async def user_profile(call: CallbackQuery):

    # =====================
    # ПРОВЕРКА
    # =====================

    if call.from_user.id not in ADMIN_IDS:

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # =====================
    # ID
    # =====================

    try:

        user_id = int(
            call.data.replace(
                "admin_user_",
                ""
            )
        )

    except ValueError:

        await call.answer(
            "❌ Неверный ID",
            show_alert=True
        )

        return

    # =====================
    # ПОЛЬЗОВАТЕЛЬ
    # =====================

    user = get_user(user_id)

    if not user:

        await call.answer(
            "Пользователь не найден",
            show_alert=True
        )

        return

    # =====================
    # ССЫЛКА
    # =====================

    link = get_subscription_link(
        user_id
    )

    # =====================
    # СТАТУС
    # =====================

    subscription = user[3]
    subscription_until = user[4]

    if subscription in (
        "vip",
        "trial"
    ) and subscription_until:

        status = "🟢 Активен"

    else:

        status = "🔴 Неактивен"

    # =====================
    # ТЕКСТ
    # =====================

    text = (
        "👤 Пользователь\n\n"

        f"🆔 ID: {user[0]}\n"

        f"👤 Username: "
        f"@{user[1] or 'нет'}\n\n"

        f"🧑‍💻 Имя: "
        f"{user[2] or 'нет'}\n\n"

        f"📦 Тариф: "
        f"{subscription or 'нет'}\n"

        f"📅 До: "
        f"{subscription_until or 'нет'}\n\n"

        f"🔗 Подписка:\n"
        f"{link or 'нет'}\n\n"

        f"📊 Статус: "
        f"{status}"
    )

    # =====================
    # КНОПКИ
    # =====================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=f"extend_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=f"disable_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_users"
                )
            ]

        ]
    )

    # =====================
    # ПОКАЗ
    # =====================

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):

            raise

    await call.answer()


# =====================
# ОБНОВЛЕНИЕ СЕРВЕРОВ
# =====================

@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(call: CallbackQuery):

    # =====================
    # ПРОВЕРКА АДМИНА
    # =====================

    if call.from_user.id not in ADMIN_IDS:

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # =====================
    # УВЕДОМЛЕНИЕ
    # =====================

    await call.answer(
        "🔄 Обновление началось..."
    )

    # =====================
    # СООБЩЕНИЕ
    # =====================

    status_message = await call.message.answer(
        "🔄 Обновляю серверы...\n\n"
        "⏳ Пожалуйста, подожди."
    )

    try:

        # =====================
        # СИНХРОНИЗАЦИЯ
        # =====================

        result = sync_servers_update()

        # =====================
        # РЕЗУЛЬТАТ
        # =====================

        await status_message.edit_text(
            "✅ Серверы обновлены!\n\n"

            f"👥 Обновлено: "
            f"{result['updated']}\n"

            f"⏭ Пропущено: "
            f"{result['skipped']}\n"

            f"⛔ Просрочено: "
            f"{result['expired']}\n"

            f"❌ Ошибок: "
            f"{result['errors']}"
        )

    except Exception as e:

        await status_message.edit_text(
            "❌ Не удалось обновить серверы.\n\n"
            f"Ошибка:\n"
            f"{e}"
        )