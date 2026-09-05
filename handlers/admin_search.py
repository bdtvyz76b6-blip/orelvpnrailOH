from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import get_user


router = Router()


# ============================================================
# FSM
# ============================================================

class SearchUser(StatesGroup):
    waiting_query = State()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ПОЛЯ
# ============================================================

def user_field(user, index, default=""):

    try:

        if isinstance(user, dict):

            keys = [
                "user_id",
                "username",
                "first_name",
                "subscription",
                "subscription_until",
                "subscription_link",
                "uuid",
                "trial_used",
                "pending_days",
                "notify",
                "accepted_terms",
                "created_at",
                "subscription_content",
            ]

            if index < len(keys):
                return user.get(
                    keys[index],
                    default,
                )

            return default

        return user[index]

    except (IndexError, KeyError, TypeError):

        return default


# ============================================================
# КЛАВИАТУРА ПОЛЬЗОВАТЕЛЯ
# ============================================================

def user_keyboard(user_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Карточка",
                    callback_data=f"admin_user_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➕ Продлить",
                    callback_data=f"extend_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data=f"admin_payments_{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Новый поиск",
                    callback_data="admin_search",
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


# ============================================================
# ФОРМАТИРОВАНИЕ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def format_user(user):

    user_id = user_field(
        user,
        0,
        "—",
    )

    username = user_field(
        user,
        1,
        "",
    )

    first_name = user_field(
        user,
        2,
        "",
    )

    subscription = user_field(
        user,
        3,
        "none",
    )

    subscription_until = user_field(
        user,
        4,
        "",
    )

    subscription_link = user_field(
        user,
        5,
        "",
    )

    trial_used = user_field(
        user,
        7,
        0,
    )

    pending_days = user_field(
        user,
        8,
        0,
    )

    notify = user_field(
        user,
        9,
        1,
    )

    accepted_terms = user_field(
        user,
        10,
        0,
    )

    created_at = user_field(
        user,
        11,
        "",
    )

    # --------------------------------------------------------
    # ТАРИФ
    # --------------------------------------------------------

    subscription_text = str(
        subscription or "none"
    )

    subscription_names = {
        "vip": "👑 VIP",
        "trial": "🎁 Пробный период",
        "none": "⚪ Нет подписки",
        "expired": "🔴 Истекла",
    }

    subscription_text = subscription_names.get(
        subscription_text.lower(),
        subscription_text,
    )

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------

    if username:

        username_text = (
            f"@{str(username).lstrip('@')}"
        )

    else:

        username_text = "нет"

    # --------------------------------------------------------
    # ДАТА
    # --------------------------------------------------------

    until_text = (
        str(subscription_until)
        if subscription_until
        else "нет"
    )

    if hasattr(
        subscription_until,
        "strftime",
    ):

        try:

            until_text = subscription_until.strftime(
                "%d.%m.%Y"
            )

        except Exception:

            pass

    # --------------------------------------------------------
    # ДАТА РЕГИСТРАЦИИ
    # --------------------------------------------------------

    created_text = (
        str(created_at)
        if created_at
        else "нет"
    )

    if hasattr(
        created_at,
        "strftime",
    ):

        try:

            created_text = created_at.strftime(
                "%d.%m.%Y %H:%M"
            )

        except Exception:

            pass

    # --------------------------------------------------------
    # СТАТУСЫ
    # --------------------------------------------------------

    trial_text = (
        "использован"
        if int(trial_used or 0)
        else "не использован"
    )

    notify_text = (
        "включены"
        if int(notify or 0)
        else "выключены"
    )

    terms_text = (
        "приняты"
        if int(accepted_terms or 0)
        else "не приняты"
    )

    # --------------------------------------------------------
    # ТЕКСТ
    # --------------------------------------------------------

    return (
        "👤 <b>Пользователь найден</b>\n\n"

        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: <b>{first_name or 'нет'}</b>\n"
        f"🔗 Username: <b>{username_text}</b>\n\n"

        f"📌 Тариф: <b>{subscription_text}</b>\n"
        f"📅 Подписка до: <b>{until_text}</b>\n"
        f"🎁 Пробный период: <b>{trial_text}</b>\n"
        f"⏳ Ожидающие дни: <b>{pending_days or 0}</b>\n\n"

        f"🔔 Уведомления: <b>{notify_text}</b>\n"
        f"📜 Условия: <b>{terms_text}</b>\n"
        f"🕐 Регистрация: <b>{created_text}</b>\n\n"

        "🔗 <b>Ссылка подписки:</b>\n"
        f"<code>{subscription_link or 'нет'}</code>"
    )


# ============================================================
# НАЧАЛО ПОИСКА
# ============================================================

@router.callback_query(
    F.data == "admin_search"
)
async def start_search(
    call: CallbackQuery,
    state: FSMContext,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):

        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )

        return

    await state.clear()

    await state.set_state(
        SearchUser.waiting_query
    )

    await call.message.answer(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Можно отправить:\n"
        "🆔 Telegram ID\n"
        "👤 username\n"
        "🔤 имя пользователя\n\n"
        "Примеры:\n"
        "<code>123456789</code>\n"
        "<code>@username</code>\n"
        "<code>username</code>",
        parse_mode="HTML",
    )

    await call.answer()


# ============================================================
# ПОИСК ПО ID
# ============================================================

async def search_by_id(
    user_id: int,
):

    try:

        return get_user(
            user_id
        )

    except Exception as e:

        print(
            "Admin search DB error:",
            repr(e),
        )

        return None


# ============================================================
# ОСНОВНОЙ ПОИСК
# ============================================================

@router.message(
    SearchUser.waiting_query
)
async def find_user(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):

        await state.clear()
        return

    if not message.text:

        await message.answer(
            "❌ Отправьте ID или username."
        )

        return

    query = message.text.strip()

    if not query:

        await message.answer(
            "❌ Поисковый запрос пустой."
        )

        return

    # --------------------------------------------------------
    # ID
    # --------------------------------------------------------

    user = None

    if query.isdigit():

        try:

            user_id = int(query)

            user = await search_by_id(
                user_id
            )

        except Exception as e:

            print(
                "Admin search ID error:",
                repr(e),
            )

    # --------------------------------------------------------
    # USERNAME
    # --------------------------------------------------------
    #
    # В текущей database.py есть get_user(),
    # но отдельного поиска по username нет.
    #
    # Поэтому для username/имени пока используем
    # понятное сообщение вместо выдуманного SQL.
    # --------------------------------------------------------

    if not user and not query.isdigit():

        await state.clear()

        await message.answer(
            "🔎 <b>Поиск по username/имени</b>\n\n"
            "Сейчас в базе есть прямой поиск по Telegram ID.\n\n"
            "Для поиска по <code>@username</code> или имени "
            "нужно добавить отдельную функцию поиска "
            "в <code>database.py</code>.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🆔 Искать по ID",
                            callback_data="admin_search",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Админ-панель",
                            callback_data="admin_back",
                        )
                    ],
                ]
            ),
        )

        return

    # --------------------------------------------------------
    # НЕ НАЙДЕН
    # --------------------------------------------------------

    if not user:

        await state.clear()

        await message.answer(
            "❌ <b>Пользователь не найден</b>\n\n"
            f"🔎 Запрос: <code>{query}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🔎 Новый поиск",
                            callback_data="admin_search",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Админ-панель",
                            callback_data="admin_back",
                        )
                    ],
                ]
            ),
        )

        return

    # --------------------------------------------------------
    # НАЙДЕН
    # --------------------------------------------------------

    user_id = user_field(
        user,
        0,
        0,
    )

    await state.clear()

    await message.answer(
        format_user(user),
        parse_mode="HTML",
        reply_markup=user_keyboard(
            int(user_id)
        ),
    )


# ============================================================
# БЫСТРЫЙ ПОИСК ПО ID ИЗ ДРУГИХ МЕСТ
# ============================================================

@router.callback_query(
    F.data.startswith("search_user_")
)
async def quick_search_user(
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

        user_id = int(
            call.data.replace(
                "search_user_",
                "",
                1,
            )
        )

    except (ValueError, AttributeError):

        await call.answer(
            "❌ Некорректный ID.",
            show_alert=True,
        )

        return

    user = await search_by_id(
        user_id
    )

    if not user:

        await call.answer(
            "❌ Пользователь не найден.",
            show_alert=True,
        )

        return

    try:

        await call.message.edit_text(
            format_user(user),
            parse_mode="HTML",
            reply_markup=user_keyboard(
                user_id
            ),
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise

    await call.answer()