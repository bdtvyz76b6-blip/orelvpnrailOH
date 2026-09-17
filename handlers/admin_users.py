import asyncio
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timezone
from html import escape
from config import ADMIN_IDS
from keyboards import admin_menu
from database import (
    get_all_users,
    get_user,
    get_all_payments,
    get_subscription_link,
    disable_subscription,
    extend_subscription,
)
from github_update import (
    sync_servers_update,
    update_subscription_file,
)
router = Router()
USERS_PER_PAGE = 15
MAX_CUSTOM_DAYS = 999_999_999
class AdminSearch(StatesGroup):
    waiting_query = State()
class AdminCustomExtend(StatesGroup):
    waiting_days = State()
def is_admin(user_id: int) -> bool:
    try:
        return int(user_id) in ADMIN_IDS
    except (TypeError, ValueError):
        return False
def h(value) -> str:
    return escape(str(value or ""))
def normalize_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        try:
            dt = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )
        except Exception:
            try:
                dt = datetime.strptime(
                    text,
                    "%Y-%m-%d",
                )
            except Exception:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
def format_date(value):
    if not value:
        return "нет"
    dt = normalize_datetime(value)
    if dt:
        return dt.strftime("%d.%m.%Y")
    return str(value)
def format_datetime(value):
    if not value:
        return "нет"
    dt = normalize_datetime(value)
    if dt:
        return dt.strftime("%d.%m.%Y %H:%M")
    return str(value)
def get_subscription_status(
    subscription,
    subscription_until,
):
    # PostgreSQL subscription = BOOLEAN
    if subscription is not True:
        return "🔴 Неактивен", 0
    if not subscription_until:
        return "🔴 Неактивен", 0
    dt = normalize_datetime(subscription_until)
    if not dt:
        return "⚠️ Ошибка даты", 0
    now = datetime.now(timezone.utc)
    if dt <= now:
        return "⛔ Истёк", 0
    days = max(
        0,
        (dt - now).days,
    )
    return "🟢 Активен", days
def get_tariff_name(user: dict):
    if not isinstance(user, dict):
        return "❌ Нет подписки"
    if user.get("subscription") is not True:
        return "❌ Нет подписки"
    if (
        bool(user.get("trial_used"))
        and not user.get("pending_days")
    ):
        return "🎁 Пробный период"
    return "☂️ ixxy VPN"
# ============================================================
# ПОСТОЯННАЯ ССЫЛКА ПОДПИСКИ
#
# ВАЖНО:
# Всегда используем текущий сайт ixxy.
#
# Старый:
# https://orelvpnrailoh-1.onrender.com
#
# больше нигде здесь не используется.
# ============================================================
def get_user_subscription_url(user_id: int) -> str:
    user_id = int(user_id)
    return (
        "https://ixxyweb.onrender.com/sub/"
        f"2ix847xy{user_id}"
    )
def add_url_button(
    buttons,
    text,
    url,
):
    if url and url.startswith(
        ("http://", "https://")
    ):
        buttons.append(
            [
                InlineKeyboardButton(
                    text=text,
                    url=url,
                )
            ]
        )
def user_display_name(user: dict) -> str:
    if not isinstance(user, dict):
        return "неизвестный"
    username = user.get("username")
    first_name = user.get("first_name")
    user_id = user.get("user_id")
    if username:
        return f"@{username}"
    if first_name:
        return str(first_name)
    return f"ID {user_id}"
