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

from datetime import datetime
from html import escape

from config import ADMIN_IDS
from keyboards import admin_menu

from database import (
    get_all_users,
    get_user,
    get_subscription_link,
    get_user_payments,
    get_payments,
    disable_subscription,
    extend_subscription,
    today_msk,
)

from github_update import (
    sync_servers_update,
    update_subscription_file,
    get_subscription_link as get_github_subscription_link,
)


router = Router()


# ============================================================
# НАСТРОЙКИ
# ============================================================

USERS_PER_PAGE = 15
MAX_CUSTOM_DAYS = 999_999_999


# ============================================================
# ПОИСК
# ============================================================

class AdminSearch(StatesGroup):
    waiting_query = State()


# ============================================================
# СВОЁ КОЛИЧЕСТВО ДНЕЙ
# ============================================================

class AdminCustomExtend(StatesGroup):
    waiting_days = State()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# ССЫЛКА НА ПОДПИСКУ
# ============================================================

def get_user_subscription_url(user_id: int) -> str:
    try:
        link = get_github_subscription_link(user_id)

        if link:
            return str(link).strip()

    except Exception as e:
        print(
            f"⚠️ GITHUB SUB LINK ERROR "
            f"user={user_id}: {e}"
        )

    try:
        link = get_subscription_link(user_id)

        if link:
            return str(link).strip()

    except Exception as e:
        print(
            f"⚠️ DB SUB LINK ERROR "
            f"user={user_id}: {e}"
        )

    return (
        "https://raw.githubusercontent.com/"
        "bdtvyz76b6-blip/vpn-sub/main/users/"
        f"{user_id}.txt"
    )


# ============================================================
# БЕЗОПАСНЫЙ HTML
# ============================================================

def h(value) -> str:
    return escape(str(value or ""))


# ============================================================
# СТАТУС ПОДПИСКИ
# ============================================================

def get_subscription_status(
    subscription,
    subscription_until,
):
    if subscription in (
        None,
        "",
        "none",
        "expired",
    ):
        return "🔴 Неактивен", 0

    if not subscription_until:
        return "🔴 Неактивен", 0

    try:
        if isinstance(subscription_until, datetime):
            expire_date = subscription_until.date()
        else:
            expire_date = datetime.strptime(
                str(subscription_until),
                "%Y-%m-%d",
            ).date()

    except Exception:
        return "⚠️ Ошибка даты", 0

    try:
        today = today_msk()
    except Exception:
        today = datetime.now().date()

    if expire_date < today:
        return "⛔ Истёк", 0

    days = (expire_date - today).days

    return "🟢 Активен", days


# ============================================================
# ТАРИФ
# ============================================================

def get_tariff_name(subscription):
    if subscription == "vip":
        return "☂️ ixxy VIP"

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

    return str(subscription)


# ============================================================
# ДАТА
# ============================================================

def format_date(value):
    if not value:
        return "нет"

    try:
        if isinstance(value, datetime):
            return value.strftime("%d.%m.%Y")

        return datetime.strptime(
            str(value),
            "%Y-%m-%d",
        ).strftime("%d.%m.%Y")

    except Exception:
        return str(value)


# ============================================================
# КНОПКА URL
# ============================================================

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


# ============================================================
# НАЗАД
# ============================================================

