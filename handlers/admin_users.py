from aiogram import Router, F

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.exceptions import TelegramBadRequest

from datetime import datetime

from html import escape

from config import ADMIN_IDS

from database import (
    get_all_users,
    get_user,
    get_subscription_link,
    disable_subscription,
)

from github_update import (
    sync_servers_update,
)


router = Router()


# ============================================================
# НАСТРОЙКИ САЙТА
# ============================================================

import os

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com",
).rstrip("/")

SUBSCRIPTION_PREFIX = os.getenv(
    "SUBSCRIPTION_PREFIX",
    "2ix847xy",
).strip()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


# ============================================================
# URL ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_user_urls(user_id):

    token = (
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )

    site_url = (
        f"{PUBLIC_SITE_URL}"
        f"/s/{token}"
    )

    subscription_url = (
        f"{PUBLIC_SITE_URL}"
        f"/sub/{token}"
    )

    return (
        site_url,
        subscription_url,
    )


# ============================================================
# СТАТУС ПОДПИСКИ
# ============================================================

def get_subscription_status(
    subscription,
    subscription_until,
):

    if subscription not in (
        "vip",
        "trial",
    ):

        return (
            "🔴 Неактивен",
            0,
        )

    if not subscription_until:

        return (
            "🔴 Неактивен",
            0,
        )

    try:

        expire_date = datetime.strptime(
            str(subscription_until),
            "%Y-%m-%d",
        ).date()

    except Exception:

        return (
            "⚠️ Ошибка даты",
            0,
        )

    today = datetime.now().date()

    # --------------------------------------------------------
    # Дата окончания активна до конца этого дня
    # --------------------------------------------------------

    if expire_date < today:

        return (
            "⛔ Истёк",
            0,
        )

    days = (
        expire_date - today
    ).days

    return (
        "🟢 Активен",
        days,
    )


# ============================================================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

