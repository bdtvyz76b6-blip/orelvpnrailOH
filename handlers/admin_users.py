from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.exceptions import TelegramBadRequest

from datetime import datetime

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


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ============================================================
# ПРОВЕРКА СТАТУСА ПОДПИСКИ
# ============================================================

def get_subscription_status(
    subscription,
    subscription_until
):

    # --------------------------------------------------------
    # Нет подписки
    # --------------------------------------------------------

    if subscription not in (
        "vip",
        "trial"
    ):

        return (
            "🔴 Неактивен",
            0
        )

    # --------------------------------------------------------
    # Нет даты
    # --------------------------------------------------------

    if not subscription_until:

        return (
            "🔴 Неактивен",
            0
        )

    # --------------------------------------------------------
    # Парсим дату
    # --------------------------------------------------------

    try:

        expire_date = datetime.strptime(
            str(subscription_until),
            "%Y-%m-%d"
        ).date()

    except Exception:

        return (
            "⚠️ Ошибка даты",
            0
        )

    # --------------------------------------------------------
    # Сегодня
    # --------------------------------------------------------

    today = datetime.now().date()

    # --------------------------------------------------------
    # ИСТЁК
    #
    # Важно:
    # если дата равна сегодняшней,
    # считаем подписку истёкшей.
    # --------------------------------------------------------

    if expire_date <= today:

        return (
            "⛔ Истёк",
            0
        )

    # --------------------------------------------------------
    # Активен
    # --------------------------------------------------------

    days = (
        expire_date - today
    ).days

    return (
        "🟢 Активен",
        days
    )


# ============================================================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

@router.callback_query(
    F.data == "admin_users"
)
async def show_users(
    call: CallbackQuery
):

    # --------------------------------------------------------
    # Проверка администратора
    # --------------------------------------------------------

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # Получаем пользователей
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Кнопки
    # --------------------------------------------------------

    buttons = []

    for user in users[:20]:

        user_id = user[0]

        username = (
            user[1]
            or "без username"
        )

        # ----------------------------------------------------
        # Получаем статус
        # ----------------------------------------------------

        subscription = user[3]

        subscription_until = user[4]

        status, days = get_subscription_status(
            subscription,
            subscription_until
        )

        # ----------------------------------------------------
        # Текст кнопки
        # ----------------------------------------------------

        if days > 0:

            text = (
                f"👤 {username} "
                f"• 🟢 {days} д."
            )

        elif status == "⛔ Истёк":

            text = (
                f"👤 {username} "
                f"• ⛔ Истёк"
            )

        else:

            text = (
                f"👤 {username}"
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=(
                        f"admin_user_{user_id}"
                    )
                )
            ]
        )

    # --------------------------------------------------------
    # Назад
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Показываем
    # --------------------------------------------------------

    try:

        await call.message.edit_text(
            "👥 <b>Пользователи</b>\n\n"
            "Выбери пользователя:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):

            raise

    await call.answer()


# ============================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================

@router.callback_query(
    F.data.startswith("admin_user_")
)
async def user_profile(
    call: CallbackQuery
):

    # --------------------------------------------------------
    # Проверка администратора
    # --------------------------------------------------------

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # ID пользователя
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Получаем пользователя
    # --------------------------------------------------------

    user = get_user(
        user_id
    )

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # Данные
    # --------------------------------------------------------

    subscription = user[3]

    subscription_until = user[4]

    # --------------------------------------------------------
    # Username
    # --------------------------------------------------------

    username = (
        user[1]
        or "нет"
    )

    # --------------------------------------------------------
    # Имя
    # --------------------------------------------------------

    first_name = (
        user[2]
        or "нет"
    )

    # --------------------------------------------------------
    # Ссылка
    # --------------------------------------------------------

    link = get_subscription_link(
        user_id
    )

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    status, days = get_subscription_status(
        subscription,
        subscription_until
    )

    # --------------------------------------------------------
    # Тариф
    # --------------------------------------------------------

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "❌ Нет подписки"

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    if subscription_until:

        try:

            expire_date = datetime.strptime(
                str(subscription_until),
                "%Y-%m-%d"
            )

            date_text = expire_date.strftime(
                "%d.%m.%Y"
            )

        except Exception:

            date_text = str(
                subscription_until
            )

    else:

        date_text = "нет"

    # --------------------------------------------------------
    # Осталось
    # --------------------------------------------------------

    if days > 0:

        days_text = (
            f"⏳ Осталось: {days} д."
        )

    else:

        days_text = (
            "⏳ Осталось: 0 д."
        )

    # ========================================================
    # ТЕКСТ
    # ========================================================

    text = (
        "👤 <b>Пользователь</b>\n\n"

        f"🆔 ID: "
        f"<code>{user_id}</code>\n"

        f"👤 Username: "
        f"@{username}\n\n"

        f"🧑‍💻 Имя: "
        f"{first_name}\n\n"

        f"🎫 Тариф: "
        f"{tariff}\n"

        f"📊 Статус: "
        f"{status}\n"

        f"📅 До: "
        f"{date_text}\n"

        f"{days_text}\n\n"

        f"🔗 Подписка:\n"
        f"{link or 'нет'}"
    )

    # ========================================================
    # КНОПКИ
    # ========================================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=(
                        f"extend_{user_id}"
                    )
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=(
                        f"disable_{user_id}"
                    )
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

    # ========================================================
    # ПОКАЗЫВАЕМ
    # ========================================================

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


# ============================================================
# ОБНОВЛЕНИЕ СЕРВЕРОВ
# ============================================================

@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(
    call: CallbackQuery
):

    # --------------------------------------------------------
    # Проверка администратора
    # --------------------------------------------------------

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # Уведомление
    # --------------------------------------------------------

    await call.answer(
        "🔄 Обновление началось..."
    )

    # --------------------------------------------------------
    # Сообщение
    # --------------------------------------------------------

    status_message = await call.message.answer(
        "🔄 <b>Обновляю серверы...</b>\n\n"
        "⏳ Проверяю активные и "
        "истёкшие подписки...",
        parse_mode="HTML"
    )

    # --------------------------------------------------------
    # Синхронизация
    # --------------------------------------------------------

    try:

        result = sync_servers_update()

        await status_message.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"

            f"🟢 Активных обновлено: "
            f"{result['updated']}\n"

            f"⛔ Истёкших обновлено: "
            f"{result['expired']}\n"

            f"⏭ Пропущено: "
            f"{result['skipped']}\n"

            f"❌ Ошибок: "
            f"{result['errors']}",
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"❌ Ошибка синхронизации: {e}"
        )

        try:

            await status_message.edit_text(
                "❌ <b>Не удалось обновить серверы.</b>\n\n"
                f"Ошибка:\n"
                f"<code>{str(e)}</code>",
                parse_mode="HTML"
            )

        except TelegramBadRequest:

            pass