@router.callback_query(
    F.data == "admin_back"
)
async def admin_back(
    call: CallbackQuery,
):
    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return

    # Сначала закрываем callback
    await call.answer()

    try:
        await call.message.edit_text(
            "🛠 <b>Админ-панель ixxy</b>\n\n"
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
        min(page, total_pages - 1),
    )

    start = page * USERS_PER_PAGE
    end = start + USERS_PER_PAGE

    page_users = users[start:end]

    buttons = []

    for user in page_users:
        user_id = user[0]

        username = (
            user[1]
            or f"ID {user_id}"
        )

        subscription = user[3]
        subscription_until = user[4]

        status, days = get_subscription_status(
            subscription,
            subscription_until,
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
                        f"👤 {username} "
                        f"• {status_text}"
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


# ============================================================
# ПОКАЗ ПОЛЬЗОВАТЕЛЕЙ
# ============================================================

async def render_users(
    call: CallbackQuery,
    page=0,
):
    try:
        users = get_all_users()

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

    (
        keyboard,
        page,
        total_pages,
    ) = build_users_keyboard(
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


# ============================================================
# USERS
# ============================================================

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

    # ВАЖНО:
    # закрываем callback ДО работы с БД
    await call.answer()

    await render_users(
        call,
        0,
    )


# ============================================================
# ПАГИНАЦИЯ
# ============================================================

@router.callback_query(
    F.data.startswith("admin_users_page_")
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
            )
        )

    except ValueError:
        await call.answer(
            "❌ Неверная страница",
            show_alert=True,
        )
        return

    # ВАЖНО:
    # callback закрываем сразу
    await call.answer()

    await render_users(
        call,
        page,
    )


# ============================================================
# NOOP
# ============================================================

@router.callback_query(
    F.data == "admin_users_noop"
)
async def users_noop(
    call: CallbackQuery,
):
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
                    callback_data="admin_search_cancel",
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


# ============================================================
# ОТМЕНА ПОИСКА
# ============================================================

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


# ============================================================
# ОБРАБОТКА ПОИСКА
# ============================================================

@router.message(
    AdminSearch.waiting_query
)
async def admin_search_query(
    message: Message,
    state: FSMContext,
):
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
        users = get_all_users()

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
        user_id = str(
            user[0]
        ).lower()

        username = str(
            user[1] or ""
        ).lower().lstrip("@")

        first_name = str(
            user[2] or ""
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
        user_id = user[0]

        username = (
            user[1]
            or user[2]
            or f"ID {user_id}"
        )

        subscription = user[3]
        subscription_until = user[4]

        status, days = get_subscription_status(
            subscription,
            subscription_until,
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
                        f"👤 {username} "
                        f"• {state_text}"
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
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
        f"Найдено: <b>{len(found)}</b>"
        f"{extra}",
        reply_markup=keyboard,
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
            )
        )

    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return

    # Закрываем callback до БД
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

    username = user[1] or "нет"
    first_name = user[2] or "нет"

    subscription = user[3] or "none"
    subscription_until = user[4] or ""

    created_at = (
        user[11]
        if len(user) > 11
        else None
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

    tariff = get_tariff_name(
        subscription
    )

    date_text = format_date(
        subscription_until
    )

    created_text = "нет"

    if created_at:
        try:
            if isinstance(
                created_at,
                datetime,
            ):
                created_text = (
                    created_at.strftime(
                        "%d.%m.%Y %H:%M"
                    )
                )
            else:
                created_text = str(created_at)

        except Exception:
            created_text = str(created_at)

    try:
        user_payments = get_user_payments(
            user_id
        )

        payment_count = len(
            user_payments or []
        )

        paid_count = sum(
            1
            for payment in (
                user_payments or []
            )
            if len(payment) > 5
            and payment[5] == "paid"
        )

    except Exception as e:
        print(
            f"⚠️ USER PAYMENTS ERROR "
            f"{user_id}: {e}"
        )

        payment_count = 0
        paid_count = 0

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

        f"🎫 <b>Тариф:</b> "
        f"{h(tariff)}\n"

        f"📊 <b>Статус:</b> "
        f"{status}\n"

        f"📅 <b>До:</b> "
        f"{date_text}\n"

        f"⏳ <b>Осталось:</b> "
        f"{days} д.\n\n"

        "━━━━━━━━━━━━━━━━━━\n\n"

        f"💳 <b>Платежей:</b> "
        f"{payment_count}\n"

        f"✅ <b>Оплаченных:</b> "
        f"{paid_count}\n"

        f"📆 <b>Создан:</b> "
        f"{h(created_text)}"
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

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Пользователи",
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
            disable_web_page_preview=True,
        )

    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ============================================================
# ВЫБОР СРОКА ПРОДЛЕНИЯ
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

    # Сразу отвечаем Telegram
    await call.answer()

    try:
        user = get_user(user_id)

    except Exception as e:
        print(
            f"❌ GET USER ERROR {user_id}: {e}"
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

    username = (
        user[1]
        or user[2]
        or f"ID {user_id}"
    )

    current_until = user[4] or ""

    _, current_days = get_subscription_status(
        user[3],
        current_until,
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
        f"🆔 ID: <code>{user_id}</code>\n\n"
        f"📅 Сейчас осталось: "
        f"<b>{current_days} д.</b>\n\n"
        "Выбери срок продления:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ============================================================
# ЗАПРОС СВОЕГО КОЛИЧЕСТВА ДНЕЙ
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

    # Закрываем callback сразу
    await call.answer()

    user = get_user(user_id)

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
                        f"custom_extend_cancel_{user_id}"
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
        f"<b>{MAX_CUSTOM_DAYS:,}</b> дней."
        .replace(",", " "),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ============================================================
# ОТМЕНА СВОЕГО ПРОДЛЕНИЯ
# ============================================================

@router.callback_query(
    F.data.regexp(r"^custom_extend_cancel_\d+$")
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

    await call.answer("❌ Отменено")

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


# ============================================================
# ОБРАБОТКА СВОЕГО КОЛИЧЕСТВА ДНЕЙ
# ============================================================

@router.message(
    AdminCustomExtend.waiting_days
)
async def custom_extend_days(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
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
            f"<b>{MAX_CUSTOM_DAYS:,}</b> дней."
            .replace(",", " "),
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

    username = (
        user[1]
        or user[2]
        or f"ID {user_id}"
    )

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

        try:
            update_subscription_file(
                user_id,
                new_date,
            )

        except Exception as github_error:
            print(
                f"⚠️ CUSTOM GITHUB ERROR "
                f"user={user_id}: "
                f"{github_error}"
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
                            text="🔄 Синхронизировать",
                            callback_data=(
                                "admin_sync_servers"
                            ),
                        )
                    ],
                ]
            )

            await message.answer(
                "⚠️ <b>Подписка продлена в базе</b>\n\n"
                f"👤 {h(username)}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                f"➕ Добавлено: "
                f"<b>{days} д.</b>\n"
                f"📅 Новая дата: "
                f"<b>{format_date(new_date)}</b>\n\n"
                "⚠️ Не удалось сразу обновить "
                "файл подписки.\n"
                "Нажми «Синхронизировать».",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

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
                        callback_data="admin_users",
                    )
                ],
            ]
        )

        await message.answer(
            "✅ <b>Подписка успешно продлена!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Пользователь: "
            f"<b>{h(username)}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"
            f"➕ Добавлено: "
            f"<b>{days} дней</b>\n"
            f"📅 Действует до: "
            f"<b>{format_date(new_date)}</b>\n\n"
            "🔄 Файл подписки обновлён.",
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
# ПРОДЛЕНИЕ — ГОТОВЫЕ СРОКИ
# ============================================================

@router.callback_query(
    F.data.startswith("extend_days_")
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

    except (ValueError, IndexError):
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

    # Закрываем callback ДО БД
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

    username = (
        user[1]
        or user[2]
        or f"ID {user_id}"
    )

    try:
        new_date = extend_subscription(
            user_id,
            days,
        )

        if not new_date:
            raise RuntimeError(
                "База данных не вернула новую дату"
            )

        try:
            update_subscription_file(
                user_id,
                new_date,
            )

        except Exception as github_error:
            print(
                f"⚠️ GITHUB UPDATE ERROR "
                f"user={user_id}: "
                f"{github_error}"
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
                            text="🔄 Синхронизировать",
                            callback_data=(
                                "admin_sync_servers"
                            ),
                        )
                    ],
                ]
            )

            await call.message.edit_text(
                "⚠️ <b>Подписка продлена в базе</b>\n\n"
                f"👤 {h(username)}\n"
                f"🆔 <code>{user_id}</code>\n\n"
                f"➕ Добавлено: <b>{days} д.</b>\n"
                f"📅 Новая дата: "
                f"<b>{format_date(new_date)}</b>\n\n"
                "⚠️ Не удалось сразу обновить "
                "файл подписки.\n"
                "Нажми «Синхронизировать».",
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

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
                        callback_data="admin_users",
                    )
                ],
            ]
        )

        await call.message.edit_text(
            "✅ <b>Подписка успешно продлена!</b>\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Пользователь: "
            f"<b>{h(username)}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"
            f"➕ Добавлено: "
            f"<b>{days} дней</b>\n"
            f"📅 Действует до: "
            f"<b>{format_date(new_date)}</b>\n\n"
            "🔄 Файл подписки обновлён.",
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
    F.data.startswith("admin_payments_")
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
            )
        )

    except ValueError:
        await call.answer(
            "❌ Неверный ID",
            show_alert=True,
        )
        return

    # Сразу закрываем callback
    await call.answer()

    try:
        user = get_user(user_id)
        payments = get_user_payments(
            user_id
        )

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

    username = (
        user[1]
        or user[2]
        or f"ID {user_id}"
    )

    payments = payments or []

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

            payment_id = (
                payment[0]
                if len(payment) > 0
                else "?"
            )

            days = (
                payment[3]
                if len(payment) > 3
                else 0
            )

            external_id = (
                payment[4]
                if len(payment) > 4
                else None
            )

            status_value = (
                payment[5]
                if len(payment) > 5
                else "unknown"
            )

            created_at = (
                payment[6]
                if len(payment) > 6
                else ""
            )

            if status_value == "paid":
                status_text = "✅ Оплачен"

            elif status_value == "pending":
                status_text = "⏳ Ожидает"

            elif status_value == "cancelled":
                status_text = "❌ Отменён"

            else:
                status_text = (
                    f"⚪ {status_value}"
                )

            date_text = ""

            if created_at:
                try:
                    if isinstance(
                        created_at,
                        datetime,
                    ):
                        date_text = (
                            created_at.strftime(
                                "%d.%m.%Y %H:%M"
                            )
                        )
                    else:
                        date_text = str(
                            created_at
                        )

                except Exception:
                    date_text = str(
                        created_at
                    )

            text += (
                f"💳 <b>#{payment_id}</b>\n"
                f"📅 {h(date_text)}\n"
                f"⏳ Дней: <b>{days}</b>\n"
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
                    callback_data="admin_users",
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
    F.data.startswith("disable_")
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

    username = (
        user[1]
        or user[2]
        or f"ID {user_id}"
    )

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
            f"🆔 ID: <code>{user_id}</code>\n\n"
            "Подписка будет отключена.\n"
            "Файл пользователя будет переведён "
            "в состояние неактивной подписки.\n\n"
            "<b>Продолжить?</b>",
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ============================================================
# ПОДТВЕРЖДЁННОЕ ОТКЛЮЧЕНИЕ
# ============================================================

@router.callback_query(
    F.data.startswith("confirm_disable_")
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
        user = get_user(user_id)

    except Exception:
        user = None

    username = "нет"
    first_name = "нет"

    if user:
        username = user[1] or "нет"
        first_name = user[2] or "нет"

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

        "📅 <b>До:</b> "
        "нет\n"

        "⏳ <b>Осталось:</b> "
        "0 д.\n\n"

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
                callback_data="admin_users",
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=buttons
    )

    try:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
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

    # Сразу закрываем callback
    await call.answer()

    try:
        users = get_all_users()
        payments = get_payments()

    except Exception as e:
        print(
            f"❌ ADMIN STATS ERROR: {e}"
        )

        await call.message.answer(
            "❌ Ошибка базы данных."
        )
        return

    users = users or []
    payments = payments or []

    total_users = len(users)

    active_users = 0
    expired_users = 0
    trial_users = 0
    no_subscription = 0

    for user in users:

        subscription = (
            user[3]
            if len(user) > 3
            else "none"
        )

        subscription_until = (
            user[4]
            if len(user) > 4
            else ""
        )

        status, days = get_subscription_status(
            subscription,
            subscription_until,
        )

        if subscription == "trial":

            if days > 0:
                trial_users += 1

            elif status == "⛔ Истёк":
                expired_users += 1

        elif days > 0:
            active_users += 1

        elif status == "⛔ Истёк":
            expired_users += 1

        else:
            no_subscription += 1

    paid_payments = sum(
        1
        for payment in payments
        if len(payment) > 5
        and payment[5] == "paid"
    )

    pending_payments = sum(
        1
        for payment in payments
        if len(payment) > 5
        and payment[5] == "pending"
    )

    total_days_paid = sum(
        int(payment[3] or 0)
        for payment in payments
        if len(payment) > 5
        and payment[5] == "paid"
        and payment[3] is not None
    )

    try:
        current_time = datetime.now().strftime(
            "%d.%m.%Y %H:%M"
        )

    except Exception:
        current_time = "—"

    text = (
        "📊 <b>Статистика ixxy</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "👥 <b>Пользователи</b>\n"
        f"├ Всего: <b>{total_users}</b>\n"
        f"├ 🟢 Активных: <b>{active_users}</b>\n"
        f"├ 🎁 Пробных: <b>{trial_users}</b>\n"
        f"├ ⛔ Истёкших: <b>{expired_users}</b>\n"
        f"└ 🔴 Без подписки: "
        f"<b>{no_subscription}</b>\n\n"

        "💳 <b>Платежи</b>\n"
        f"├ Всего: <b>{len(payments)}</b>\n"
        f"├ ✅ Оплачено: <b>{paid_payments}</b>\n"
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
                    callback_data="admin_stats",
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
    if not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return

    # КРИТИЧНО:
    # callback закрывается ДО синхронизации
    await call.answer(
        "🔄 Обновление началось..."
    )

    status_message = await call.message.answer(
        "🔄 <b>Обновляю серверы...</b>\n\n"
        "⏳ Проверяю активные и "
        "истёкшие подписки...",
        parse_mode="HTML",
    )

    try:
        result = sync_servers_update()

        if not isinstance(result, dict):
            result = {}

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

        await status_message.edit_text(
            "✅ <b>Синхронизация завершена!</b>\n\n"
            f"🟢 Активных обновлено: "
            f"<b>{updated}</b>\n"
            f"⛔ Истёкших обновлено: "
            f"<b>{expired}</b>\n"
            f"⏭ Пропущено: "
            f"<b>{skipped}</b>\n"
            f"❌ Ошибок: "
            f"<b>{errors}</b>",
            parse_mode="HTML",
        )

    except Exception as e:
        print(
            f"❌ SYNC ERROR: {e}"
        )

        try:
            await status_message.edit_text(
                "❌ <b>Не удалось "
                "обновить серверы.</b>\n\n"
                "Ошибка:\n"
                f"<code>{h(str(e))}</code>",
                parse_mode="HTML",
            )

        except TelegramBadRequest:
            pass