@router.callback_query(
    F.data == "admin_users"
)
async def show_users(
    call: CallbackQuery,
):

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    users = get_all_users()

    if not users:

        try:

            await call.message.edit_text(
                "👥 <b>Пользователей пока нет</b>",
                parse_mode="HTML",
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

        subscription = user[3]

        subscription_until = user[4]

        status, days = (
            get_subscription_status(
                subscription,
                subscription_until,
            )
        )

        if days > 0:

            text = (
                f"👤 {username}"
                f"  •  🟢 {days} д."
            )

        elif status == "⛔ Истёк":

            text = (
                f"👤 {username}"
                f"  •  ⛔ Истёк"
            )

        else:

            text = (
                f"👤 {username}"
                f"  •  🔴"
            )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=(
                        f"admin_user_{user_id}"
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    try:

        await call.message.edit_text(
            "👥 <b>Пользователи</b>\n\n"
            "Выбери пользователя:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except TelegramBadRequest as e:

        if (
            "message is not modified"
            not in str(e)
        ):

            raise

    await call.answer()


# ============================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================

@router.callback_query(
    F.data.startswith("admin_user_")
)
async def user_profile(
    call: CallbackQuery,
):

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    try:

        user_id = int(
            call.data.replace(
                "admin_user_",
                "",
            )
        )

    except ValueError:

        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )

        return

    user = get_user(user_id)

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # ========================================================
    # ДАННЫЕ
    # ========================================================

    subscription = user[3]

    subscription_until = user[4]

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    # ========================================================
    # СТАТУС
    # ========================================================

    status, days = (
        get_subscription_status(
            subscription,
            subscription_until,
        )
    )

    # ========================================================
    # ТАРИФ
    # ========================================================

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "❌ Нет подписки"

    # ========================================================
    # ДАТА
    # ========================================================

    if subscription_until:

        try:

            expire_date = datetime.strptime(
                str(subscription_until),
                "%Y-%m-%d",
            )

            date_text = (
                expire_date.strftime(
                    "%d.%m.%Y"
                )
            )

        except Exception:

            date_text = str(
                subscription_until
            )

    else:

        date_text = "нет"

    # ========================================================
    # ССЫЛКИ
    # ========================================================

    site_url, subscription_url = (
        get_user_urls(user_id)
    )

    # Старая ссылка из БД.
    # Показываем её только как fallback/информацию.
    stored_link = (
        get_subscription_link(
            user_id
        )
        or ""
    )

    # ========================================================
    # ЭКРАН ПРОФИЛЯ
    # ========================================================

    text = (
        "👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🆔 <b>ID</b>\n"
        f"<code>{user_id}</code>\n\n"

        "👤 <b>Username</b>\n"
        f"@{escape(str(username))}\n\n"

        "🧑‍💻 <b>Имя</b>\n"
        f"{escape(str(first_name))}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🎫 <b>Тариф</b>\n"
        f"{tariff}\n\n"

        "📊 <b>Статус</b>\n"
        f"{status}\n\n"

        "📅 <b>Действует до</b>\n"
        f"{date_text}\n\n"

        "⏳ <b>Осталось</b>\n"
        f"{days} д.\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🌐 <b>САЙТ</b>\n"
        f"<code>{escape(site_url)}</code>\n\n"

        "🔗 <b>ПОДПИСКА</b>\n"
        f"<code>{escape(subscription_url)}</code>"
    )

    # ========================================================
    # КНОПКИ
    # ========================================================

    buttons = []

    # --------------------------------------------------------
    # Сайт + подписка
    # --------------------------------------------------------

    buttons.append(
        [
            InlineKeyboardButton(
                text="🌐 Открыть сайт",
                url=site_url,
            ),
            InlineKeyboardButton(
                text="🔗 Открыть подписку",
                url=subscription_url,
            ),
        ]
    )

    # --------------------------------------------------------
    # Продление
    # --------------------------------------------------------

    buttons.append(
        [
            InlineKeyboardButton(
                text="⏳ Продлить",
                callback_data=(
                    f"extend_{user_id}"
                ),
            )
        ]
    )

    # --------------------------------------------------------
    # Отключение
    # --------------------------------------------------------

    if (
        subscription in (
            "vip",
            "trial",
        )
        and days > 0
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=(
                        f"disable_{user_id}"
                    ),
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
                callback_data="admin_users",
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except TelegramBadRequest as e:

        if (
            "message is not modified"
            not in str(e)
        ):

            raise

    await call.answer()


# ============================================================
# ОТКЛЮЧЕНИЕ ПОДПИСКИ
# ============================================================

@router.callback_query(
    F.data.startswith("disable_")
)
async def disable_user_subscription(
    call: CallbackQuery,
):

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    try:

        user_id = int(
            call.data.replace(
                "disable_",
                "",
            )
        )

    except ValueError:

        await call.answer(
            "❌ Неверный ID пользователя",
            show_alert=True,
        )

        return

    user = get_user(user_id)

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    try:

        disable_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка отключения "
            f"подписки {user_id}: {e}"
        )

        await call.answer(
            "❌ Ошибка при отключении",
            show_alert=True,
        )

        return

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    site_url, subscription_url = (
        get_user_urls(user_id)
    )

    text = (
        "👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ</b>\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🆔 <b>ID</b>\n"
        f"<code>{user_id}</code>\n\n"

        "👤 <b>Username</b>\n"
        f"@{escape(str(username))}\n\n"

        "🧑‍💻 <b>Имя</b>\n"
        f"{escape(str(first_name))}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🎫 <b>Тариф</b>\n"
        "❌ Нет подписки\n\n"

        "📊 <b>Статус</b>\n"
        "🔴 Неактивен\n\n"

        "📅 <b>Действует до</b>\n"
        "нет\n\n"

        "⏳ <b>Осталось</b>\n"
        "0 д.\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🌐 <b>САЙТ</b>\n"
        f"<code>{escape(site_url)}</code>\n\n"

        "🔗 <b>ПОДПИСКА</b>\n"
        f"<code>{escape(subscription_url)}</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть сайт",
                    url=site_url,
                ),
                InlineKeyboardButton(
                    text="🔗 Подписка",
                    url=subscription_url,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=(
                        f"extend_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_users",
                )
            ],
        ]
    )

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except TelegramBadRequest as e:

        if (
            "message is not modified"
            not in str(e)
        ):

            raise

    await call.answer(
        "✅ Подписка отключена"
    )


# ============================================================
# ОБНОВЛЕНИЕ СЕРВЕРОВ
# ============================================================

@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(
    call: CallbackQuery,
):

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    await call.answer(
        "🔄 Обновление началось..."
    )

    status_message = (
        await call.message.answer(
            "🔄 <b>Обновляю серверы...</b>\n\n"
            "⏳ Проверяю активные и "
            "истёкшие подписки...",
            parse_mode="HTML",
        )
    )

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

            parse_mode="HTML",
        )

    except Exception as e:

        print(
            f"❌ Ошибка синхронизации: {e}"
        )

        try:

            await status_message.edit_text(
                "❌ <b>Не удалось обновить "
                "серверы.</b>\n\n"

                "Ошибка:\n"
                f"<code>{escape(str(e))}</code>",

                parse_mode="HTML",
            )

        except TelegramBadRequest:

            pass