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
    get_subscription_link,
    disable_subscription
)

from github_update import (
    sync_servers_update
)


router = Router()


# ============================================================
# НАСТРОЙКИ САЙТА
# ============================================================

PUBLIC_SITE_URL = (
    "https://orelvpnrailoh-1.onrender.com"
)

SUBSCRIPTION_PREFIX = (
    "2ix847xy"
)


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
        subscription_url
    )


# ============================================================
# СТАТУС ПОДПИСКИ
# ============================================================

def get_subscription_status(
    subscription,
    subscription_until
):

    if subscription not in (
        "vip",
        "trial"
    ):

        return (
            "🔴 Неактивен",
            0
        )

    if not subscription_until:

        return (
            "🔴 Неактивен",
            0
        )

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

    today = datetime.now().date()

    if expire_date < today:

        return (
            "⛔ Истёк",
            0
        )

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

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )

        return

    users = get_all_users()

    if not users:

        try:

            await call.message.edit_text(
                "👥 <b>Пользователи</b>\n\n"
                "Пользователей пока нет.",
                parse_mode="HTML"
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
                subscription_until
            )
        )

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
            "👥 <b>Пользователи</b>\n\n"
            "Выбери пользователя:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except TelegramBadRequest as e:

        if (
            "message is not modified"
            not in str(e)
        ):

            raise

    await call.answer()


# ============================================================
# ПРОФИЛЬ
# ============================================================

@router.callback_query(
    F.data.startswith("admin_user_")
)
async def user_profile(
    call: CallbackQuery
):

    if not is_admin(
        call.from_user.id
    ):

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

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    subscription = user[3]

    subscription_until = user[4]

    # --------------------------------------------------------
    # Ссылки
    # --------------------------------------------------------

    saved_link = get_subscription_link(
        user_id
    )

    site_url, subscription_url = (
        get_user_urls(user_id)
    )

    # --------------------------------------------------------
    # Если ссылка уже сохранена в БД
    # используем её для отображения
    # --------------------------------------------------------

    if saved_link:

        subscription_url = saved_link

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    status, days = (
        get_subscription_status(
            subscription,
            subscription_until
        )
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

    # --------------------------------------------------------
    # Осталось
    # --------------------------------------------------------

    if days > 0:

        days_text = (
            f"⏳ <b>Осталось:</b> "
            f"{days} д."
        )

    else:

        days_text = (
            "⏳ <b>Осталось:</b> 0 д."
        )

    # ========================================================
    # ПРОФИЛЬ
    # ========================================================

    text = (
        "👤 <b>Пользователь</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🆔 <b>ID:</b> "
        f"<code>{user_id}</code>\n"

        f"👤 <b>Username:</b> "
        f"@{username}\n"

        f"🧑‍💻 <b>Имя:</b> "
        f"{first_name}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🎫 <b>Тариф:</b> "
        f"{tariff}\n"

        f"📊 <b>Статус:</b> "
        f"{status}\n"

        f"📅 <b>До:</b> "
        f"{date_text}\n"

        f"{days_text}\n\n"

        "━━━━━━━━━━━━━━━━━━"
    )

    # ========================================================
    # КНОПКИ
    # ========================================================

    buttons = [

        [
            InlineKeyboardButton(
                text="🌐 Открыть сайт",
                url=site_url
            )
        ],

        [
            InlineKeyboardButton(
                text="🔗 Открыть подписку",
                url=subscription_url
            )
        ],

        [
            InlineKeyboardButton(
                text="⏳ Продлить",
                callback_data=(
                    f"extend_{user_id}"
                )
            )
        ]
    ]

    # --------------------------------------------------------
    # Отключение
    # --------------------------------------------------------

    if (
        subscription in (
            "vip",
            "trial"
        )
        and days > 0
    ):

        buttons.append(
            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=(
                        f"disable_{user_id}"
                    )
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_users"
            )
        ]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    # ========================================================
    # ПОКАЗ
    # ========================================================

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True
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
    call: CallbackQuery
):

    if not is_admin(
        call.from_user.id
    ):

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
            "❌ Неверный ID пользователя",
            show_alert=True
        )

        return

    user = get_user(
        user_id
    )

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    try:

        disable_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка отключения "
            f"{user_id}: {e}"
        )

        await call.answer(
            "❌ Ошибка при отключении",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # Ссылки
    # --------------------------------------------------------

    site_url, subscription_url = (
        get_user_urls(user_id)
    )

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    # ========================================================
    # ОБНОВЛЁННЫЙ ПРОФИЛЬ
    # ========================================================

    text = (
        "👤 <b>Пользователь</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        f"🆔 <b>ID:</b> "
        f"<code>{user_id}</code>\n"

        f"👤 <b>Username:</b> "
        f"@{username}\n"

        f"🧑‍💻 <b>Имя:</b> "
        f"{first_name}\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        "🎫 <b>Тариф:</b> "
        "❌ Нет подписки\n"

        "📊 <b>Статус:</b> "
        "🔴 Неактивен\n"

        "📅 <b>До:</b> "
        "нет\n"

        "⏳ <b>Осталось:</b> "
        "0 д.\n\n"

        "━━━━━━━━━━━━━━━━━━"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🌐 Открыть сайт",
                    url=site_url
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔗 Открыть подписку",
                    url=subscription_url
                )
            ],

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
            parse_mode="HTML",
            disable_web_page_preview=True
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
# СИНХРОНИЗАЦИЯ СЕРВЕРОВ
# ============================================================

@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(
    call: CallbackQuery
):

    if not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа",
            show_alert=True
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
            parse_mode="HTML"
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

            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"❌ Ошибка синхронизации: "
            f"{e}"
        )

        try:

            await status_message.edit_text(
                "❌ <b>Не удалось "
                "обновить серверы.</b>\n\n"

                f"Ошибка:\n"
                f"<code>{str(e)}</code>",

                parse_mode="HTML"
            )

        except TelegramBadRequest:

            pass