# ============================================================
# НАЗАД
# ============================================================
@router.callback_query(F.data == "admin_back")
async def admin_back(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        await call.message.edit_text(
            "🛠 <b>☂️ ixxy VPN — Админ-панель</b>\n\n"
            "Выбери нужный раздел:",
            reply_markup=admin_menu(),
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
# ============================================================
# КЛАВИАТУРА ПОЛЬЗОВАТЕЛЕЙ
# ============================================================
def build_users_keyboard(
    users,
    page=0,
):
    total = len(users)
    total_pages = max(
        1,
        (total + USERS_PER_PAGE - 1)
        // USERS_PER_PAGE,
    )
    page = max(
        0,
        min(
            page,
            total_pages - 1,
        ),
    )
    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE
    page_users = users[start:end]
    buttons = []
    for user in page_users:
        if not isinstance(user, dict):
            continue
        user_id = user.get("user_id")
        username = (
            user.get("username")
            or user.get("first_name")
            or f"ID {user_id}"
        )
        status, days = get_subscription_status(
            user.get("subscription"),
            user.get("subscription_until"),
        )
        if days > 0:
            status_text = f"🟢 {days}д."
        elif status == "⛔ Истёк":
            status_text = "⛔ истёк"
        elif status == "⚠️ Ошибка даты":
            status_text = "⚠️ дата"
        else:
            status_text = "🔴 нет"
        username = str(username)
        if len(username) > 22:
            username = username[:21] + "…"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"👤 {username} • "
                        f"{status_text}"
                    ),
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ]
        )
    navigation = []
    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=(
                    f"admin_users_page_{page - 1}"
                ),
            )
        )
    navigation.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="admin_users_noop",
        )
    )
    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=(
                    f"admin_users_page_{page + 1}"
                ),
            )
        )
    buttons.append(navigation)
    buttons.append(
        [
            InlineKeyboardButton(
                text="🔎 Найти пользователя",
                callback_data="admin_search",
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats",
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
    return (
        InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        page,
        total_pages,
    )
async def render_users(
    call: CallbackQuery,
    page=0,
):
    try:
        users = get_all_users() or []
    except Exception as e:
        print(
            f"❌ ADMIN USERS ERROR: {e}"
        )
        try:
            await call.message.edit_text(
                "❌ <b>Ошибка базы данных.</b>",
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
        return
    users = [
        user
        for user in users
        if isinstance(user, dict)
    ]
    if not users:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔎 Найти пользователя",
                        callback_data="admin_search",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_back",
                    )
                ],
            ]
        )
        try:
            await call.message.edit_text(
                "👥 <b>Пользователи</b>\n\n"
                "Пока пользователей нет.",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        return
    keyboard, page, total_pages = build_users_keyboard(
        users,
        page,
    )
    start_number = (
        page * USERS_PER_PAGE + 1
    )
    end_number = min(
        (page + 1) * USERS_PER_PAGE,
        len(users),
    )
    text = (
        "👥 <b>Пользователи</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Всего: <b>{len(users)}</b>\n"
        f"📄 Показаны: "
        f"<b>{start_number}–{end_number}</b>\n"
        f"📑 Страница: "
        f"<b>{page + 1}/{total_pages}</b>\n\n"
        "Выбери пользователя:"
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
@router.callback_query(
    F.data == "admin_users"
)
async def show_users(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
    await render_users(
        call,
        0,
    )
@router.callback_query(
    F.data.startswith(
        "admin_users_page_"
    )
)
async def users_page(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        page = int(
            call.data.replace(
                "admin_users_page_",
                "",
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверная страница",
            show_alert=True,
        )
        return
    await call.answer()
    await render_users(
        call,
        page,
    )
@router.callback_query(
    F.data == "admin_users_noop"
)
async def users_noop(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
# ============================================================
# ПОИСК
# ============================================================
@router.callback_query(
    F.data == "admin_search"
)
async def admin_search(
    call: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
    await state.set_state(
        AdminSearch.waiting_query
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=(
                        "admin_search_cancel"
                    ),
                )
            ]
        ]
    )
    await call.message.answer(
        "🔎 <b>Поиск пользователя</b>\n\n"
        "Отправь:\n"
        "• Telegram ID\n"
        "• @username\n"
        "• username\n"
        "• имя пользователя",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
@router.callback_query(
    F.data == "admin_search_cancel"
)
async def admin_search_cancel(
    call: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
    await state.clear()
    await call.message.answer(
        "❌ Поиск отменён.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛠 Админ-панель",
                        callback_data="admin_back",
                    )
                ]
            ]
        ),
    )
@router.message(
    AdminSearch.waiting_query
)
async def admin_search_query(
    message: Message,
    state: FSMContext,
):
    if not message.from_user:
        return
    if not is_admin(message.from_user.id):
        return
    query = (
        (message.text or "")
        .strip()
        .lower()
    )
    if not query:
        await message.answer(
            "❌ Введи ID, username или имя."
        )
        return
    try:
        users = get_all_users() or []
    except Exception as e:
        print(
            f"❌ ADMIN SEARCH ERROR: {e}"
        )
        await state.clear()
        await message.answer(
            "❌ Ошибка базы данных."
        )
        return
    normalized_query = query.lstrip("@")
    found = []
    for user in users:
        if not isinstance(user, dict):
            continue
        user_id = str(
            user.get("user_id") or ""
        ).lower()
        username = str(
            user.get("username") or ""
        ).lower().lstrip("@")
        first_name = str(
            user.get("first_name") or ""
        ).lower()
        if (
            normalized_query in user_id
            or normalized_query in username
            or normalized_query in first_name
        ):
            found.append(user)
    await state.clear()
    if not found:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔎 Искать снова",
                        callback_data="admin_search",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Пользователи",
                        callback_data="admin_users",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data="admin_back",
                    )
                ],
            ]
        )
        await message.answer(
            "🔎 <b>Результат поиска</b>\n\n"
            f"По запросу "
            f"<code>{h(query)}</code> "
            "ничего не найдено.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return
    buttons = []
    for user in found[:30]:
        user_id = user.get("user_id")
        username = (
            user.get("username")
            or user.get("first_name")
            or f"ID {user_id}"
        )
        status, days = get_subscription_status(
            user.get("subscription"),
            user.get("subscription_until"),
        )
        if days > 0:
            state_text = f"🟢 {days}д."
        elif status == "⛔ Истёк":
            state_text = "⛔ истёк"
        else:
            state_text = "🔴 нет"
        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"👤 {username} • "
                        f"{state_text}"
                    ),
                    callback_data=(
                        f"admin_user_{user_id}"
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
                text="👥 Пользователи",
                callback_data="admin_users",
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
    extra = ""
    if len(found) > 30:
        extra = (
            "\n\nПоказаны первые 30 результатов."
        )
    await message.answer(
        "🔎 <b>Результаты поиска</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Запрос: <code>{h(query)}</code>\n"
        f"Найдено: <b>{len(found)}</b>{extra}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        ),
        parse_mode="HTML",
    )
# ============================================================
# ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================
@router.callback_query(
    F.data.startswith("admin_user_")
)
async def user_profile(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
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
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ ADMIN PROFILE ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user.get(
        "username"
    ) or "нет"
    first_name = user.get(
        "first_name"
    ) or "нет"
    subscription = user.get(
        "subscription"
    )
    subscription_until = user.get(
        "subscription_until"
    )
    created_at = user.get(
        "created_at"
    )
    subscription_url = (
        get_user_subscription_url(
            user_id
        )
    )
    status, days = get_subscription_status(
        subscription,
        subscription_until,
    )
    tariff = get_tariff_name(user)
    payment_count = 0
    paid_count = 0
    try:
        all_payments = (
            get_all_payments() or []
        )
        user_payments = [
            payment
            for payment in all_payments
            if (
                isinstance(payment, dict)
                and int(
                    payment.get("user_id")
                    or 0
                )
                == int(user_id)
            )
        ]
        payment_count = len(
            user_payments
        )
        paid_count = sum(
            1
            for payment in user_payments
            if str(
                payment.get("status")
                or ""
            ).lower()
            in (
                "paid",
                "success",
                "successful",
                "completed",
                "approved",
            )
        )
    except Exception as e:
        print(
            f"⚠️ USER PAYMENTS ERROR "
            f"{user_id}: {e}"
        )
    username_text = (
        f"@{h(username)}"
        if username != "нет"
        else "нет"
    )
    text = (
        "👤 <b>Пользователь</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>ID:</b> "
        f"<code>{user_id}</code>\n"
        f"👤 <b>Username:</b> "
        f"{username_text}\n"
        f"🧑‍💻 <b>Имя:</b> "
        f"{h(first_name)}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎫 <b>Тариф:</b> "
        f"{h(tariff)}\n"
        f"📊 <b>Статус:</b> "
        f"{status}\n"
        f"📅 <b>До:</b> "
        f"{format_date(subscription_until)}\n"
        f"⏳ <b>Осталось:</b> "
        f"{days} д.\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💳 <b>Платежей:</b> "
        f"{payment_count}\n"
        f"✅ <b>Оплаченных:</b> "
        f"{paid_count}\n"
        f"📆 <b>Создан:</b> "
        f"{h(format_datetime(created_at))}"
    )
    buttons = []
    add_url_button(
        buttons,
        "🔗 Открыть подписку",
        subscription_url,
    )
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
    buttons.append(
        [
            InlineKeyboardButton(
                text="💳 Платежи",
                callback_data=(
                    f"admin_payments_{user_id}"
                ),
            )
        ]
    )
    if (
        subscription is True
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
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Пользователи",
                callback_data="admin_users",
            )
        ]
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=buttons
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
# ============================================================
# ВЫБОР СРОКА
# ============================================================
@router.callback_query(
    F.data.regexp(r"^extend_\d+$")
)
async def extend_subscription_menu(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
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
    except ValueError:
        await call.answer(
            "❌ Неверный ID пользователя",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ GET USER ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user_display_name(user)
    _, current_days = (
        get_subscription_status(
            user.get("subscription"),
            user.get(
                "subscription_until"
            ),
        )
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📅 +30 дней",
                    callback_data=(
                        f"extend_days_{user_id}_30"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 +3 месяца",
                    callback_data=(
                        f"extend_days_{user_id}_90"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 +6 месяцев",
                    callback_data=(
                        f"extend_days_{user_id}_180"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📅 +12 месяцев",
                    callback_data=(
                        f"extend_days_{user_id}_365"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Своё количество дней",
                    callback_data=(
                        f"custom_extend_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ],
        ]
    )
    await call.message.edit_text(
        "⏳ <b>Продление подписки</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Пользователь: "
        f"<b>{h(username)}</b>\n"
        f"🆔 ID: "
        f"<code>{user_id}</code>\n\n"
        f"📅 Сейчас осталось: "
        f"<b>{current_days} д.</b>\n\n"
        "Выбери срок продления:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
# ============================================================
# CUSTOM EXTEND
# ============================================================
@router.callback_query(
    F.data.regexp(r"^custom_extend_\d+$")
)
async def custom_extend_start(
    call: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        user_id = int(
            call.data.replace(
                "custom_extend_",
                "",
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверный ID пользователя",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ CUSTOM EXTEND USER ERROR: "
            f"{e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    await state.update_data(
        custom_extend_user_id=user_id
    )
    await state.set_state(
        AdminCustomExtend.waiting_days
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=(
                        f"custom_extend_cancel_"
                        f"{user_id}"
                    ),
                )
            ]
        ]
    )
    await call.message.answer(
        "✏️ <b>Своё количество дней</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 Пользователь: "
        f"<code>{user_id}</code>\n\n"
        "Введи количество дней числом.\n\n"
        "Например:\n"
        "• <code>7</code>\n"
        "• <code>45</code>\n"
        "• <code>180</code>\n"
        "• <code>1000</code>\n\n"
        f"Максимум: "
        f"<b>{MAX_CUSTOM_DAYS:,}</b> дней.".replace(
            ",",
            " ",
        ),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
@router.callback_query(
    F.data.regexp(
        r"^custom_extend_cancel_\d+$"
    )
)
async def custom_extend_cancel(
    call: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        user_id = int(
            call.data.replace(
                "custom_extend_cancel_",
                "",
                1,
            )
        )
    except ValueError:
        await state.clear()
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return
    await call.answer(
        "❌ Отменено"
    )
    await state.clear()
    try:
        await call.message.edit_text(
            "❌ <b>Ввод отменён</b>\n\n"
            "Можно вернуться к пользователю.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="👤 К пользователю",
                            callback_data=(
                                f"admin_user_{user_id}"
                            ),
                        )
                    ]
                ]
            ),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass
@router.message(
    AdminCustomExtend.waiting_days
)
async def custom_extend_days(
    message: Message,
    state: FSMContext,
):
    if not message.from_user:
        return
    if not is_admin(
        message.from_user.id
    ):
        return
    raw_days = (
        (message.text or "")
        .strip()
        .replace(" ", "")
    )
    if not raw_days.isdigit():
        await message.answer(
            "❌ <b>Неверное количество дней.</b>\n\n"
            "Введи только целое число.\n"
            "Например: <code>45</code>",
            parse_mode="HTML",
        )
        return
    try:
        days = int(raw_days)
    except ValueError:
        await message.answer(
            "❌ Слишком большое число."
        )
        return
    if days < 1:
        await message.answer(
            "❌ Количество дней должно быть больше 0."
        )
        return
    if days > MAX_CUSTOM_DAYS:
        await message.answer(
            "❌ Слишком большое количество дней.\n\n"
            f"Максимум: "
            f"<b>{MAX_CUSTOM_DAYS:,}</b> дней.".replace(
                ",",
                " ",
            ),
            parse_mode="HTML",
        )
        return
    data = await state.get_data()
    user_id = data.get(
        "custom_extend_user_id"
    )
    if not user_id:
        await state.clear()
        await message.answer(
            "❌ Не удалось определить пользователя.\n"
            "Начни продление заново."
        )
        return
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ CUSTOM EXTEND GET USER ERROR "
            f"{user_id}: {e}"
        )
        await state.clear()
        await message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await state.clear()
        await message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user_display_name(user)
    await state.clear()
    try:
        new_date = extend_subscription(
            user_id,
            days,
        )
        if not new_date:
            raise RuntimeError(
                "База данных не вернула новую дату"
            )
        await asyncio.to_thread(
            update_subscription_file,
            user_id,
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 К пользователю",
                        callback_data=(
                            f"admin_user_{user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Пользователи",
                        callback_data=(
                            "admin_users"
                        ),
                    )
                ],
            ]
        )
        await message.answer(
            "✅ <b>Подписка успешно продлена!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Пользователь: "
            f"<b>{h(username)}</b>\n"
            f"🆔 ID: "
            f"<code>{user_id}</code>\n\n"
            f"➕ Добавлено: "
            f"<b>{days} дней</b>\n"
            f"📅 Действует до: "
            f"<b>{format_date(new_date)}</b>\n\n"
            "🔄 Содержимое подписки обновлено.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        print(
            f"✅ ADMIN CUSTOM EXTEND: "
            f"user={user_id}, "
            f"days={days}, "
            f"until={new_date}"
        )
    except Exception as e:
        print(
            f"❌ CUSTOM EXTEND ERROR "
            f"user={user_id}, "
            f"days={days}: {e}"
        )
        await message.answer(
            "❌ <b>Ошибка продления</b>\n\n"
            f"👤 {h(username)}\n"
            f"🆔 <code>{user_id}</code>\n\n"
            "Ошибка:\n"
            f"<code>{h(str(e))}</code>",
            parse_mode="HTML",
        )
# ============================================================
# ГОТОВЫЕ СРОКИ
# ============================================================
@router.callback_query(
    F.data.startswith(
        "extend_days_"
    )
)
async def extend_subscription_admin(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        parts = call.data.split("_")
        if len(parts) != 4:
            raise ValueError
        user_id = int(parts[2])
        days = int(parts[3])
    except (
        ValueError,
        IndexError,
    ):
        await call.answer(
            "❌ Неверные параметры",
            show_alert=True,
        )
        return
    if days not in (
        30,
        90,
        180,
        365,
    ):
        await call.answer(
            "❌ Недопустимый срок",
            show_alert=True,
        )
        return
    await call.answer(
        "⏳ Продлеваю..."
    )
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ GET USER ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user_display_name(user)
    try:
        new_date = extend_subscription(
            user_id,
            days,
        )
        if not new_date:
            raise RuntimeError(
                "База данных не вернула новую дату"
            )
        await asyncio.to_thread(
            update_subscription_file,
            user_id,
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="👤 К пользователю",
                        callback_data=(
                            f"admin_user_{user_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👥 Пользователи",
                        callback_data=(
                            "admin_users"
                        ),
                    )
                ],
            ]
        )
        await call.message.edit_text(
            "✅ <b>Подписка успешно продлена!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Пользователь: "
            f"<b>{h(username)}</b>\n"
            f"🆔 ID: "
            f"<code>{user_id}</code>\n\n"
            f"➕ Добавлено: "
            f"<b>{days} дней</b>\n"
            f"📅 Действует до: "
            f"<b>{format_date(new_date)}</b>\n\n"
            "🔄 Содержимое подписки обновлено.",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        print(
            f"✅ ADMIN EXTEND: "
            f"user={user_id}, "
            f"days={days}, "
            f"until={new_date}"
        )
    except Exception as e:
        print(
            f"❌ ADMIN EXTEND ERROR "
            f"user={user_id}, "
            f"days={days}: {e}"
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="↩️ К пользователю",
                        callback_data=(
                            f"admin_user_{user_id}"
                        ),
                    )
                ]
            ]
        )
        try:
            await call.message.edit_text(
                "❌ <b>Ошибка продления</b>\n\n"
                f"👤 {h(username)}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                "Ошибка:\n"
                f"<code>{h(str(e))}</code>",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
# ============================================================
# ПЛАТЕЖИ ПОЛЬЗОВАТЕЛЯ
# ============================================================
@router.callback_query(
    F.data.startswith(
        "admin_payments_"
    )
)
async def admin_user_payments(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        user_id = int(
            call.data.replace(
                "admin_payments_",
                "",
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        user = get_user(user_id)
        all_payments = (
            get_all_payments() or []
        )
        payments = [
            payment
            for payment in all_payments
            if (
                isinstance(payment, dict)
                and int(
                    payment.get("user_id")
                    or 0
                )
                == int(user_id)
            )
        ]
    except Exception as e:
        print(
            f"❌ PAYMENTS ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user_display_name(user)
    payments.sort(
        key=lambda payment: str(
            payment.get("created_at")
            or ""
        ),
        reverse=True,
    )
    text = (
        "💳 <b>Платежи пользователя</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 {h(username)}\n"
        f"🆔 <code>{user_id}</code>\n\n"
    )
    if not payments:
        text += "Платежей пока нет."
    else:
        for payment in payments[:15]:
            payment_id = payment.get(
                "id",
                "?",
            )
            days = payment.get(
                "days"
            ) or 0
            external_id = (
                payment.get("payment_id")
                or payment.get("external_id")
            )
            status_value = str(
                payment.get("status")
                or "unknown"
            ).lower()
            created_at = payment.get(
                "created_at"
            )
            provider = str(
                payment.get("provider")
                or ""
            ).lower()
            amount = payment.get(
                "amount"
            )
            if status_value in (
                "paid",
                "success",
                "successful",
                "completed",
                "approved",
            ):
                status_text = "✅ Оплачен"
            elif status_value in (
                "pending",
                "processing",
                "waiting",
                "created",
            ):
                status_text = "⏳ Ожидает"
            elif status_value in (
                "cancelled",
                "canceled",
                "rejected",
                "failed",
                "error",
            ):
                status_text = "❌ Неуспешен"
            else:
                status_text = (
                    f"⚪ {status_value}"
                )
            if provider == "cashera":
                try:
                    amount_text = (
                        f"{int(amount) / 100:.2f} ₽"
                    )
                except Exception:
                    amount_text = "—"
            elif provider in (
                "stars",
                "telegram_stars",
                "xtr",
            ):
                try:
                    amount_text = (
                        f"{int(amount)} ⭐"
                    )
                except Exception:
                    amount_text = "—"
            else:
                amount_text = (
                    str(amount)
                    if amount is not None
                    else "—"
                )
            text += (
                f"💳 <b>#{h(payment_id)}</b>\n"
                f"💰 Сумма: "
                f"<b>{h(amount_text)}</b>\n"
                f"📅 "
                f"{h(format_datetime(created_at))}\n"
                f"⏳ Дней: "
                f"<b>{h(days)}</b>\n"
                f"📊 {status_text}\n"
            )
            if external_id:
                text += (
                    f"🔖 ID: "
                    f"<code>{h(external_id)}</code>\n"
                )
            text += "\n"
        if len(payments) > 15:
            text += (
                f"Показаны последние 15 "
                f"из {len(payments)}."
            )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ К пользователю",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data=(
                        "admin_users"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Админ-панель",
                    callback_data=(
                        "admin_back"
                    ),
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
        if "message is not modified" not in str(e):
            raise
# ============================================================
# ОТКЛЮЧЕНИЕ
# ============================================================
@router.callback_query(
    F.data.regexp(
        r"^disable_\d+$"
    )
)
async def disable_user_subscription(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
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
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        user = get_user(user_id)
    except Exception as e:
        print(
            f"❌ GET USER ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    if not user:
        await call.message.answer(
            "❌ Пользователь не найден."
        )
        return
    username = user_display_name(user)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Да, отключить",
                    callback_data=(
                        f"confirm_disable_{user_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Отмена",
                    callback_data=(
                        f"admin_user_{user_id}"
                    ),
                )
            ],
        ]
    )
    try:
        await call.message.edit_text(
            "⚠️ <b>Отключение подписки</b>\n\n"
            f"👤 Пользователь: "
            f"<b>{h(username)}</b>\n"
            f"🆔 ID: "
            f"<code>{user_id}</code>\n\n"
            "Подписка будет отключена.\n"
            "Постоянная ссылка останется прежней,\n"
            "но содержимое станет неактивным.\n\n"
            "<b>Продолжить?</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
@router.callback_query(
    F.data.startswith(
        "confirm_disable_"
    )
)
async def confirm_disable_subscription(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    try:
        user_id = int(
            call.data.replace(
                "confirm_disable_",
                "",
                1,
            )
        )
    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return
    await call.answer(
        "⏳ Отключаю..."
    )
    try:
        disable_subscription(
            user_id
        )
    except Exception as e:
        print(
            f"❌ DISABLE ERROR "
            f"{user_id}: {e}"
        )
        await call.message.answer(
            "❌ Ошибка при отключении."
        )
        return
    try:
        await asyncio.to_thread(
            update_subscription_file,
            user_id,
        )
    except Exception as e:
        print(
            f"⚠️ DISABLE SUB CONTENT ERROR "
            f"user={user_id}: {e}"
        )
    try:
        user = get_user(user_id)
    except Exception:
        user = None
    username = "нет"
    first_name = "нет"
    if user:
        username = (
            user.get("username")
            or "нет"
        )
        first_name = (
            user.get("first_name")
            or "нет"
        )
    subscription_url = (
        get_user_subscription_url(
            user_id
        )
    )
    text = (
        "👤 <b>Пользователь</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 <b>ID:</b> "
        f"<code>{user_id}</code>\n"
        f"👤 <b>Username:</b> "
        f"{('@' + h(username)) if username != 'нет' else 'нет'}\n"
        f"🧑‍💻 <b>Имя:</b> "
        f"{h(first_name)}\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 <b>Тариф:</b> "
        "❌ Нет подписки\n"
        "📊 <b>Статус:</b> "
        "🔴 Неактивен\n"
        "📅 <b>До:</b> нет\n"
        "⏳ <b>Осталось:</b> 0 д.\n\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    buttons = []
    add_url_button(
        buttons,
        "🔗 Открыть подписку",
        subscription_url,
    )
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
    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Пользователи",
                callback_data=(
                    "admin_users"
                ),
            )
        ]
    )
    buttons.append(
        [
            InlineKeyboardButton(
                text="🏠 Админ-панель",
                callback_data=(
                    "admin_back"
                ),
            )
        ]
    )
    try:
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=buttons
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
# ============================================================
# СТАТИСТИКА
# ============================================================
@router.callback_query(
    F.data == "admin_stats"
)
async def admin_stats(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    await call.answer()
    try:
        users = get_all_users() or []
        payments = get_all_payments() or []
    except Exception as e:
        print(
            f"❌ ADMIN STATS ERROR: {e}"
        )
        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return
    users = [
        user
        for user in users
        if isinstance(user, dict)
    ]
    payments = [
        payment
        for payment in payments
        if isinstance(payment, dict)
    ]
    total_users = len(users)
    active_users = 0
    expired_users = 0
    trial_users = 0
    no_subscription = 0
    for user in users:
        status, _ = get_subscription_status(
            user.get("subscription"),
            user.get(
                "subscription_until"
            ),
        )
        if (
            bool(
                user.get("trial_used")
            )
            and user.get(
                "subscription"
            )
            is not True
        ):
            trial_users += 1
        if status == "🟢 Активен":
            active_users += 1
        elif status == "⛔ Истёк":
            expired_users += 1
        elif (
            user.get("subscription")
            is not True
        ):
            no_subscription += 1
    successful_statuses = {
        "paid",
        "success",
        "successful",
        "completed",
        "approved",
    }
    pending_statuses = {
        "pending",
        "processing",
        "waiting",
        "created",
    }
    paid_payments = sum(
        1
        for payment in payments
        if str(
            payment.get("status")
            or ""
        ).lower()
        in successful_statuses
    )
    pending_payments = sum(
        1
        for payment in payments
        if str(
            payment.get("status")
            or ""
        ).lower()
        in pending_statuses
    )
    total_days_paid = 0
    for payment in payments:
        status = str(
            payment.get("status")
            or ""
        ).lower()
        if status in successful_statuses:
            try:
                total_days_paid += int(
                    payment.get("days")
                    or 0
                )
            except (
                TypeError,
                ValueError,
            ):
                pass
    current_time = (
        datetime.now(
            timezone.utc
        ).strftime(
            "%d.%m.%Y %H:%M UTC"
        )
    )
    text = (
        "📊 <b>Статистика ixxy</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "👥 <b>Пользователи</b>\n"
        f"├ Всего: "
        f"<b>{total_users}</b>\n"
        f"├ 🟢 Активных: "
        f"<b>{active_users}</b>\n"
        f"├ 🎁 Пробных: "
        f"<b>{trial_users}</b>\n"
        f"├ ⛔ Истёкших: "
        f"<b>{expired_users}</b>\n"
        f"└ 🔴 Без подписки: "
        f"<b>{no_subscription}</b>\n\n"
        "💳 <b>Платежи</b>\n"
        f"├ Всего: "
        f"<b>{len(payments)}</b>\n"
        f"├ ✅ Оплачено: "
        f"<b>{paid_payments}</b>\n"
        f"└ ⏳ Ожидают: "
        f"<b>{pending_payments}</b>\n\n"
        "📅 <b>Оформлено дней:</b> "
        f"<b>{total_days_paid}</b>\n\n"
        "📡 <b>Трафик:</b> "
        "<b>нет данных</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Обновлено: "
        f"<b>{current_time}</b>"
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=(
                        "admin_stats"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data=(
                        "admin_users"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=(
                        "admin_back"
                    ),
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
        if "message is not modified" not in str(e):
            raise
# ============================================================
# СИНХРОНИЗАЦИЯ СЕРВЕРОВ
# ============================================================
@router.callback_query(
    F.data == "admin_sync_servers"
)
async def sync_servers(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return
    # Отвечаем на callback сразу.
    try:
        await call.answer(
            "🔄 Обновление началось..."
        )
    except TelegramBadRequest:
        pass
    status_message = (
        await call.message.answer(
            "🔄 <b>Обновляю серверы...</b>\n\n"
            "⏳ Получаю актуальный список серверов\n"
            "и обновляю содержимое подписок...",
            parse_mode="HTML",
        )
    )
    try:
        # Запускаем синхронную функцию
        # в отдельном потоке.
        result = await asyncio.to_thread(
            sync_servers_update
        )
        if not isinstance(result, dict):
            result = {}
        total = result.get(
            "total",
            0,
        )
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
            result.get(
                "failed",
                0,
            ),
        )
        print(
            "🔄 IXXY: серверы обновлены: "
            f"{result}"
        )
        await status_message.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"
            f"📡 Всего серверов: "
            f"<b>{total}</b>\n"
            f"🟢 Обновлено: "
            f"<b>{updated}</b>\n"
            f"⛔ Неактивных обновлено: "
            f"<b>{expired}</b>\n"
            f"⏭ Пропущено: "
            f"<b>{skipped}</b>\n"
            f"❌ Ошибок: "
            f"<b>{errors}</b>\n\n"
            "🔗 Постоянные ссылки пользователей "
            "не изменились.",
            parse_mode="HTML",
        )
    except Exception as e:
        print(
            f"❌ SYNC ERROR: {e}"
        )
        try:
            await status_message.edit_text(
                "❌ <b>Не удалось обновить серверы.</b>\n\n"
                "Ошибка:\n"
                f"<code>{h(str(e))}</code>",
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass