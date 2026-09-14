# handlers/admin_search.py

from datetime import datetime, timezone

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

from database import (
    get_user,
    get_all_users,
)


router = Router()


# ============================================================
# FSM
# ============================================================

class SearchUser(StatesGroup):
    waiting_query = State()


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# SAFE USER DATA
# ============================================================

def get_user_value(user, key, default=None):
    if not isinstance(user, dict):
        return default

    return user.get(key, default)


# ============================================================
# DATE
# ============================================================

def format_date(value, with_time=False):
    if not value:
        return "нет"

    try:
        if isinstance(value, str):
            value = value.replace("Z", "+00:00")
            value = datetime.fromisoformat(value)

        if not isinstance(value, datetime):
            return str(value)

        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)

        value = value.astimezone(timezone.utc)

        if with_time:
            return value.strftime("%d.%m.%Y %H:%M")

        return value.strftime("%d.%m.%Y")

    except Exception:
        return str(value)


# ============================================================
# SUBSCRIPTION STATUS
# ============================================================

def subscription_status(user):
    subscription = get_user_value(
        user,
        "subscription",
        False,
    )

    until = get_user_value(
        user,
        "subscription_until",
    )

    # В текущей БД subscription = BOOLEAN
    if subscription is not True:
        return "⚪ Нет активной подписки"

    if not until:
        return "⚠️ Активна, дата не указана"

    try:
        if isinstance(until, str):
            until = datetime.fromisoformat(
                until.replace("Z", "+00:00")
            )

        if until.tzinfo is None:
            until = until.replace(
                tzinfo=timezone.utc
            )

        if until <= datetime.now(timezone.utc):
            return "🔴 Истекла"

        return "🟢 Активна"

    except Exception:
        return "🟢 Активна"


# ============================================================
# USER KEYBOARD
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
                    text="🔎 Новый поиск",
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
# FORMAT USER
# ============================================================

def format_user(user):

    if not isinstance(user, dict):
        return "❌ Некорректные данные пользователя."

    user_id = get_user_value(
        user,
        "user_id",
        "—",
    )

    username = get_user_value(
        user,
        "username",
        "",
    )

    first_name = get_user_value(
        user,
        "first_name",
        "",
    )

    subscription = get_user_value(
        user,
        "subscription",
        False,
    )

    subscription_until = get_user_value(
        user,
        "subscription_until",
    )

    subscription_link = get_user_value(
        user,
        "subscription_link",
        "",
    )

    trial_used = get_user_value(
        user,
        "trial_used",
        False,
    )

    pending_days = get_user_value(
        user,
        "pending_days",
        0,
    )

    notify = get_user_value(
        user,
        "notify",
        True,
    )

    accepted_terms = get_user_value(
        user,
        "accepted_terms",
        False,
    )

    created_at = get_user_value(
        user,
        "created_at",
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
    # SUBSCRIPTION
    # --------------------------------------------------------

    status_text = subscription_status(
        user
    )

    if subscription is True:
        subscription_text = "🟢 Активна"
    else:
        subscription_text = "⚪ Неактивна"

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    until_text = format_date(
        subscription_until
    )

    created_text = format_date(
        created_at,
        with_time=True,
    )

    # --------------------------------------------------------
    # BOOLEAN VALUES
    # --------------------------------------------------------

    trial_text = (
        "использован"
        if bool(trial_used)
        else "не использован"
    )

    notify_text = (
        "включены"
        if bool(notify)
        else "выключены"
    )

    terms_text = (
        "приняты"
        if bool(accepted_terms)
        else "не приняты"
    )

    # --------------------------------------------------------
    # LINK
    # --------------------------------------------------------

    link_text = (
        str(subscription_link)
        if subscription_link
        else "нет"
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    return (
        "👤 <b>Пользователь</b>\n\n"

        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Имя: <b>{first_name or 'нет'}</b>\n"
        f"🔗 Username: <b>{username_text}</b>\n\n"

        f"📌 Подписка: "
        f"<b>{subscription_text}</b>\n"

        f"📊 Статус: "
        f"<b>{status_text}</b>\n"

        f"📅 Подписка до: "
        f"<b>{until_text}</b>\n\n"

        f"🎁 Пробный период: "
        f"<b>{trial_text}</b>\n"

        f"⏳ Ожидающие дни: "
        f"<b>{pending_days or 0}</b>\n\n"

        f"🔔 Уведомления: "
        f"<b>{notify_text}</b>\n"

        f"📜 Условия: "
        f"<b>{terms_text}</b>\n"

        f"🕐 Регистрация: "
        f"<b>{created_text}</b>\n\n"

        "🔗 <b>Постоянная ссылка подписки:</b>\n"
        f"<code>{link_text}</code>"
    )


# ============================================================
# SEARCH MENU
# ============================================================

def search_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Новый поиск",
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
# START SEARCH
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

    await call.answer()

    if not call.message:
        return

    await call.message.answer(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Можно отправить:\n"
        "🆔 Telegram ID\n"
        "👤 username\n"
        "🔤 имя пользователя\n\n"
        "Примеры:\n"
        "<code>123456789</code>\n"
        "<code>@username</code>\n"
        "<code>username</code>\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML",
    )


# ============================================================
# SEARCH BY ID
# ============================================================

async def search_by_id(user_id: int):

    try:
        return get_user(user_id)

    except Exception as e:
        print(
            "Admin search DB error:",
            repr(e),
        )
        return None


# ============================================================
# SEARCH ALL USERS
# ============================================================

def search_users(query: str):

    try:
        users = get_all_users() or []
    except Exception as e:
        print(
            "Admin users search DB error:",
            repr(e),
        )
        return []

    query_clean = query.strip().lstrip("@").lower()

    if not query_clean:
        return []

    result = []

    for user in users:

        if not isinstance(user, dict):
            continue

        user_id = str(
            user.get("user_id") or ""
        )

        username = str(
            user.get("username") or ""
        ).lstrip("@")

        first_name = str(
            user.get("first_name") or ""
        )

        if (
            query_clean in user_id.lower()
            or query_clean in username.lower()
            or query_clean in first_name.lower()
        ):
            result.append(user)

    return result


# ============================================================
# SEARCH RESULTS KEYBOARD
# ============================================================

def search_results_keyboard(users):

    buttons = []

    for user in users[:10]:

        user_id = user.get(
            "user_id"
        )

        if user_id is None:
            continue

        username = user.get(
            "username"
        )

        first_name = user.get(
            "first_name"
        )

        name = (
            f"@{str(username).lstrip('@')}"
            if username
            else str(first_name or user_id)
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"👤 {name}",
                    callback_data=(
                        f"search_user_{user_id}"
                    ),
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔎 Новый поиск",
                callback_data="admin_search",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Админ-панель",
                callback_data="admin_back",
            )
        ]
    )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# ============================================================
# CANCEL
# ============================================================

@router.message(
    SearchUser.waiting_query,
    F.text == "/cancel",
)
async def cancel_search(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):
        await state.clear()
        return

    await state.clear()

    await message.answer(
        "❌ Поиск отменён.",
        reply_markup=search_menu(),
    )


# ============================================================
# MAIN SEARCH
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
            "❌ Отправь Telegram ID, "
            "username или имя."
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

    if query.isdigit():

        try:
            user_id = int(query)
        except ValueError:

            await message.answer(
                "❌ Некорректный ID."
            )

            return

        user = await search_by_id(
            user_id
        )

        await state.clear()

        if not user:

            await message.answer(
                "❌ <b>Пользователь не найден</b>\n\n"
                f"🆔 ID: <code>{user_id}</code>",
                parse_mode="HTML",
                reply_markup=search_menu(),
            )

            return

        actual_user_id = user.get(
            "user_id",
            user_id,
        )

        await message.answer(
            format_user(user),
            parse_mode="HTML",
            reply_markup=user_keyboard(
                int(actual_user_id)
            ),
        )

        return

    # --------------------------------------------------------
    # USERNAME / NAME
    # --------------------------------------------------------

    users = search_users(query)

    await state.clear()

    if not users:

        await message.answer(
            "❌ <b>Пользователь не найден</b>\n\n"
            f"🔎 Запрос: "
            f"<code>{query}</code>",
            parse_mode="HTML",
            reply_markup=search_menu(),
        )

        return

    # --------------------------------------------------------
    # ONE RESULT
    # --------------------------------------------------------

    if len(users) == 1:

        user = users[0]

        user_id = user.get(
            "user_id"
        )

        if user_id is None:

            await message.answer(
                "❌ У пользователя отсутствует ID.",
                reply_markup=search_menu(),
            )

            return

        await message.answer(
            format_user(user),
            parse_mode="HTML",
            reply_markup=user_keyboard(
                int(user_id)
            ),
        )

        return

    # --------------------------------------------------------
    # MULTIPLE RESULTS
    # --------------------------------------------------------

    await message.answer(
        "🔎 <b>Найдено пользователей:</b> "
        f"<b>{len(users)}</b>\n\n"
        "Выбери нужного пользователя:",
        parse_mode="HTML",
        reply_markup=search_results_keyboard(
            users
        ),
    )


# ============================================================
# QUICK SEARCH USER
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

    except (
        ValueError,
        AttributeError,
    ):

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

        if not call.message:
            await call.answer()
            return

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


# ============================================================
# ADMIN USER CALLBACK
# ============================================================

@router.callback_query(
    F.data.startswith("admin_user_")
)
async def admin_user_card(
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
                "admin_user_",
                "",
                1,
            )
        )

    except (
        ValueError,
        AttributeError,
    ):

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

        if not call.message:
            await call.answer()
            return

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