from aiogram import Router, F

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.exceptions import TelegramBadRequest

from datetime import datetime

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

import os


router = Router()


# ============================================================
# НАСТРОЙКИ САЙТА
# ============================================================

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

def is_admin(user_id: int) -> bool:

    return user_id in ADMIN_IDS


# ============================================================
# URL ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_user_urls(
    user_id: int,
):

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

    # --------------------------------------------------------
    # Нет подписки
    # --------------------------------------------------------

    if subscription in (
        None,
        "",
        "none",
        "expired",
    ):

        return (
            "🔴 Неактивен",
            0,
        )

    # --------------------------------------------------------
    # Нет даты
    # --------------------------------------------------------

    if not subscription_until:

        return (
            "🔴 Неактивен",
            0,
        )

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

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
    # Истёк
    # --------------------------------------------------------

    if expire_date < today:

        return (
            "⛔ Истёк",
            0,
        )

    # --------------------------------------------------------
    # Осталось
    # --------------------------------------------------------

    days = (
        expire_date
        - today
    ).days

    return (
        "🟢 Активен",
        days,
    )


# ============================================================
# ТАРИФ
# ============================================================

def get_tariff_name(
    subscription,
):

    if subscription == "ixxy":

        return "☂️ ixxy"

    if subscription == "trial":

        return "🎁 Пробный период"

    if subscription in (
        None,
        "",
        "none",
        "expired",
    ):

        return "❌ Нет подписки"

    # --------------------------------------------------------
    # Если в БД встретится другое значение
    # --------------------------------------------------------

    return str(
        subscription
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

    try:

        users = get_all_users()

    except Exception as e:

        print(
            f"❌ Ошибка получения пользователей: {e}"
        )

        await call.answer(
            "❌ Ошибка базы данных",
            show_alert=True,
        )

        return

    if not users:

        try:

            await call.message.edit_text(
                "👥 <b>Пользователи</b>\n\n"
                "Пользователей пока нет.",
                parse_mode="HTML",
            )

        except TelegramBadRequest:

            pass

        await call.answer()

        return

    buttons = []

    # --------------------------------------------------------
    # Первые 20 пользователей
    # --------------------------------------------------------

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

        # ----------------------------------------------------
        # Активный
        # ----------------------------------------------------

        if days > 0:

            text = (
                f"👤 {username} "
                f"• 🟢 {days} д."
            )

        # ----------------------------------------------------
        # Истёк
        # ----------------------------------------------------

        elif status == "⛔ Истёк":

            text = (
                f"👤 {username} "
                f"• ⛔ Истёк"
            )

        # ----------------------------------------------------
        # Неактивен
        # ----------------------------------------------------

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

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Пользователь
    # --------------------------------------------------------

    try:

        user = get_user(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка получения пользователя "
            f"{user_id}: {e}"
        )

        await call.answer(
            "❌ Ошибка базы данных",
            show_alert=True,
        )

        return

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # ========================================================
    # ДАННЫЕ
    # ========================================================

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    subscription = (
        user[3]
        or "none"
    )

    subscription_until = (
        user[4]
        or ""
    )

    # ========================================================
    # ССЫЛКИ
    # ========================================================

    site_url, subscription_url = (
        get_user_urls(
            user_id
        )
    )

    # --------------------------------------------------------
    # Сохранённая ссылка из БД
    # --------------------------------------------------------

    try:

        saved_link = get_subscription_link(
            user_id
        )

    except Exception as e:

        print(
            f"⚠️ Не удалось получить "
            f"ссылку пользователя {user_id}: {e}"
        )

        saved_link = None

    if saved_link:

        subscription_url = saved_link

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

    tariff = get_tariff_name(
        subscription
    )

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
    # ОСТАЛОСЬ
    # ========================================================

    if days > 0:

        days_text = (
            f"⏳ <b>Осталось:</b> "
            f"{days} д."
        )

    else:

        days_text = (
            "⏳ <b>Осталось:</b> "
            "0 д."
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
                url=site_url,
            )
        ],

        [
            InlineKeyboardButton(
                text="🔗 Открыть подписку",
                url=subscription_url,
            )
        ],

        [
            InlineKeyboardButton(
                text="⏳ Продлить",
                callback_data=(
                    f"extend_{user_id}"
                ),
            )
        ],
    ]

    # --------------------------------------------------------
    # Отключение
    # --------------------------------------------------------

    if (
        subscription not in (
            None,
            "",
            "none",
            "expired",
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

    # ========================================================
    # ПОКАЗ
    # ========================================================

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
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

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Проверяем пользователя
    # --------------------------------------------------------

    try:

        user = get_user(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка получения пользователя "
            f"{user_id}: {e}"
        )

        await call.answer(
            "❌ Ошибка базы данных",
            show_alert=True,
        )

        return

    if not user:

        await call.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Отключаем
    # --------------------------------------------------------

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
            show_alert=True,
        )

        return

    # ========================================================
    # ДАННЫЕ
    # ========================================================

    username = (
        user[1]
        or "нет"
    )

    first_name = (
        user[2]
        or "нет"
    )

    # ========================================================
    # URL
    # ========================================================

    site_url, subscription_url = (
        get_user_urls(
            user_id
        )
    )

    # ========================================================
    # ПРОФИЛЬ ПОСЛЕ ОТКЛЮЧЕНИЯ
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

    # ========================================================
    # КНОПКИ
    # ========================================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🌐 Открыть сайт",
                    url=site_url,
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔗 Открыть подписку",
                    url=subscription_url,
                )
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

    # ========================================================
    # ОБНОВЛЯЕМ
    # ========================================================

    try:

        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
            disable_web_page_preview=True,
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

    # ========================================================
    # СООБЩЕНИЕ
    # ========================================================

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

        # ----------------------------------------------------
        # Защита от отсутствующих ключей
        # ----------------------------------------------------

        updated = result.get(
            "updated",
            0,
        )

        expired = result.get(
            "expired",
            0,
        )

        skipped = result.get(
            "skipped",
            0,
        )

        errors = result.get(
            "errors",
            0,
        )

        # ====================================================
        # РЕЗУЛЬТАТ
        # ====================================================

        await status_message.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"

            f"🟢 Активных обновлено: "
            f"{updated}\n"

            f"⛔ Истёкших обновлено: "
            f"{expired}\n"

            f"⏭ Пропущено: "
            f"{skipped}\n"

            f"❌ Ошибок: "
            f"{errors}",

            parse_mode="HTML",
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

                parse_mode="HTML",
            )

        except TelegramBadRequest:

            pass