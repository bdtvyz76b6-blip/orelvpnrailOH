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
    get_subscription_link,
    disable_subscription
)

from github_update import (
    sync_servers_update,
    expire_subscription
)


router = Router()


# =====================
# ПРОВЕРКА АДМИНА
# =====================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# =====================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =====================

@router.callback_query(F.data == "admin_users")
async def show_users(call: CallbackQuery):

    if not is_admin(call.from_user.id):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

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

    if not is_admin(call.from_user.id):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

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

    user = get_user(user_id)

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    link = get_subscription_link(
        user_id
    )

    subscription = user[3]
    subscription_until = user[4]

    # =====================
    # СТАТУС
    # =====================

    status = "🔴 Неактивен"

    if subscription in (
        "vip",
        "trial"
    ) and subscription_until:

        try:

            from datetime import datetime

            expire_date = datetime.strptime(
                subscription_until,
                "%Y-%m-%d"
            )

            if expire_date.date() >= datetime.now().date():

                status = "🟢 Активен"

            else:

                status = "🔴 Истёк"

        except Exception:

            status = "⚠️ Ошибка даты"

    # =====================
    # ТАРИФ
    # =====================

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "❌ Нет подписки"

    # =====================
    # ТЕКСТ
    # =====================

    text = (
        "👤 <b>Пользователь</b>\n\n"

        f"🆔 ID: <code>{user[0]}</code>\n"

        f"👤 Username: "
        f"@{user[1] or 'нет'}\n"

        f"🧑‍💻 Имя: "
        f"{user[2] or 'нет'}\n\n"

        f"🎫 Тариф: {tariff}\n"

        f"📊 Статус: {status}\n"

        f"📅 До: "
        f"{subscription_until or 'нет'}\n\n"

        f"🔗 Подписка:\n"
        f"{link or 'нет'}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔗 Получить ссылку",
                    callback_data=f"admin_get_link_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=f"extend_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Забрать подписку",
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

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):

            raise

    await call.answer()


# =====================
# ПОЛУЧИТЬ ССЫЛКУ
# =====================

@router.callback_query(
    F.data.startswith("admin_get_link_")
)
async def admin_get_link(call: CallbackQuery):

    if not is_admin(call.from_user.id):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    try:

        user_id = int(
            call.data.replace(
                "admin_get_link_",
                ""
            )
        )

    except ValueError:

        await call.answer(
            "❌ Неверный ID",
            show_alert=True
        )

        return

    user = get_user(user_id)

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    link = get_subscription_link(
        user_id
    )

    if not link:

        await call.answer(
            "❌ У пользователя нет ссылки",
            show_alert=True
        )

        return

    await call.message.answer(
        f"🔗 <b>Подписка пользователя</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"{link}",
        parse_mode="HTML"
    )

    await call.answer()


# =====================
# ЗАБРАТЬ ПОДПИСКУ
# =====================

@router.callback_query(
    F.data.startswith("disable_")
)
async def disable_user_subscription(
    call: CallbackQuery
):

    if not is_admin(call.from_user.id):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    try:

        user_id = int(
            call.data.replace(
                "disable_",
                ""
            )
        )

    except ValueError:

        await call.answer(
            "❌ Неверный ID",
            show_alert=True
        )

        return

    user = get_user(user_id)

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    try:

        # =====================
        # ОТКЛЮЧАЕМ В БД
        # =====================

        disable_subscription(
            user_id
        )

        # =====================
        # ДЕЛАЕМ GITHUB-ФАЙЛ
        # ПРОСРОЧЕННЫМ
        # =====================

        expire_subscription(
            user_id
        )

        await call.answer(
            "✅ Подписка забрана"
        )

        # =====================
        # ОБНОВЛЯЕМ ПРОФИЛЬ
        # =====================

        user = get_user(
            user_id
        )

        link = get_subscription_link(
            user_id
        )

        text = (
            "👤 <b>Пользователь</b>\n\n"

            f"🆔 ID: <code>{user[0]}</code>\n"

            f"👤 Username: "
            f"@{user[1] or 'нет'}\n"

            f"🧑‍💻 Имя: "
            f"{user[2] or 'нет'}\n\n"

            "🎫 Тариф: ❌ Нет подписки\n"
            "📊 Статус: 🔴 Неактивен\n"
            "📅 До: —\n\n"

            f"🔗 Ссылка:\n"
            f"{link or 'нет'}"
        )

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
                        text="⬅️ Назад",
                        callback_data="admin_users"
                    )
                ]

            ]
        )

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"❌ Ошибка отключения "
            f"{user_id}: {e}"
        )

        await call.answer(
            "❌ Ошибка отключения",
            show_alert=True
        )


# =====================
# ОБНОВЛЕНИЕ СЕРВЕРОВ
# =====================

@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(
    call: CallbackQuery
):

    if not is_admin(call.from_user.id):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    await call.answer(
        "🔄 Обновление началось..."
    )

    status_message = await call.message.answer(
        "🔄 <b>Обновляю серверы...</b>\n\n"
        "⏳ Загружаю актуальный servers.txt\n"
        "⏳ Обновляю подписки пользователей...",
        parse_mode="HTML"
    )

    try:

        result = sync_servers_update()

        await status_message.edit_text(
            "✅ <b>Серверы обновлены!</b>\n\n"

            f"👥 Обновлено: "
            f"{result.get('updated', 0)}\n"

            f"⏭ Пропущено: "
            f"{result.get('skipped', 0)}\n"

            f"⛔ Просрочено: "
            f"{result.get('expired', 0)}\n"

            f"❌ Ошибок: "
            f"{result.get('errors', 0)}",
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"❌ ADMIN SYNC ERROR: {e}"
        )

        await status_message.edit_text(
            "❌ <b>Не удалось обновить серверы.</b>\n\n"
            f"Ошибка:\n<code>{e}</code>",
            parse_mode="HTML"
        )