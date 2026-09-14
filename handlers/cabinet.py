from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from datetime import datetime, date, timezone

from database import (
    get_user,
    use_promocode,
)

from keyboards import (
    cabinet_keyboard,
    payment_method_keyboard,
)

from github_update import (
    update_subscription_file,
    get_subscription_link,
)


router = Router()


# ============================================================
# CONFIG
# ============================================================

TELEGRAM_URL = "https://t.me/orelvpntopbot"

PUBLIC_SITE_URL = "https://ixxyweb.onrender.com"
SUBSCRIPTION_PREFIX = "2ix847xy"


# ============================================================
# ССЫЛКА ПОДПИСКИ
# ============================================================

def get_subscription_url(user_id: int) -> str:
    """
    Постоянная ссылка ixxy VPN.
    """

    user_id = int(user_id)

    try:
        link = get_subscription_link(user_id)

        if link:
            return str(link).strip()

    except Exception as e:
        print(
            f"⚠️ Ошибка получения subscription link "
            f"{user_id}: {e}"
        )

    return (
        f"{PUBLIC_SITE_URL}/sub/"
        f"{SUBSCRIPTION_PREFIX}{user_id}"
    )


# ============================================================
# ДАТА
# ============================================================

def normalize_date(value):
    """
    Преобразует PostgreSQL datetime/date/строку в date.
    """

    if value is None:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return value.astimezone(
            timezone.utc
        ).date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        ).date()

    except Exception:
        pass

    try:
        return datetime.strptime(
            text[:10],
            "%Y-%m-%d",
        ).date()

    except Exception:
        pass

    try:
        return datetime.strptime(
            text[:10],
            "%d.%m.%Y",
        ).date()

    except Exception:
        return None


def format_date_ru(value) -> str:

    parsed = normalize_date(value)

    if not parsed:
        return "—"

    return parsed.strftime(
        "%d.%m.%Y"
    )


# ============================================================
# ПРОМОКОД
# ============================================================

class PromoState(StatesGroup):
    waiting_code = State()


# ============================================================
# ПРОВЕРКА АКТИВНОСТИ
# ============================================================

def is_subscription_active(user: dict) -> bool:
    """
    Единственный источник истины для ЛК:
    subscription_until.

    Если дата окончания сегодня или позже —
    подписка активна.

    Поле subscription здесь НЕ используется.
    """

    if not isinstance(user, dict):
        return False

    expire_date = normalize_date(
        user.get("subscription_until")
    )

    if not expire_date:
        return False

    today = datetime.now(
        timezone.utc
    ).date()

    return expire_date >= today


# ============================================================
# ПОЛУЧЕНИЕ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def get_current_user(user_id: int):
    try:
        return get_user(
            int(user_id)
        )

    except Exception as e:
        print(
            f"❌ Ошибка получения пользователя "
            f"{user_id}: {e}"
        )

        return None


# ============================================================
# ЛИЧНЫЙ КАБИНЕТ
# ============================================================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet(
    message: Message,
):

    await show_cabinet(
        message
    )


# ============================================================
# ПОКАЗ КАБИНЕТА
# ============================================================

async def show_cabinet(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    user = get_current_user(
        user_id
    )

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    # --------------------------------------------------------
    # ДАТА ОКОНЧАНИЯ
    # --------------------------------------------------------

    expire_date = normalize_date(
        user.get("subscription_until")
    )

    today = datetime.now(
        timezone.utc
    ).date()

    # --------------------------------------------------------
    # АКТИВНОСТЬ
    # --------------------------------------------------------

    if expire_date:

        subscription_active = (
            expire_date >= today
        )

    else:

        subscription_active = False

    # --------------------------------------------------------
    # ДНИ
    # --------------------------------------------------------

    if subscription_active:

        days = (
            expire_date - today
        ).days

        days = max(
            0,
            days,
        )

    else:

        days = 0

    # --------------------------------------------------------
    # СТАТУС
    # --------------------------------------------------------

    if subscription_active:

        status_text = "🟢 Активна"

    else:

        status_text = "🔴 Не активна"

    # --------------------------------------------------------
    # ДАТА
    # --------------------------------------------------------

    until_text = format_date_ru(
        expire_date
    )

    # ========================================================
    # ТЕКСТ
    # ========================================================

    text = (
        "☂️ <b>ixxy VPN</b>\n\n"
        "👤 <b>Личный кабинет</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🎫 <b>Подписка</b>\n\n"
        "📊 Статус:\n"
        f"<b>{status_text}</b>\n\n"
        "📅 Активна до:\n"
        f"<b>{until_text}</b>\n\n"
        "⏳ Осталось:\n"
        f"<b>{days} дн.</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите действие ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML",
    )


# ============================================================
# ПОДКЛЮЧИТЬСЯ
# ============================================================

@router.callback_query(
    F.data == "get_link"
)
async def get_link(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    # --------------------------------------------------------
    # Получаем пользователя
    # --------------------------------------------------------

    user = get_current_user(
        user_id
    )

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Проверяем ТОЛЬКО subscription_until
    # --------------------------------------------------------

    if not is_subscription_active(user):

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Постоянная ссылка
    # --------------------------------------------------------

    subscription_url = get_subscription_url(
        user_id
    )

    # --------------------------------------------------------
    # Кнопки
    # --------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Открыть подписку",
                    url=subscription_url,
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Получить ссылку",
                    callback_data="copy_subscription_link",
                )
            ],
        ]
    )

    # --------------------------------------------------------
    # Сообщение
    # --------------------------------------------------------

    text = (
        "⚡ <b>Подключение ixxy VPN</b>\n\n"
        "🔗 <b>Ваша ссылка подписки:</b>\n\n"
        f"<code>{subscription_url}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📲 Скопируйте ссылку и добавьте "
        "её в VPN-клиент.\n\n"
        "☂️ Ссылка постоянная и не меняется.\n\n"
        "🔄 При обновлении серверов "
        "ссылка останется прежней.\n\n"
        "👇 <b>Выберите действие:</b>"
    )

    await callback.message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await callback.answer()


# ============================================================
# ПОЛУЧИТЬ ССЫЛКУ
# ============================================================

@router.callback_query(
    F.data == "copy_subscription_link"
)
async def copy_subscription_link(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    user = get_current_user(
        user_id
    )

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Проверяем дату
    # --------------------------------------------------------

    if not is_subscription_active(user):

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Ссылка
    # --------------------------------------------------------

    subscription_url = get_subscription_url(
        user_id
    )

    await callback.message.answer(
        (
            "🔗 <b>Ваша ссылка подписки</b>\n\n"
            f"<code>{subscription_url}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "📲 Скопируйте ссылку и добавьте "
            "её в VPN-клиент.\n\n"
            "☂️ Ссылка постоянная."
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    await callback.answer(
        "📋 Ссылка отправлена"
    )


# ============================================================
# ОБНОВИТЬ СЕРВЕРА
# ============================================================

@router.callback_query(
    F.data == "refresh_subscription"
)
async def refresh_subscription(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    user = get_current_user(
        user_id
    )

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Проверяем дату
    # --------------------------------------------------------

    if not is_subscription_active(user):

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    expire_date = normalize_date(
        user.get("subscription_until")
    )

    date_text = format_date_ru(
        expire_date
    )

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    # --------------------------------------------------------
    # Обновляем subscription content
    # --------------------------------------------------------

    try:

        update_subscription_file(
            user_id
        )

        subscription_url = get_subscription_url(
            user_id
        )

        await callback.message.answer(
            (
                "✅ <b>Серверы обновлены</b>\n\n"
                "📅 Подписка до:\n"
                f"<b>{date_text}</b>\n\n"
                "🔗 Постоянная ссылка:\n\n"
                f"<code>{subscription_url}</code>\n\n"
                "☂️ Ссылка не изменилась."
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except Exception as e:

        print(
            f"❌ Ошибка обновления "
            f"{user_id}: {e}"
        )

        await callback.message.answer(
            (
                "❌ <b>Не удалось обновить серверы</b>\n\n"
                "Попробуйте ещё раз."
            ),
            parse_mode="HTML",
        )


# ============================================================
# ПРОМОКОД — НАЧАЛО
# ============================================================

@router.callback_query(
    F.data == "enter_promo"
)
async def enter_promo(
    callback: CallbackQuery,
    state: FSMContext,
):

    await state.set_state(
        PromoState.waiting_code
    )

    await callback.message.answer(
        "🎟 <b>Введите промокод:</b>",
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ПРОМОКОД — ОТМЕНА
# ============================================================

@router.message(
    PromoState.waiting_code,
    F.text.in_({
        "/cancel",
        "❌ Отмена",
    }),
)
async def cancel_promo(
    message: Message,
    state: FSMContext,
):

    await state.clear()

    await message.answer(
        "❌ Ввод промокода отменён.",
        reply_markup=cabinet_keyboard(),
    )


# ============================================================
# ПРОМОКОД — АКТИВАЦИЯ
# ============================================================

@router.message(
    PromoState.waiting_code
)
async def activate_promo(
    message: Message,
    state: FSMContext,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    if not message.text:

        await message.answer(
            "❌ Введите промокод текстом."
        )

        return

    code = (
        message.text
        .strip()
        .upper()
    )

    if not code:

        await message.answer(
            "❌ Промокод не может быть пустым."
        )

        return

    # --------------------------------------------------------
    # Активация
    # --------------------------------------------------------

    try:

        result = use_promocode(
            user_id,
            code,
        )

    except Exception as e:

        print(
            f"❌ Ошибка промокода "
            f"{user_id}: {e}"
        )

        await state.clear()

        await message.answer(
            "❌ Произошла ошибка при активации.",
            reply_markup=cabinet_keyboard(),
        )

        return

    # --------------------------------------------------------
    # Ожидаемый формат:
    # (success, message, days)
    # --------------------------------------------------------

    if (
        not isinstance(result, tuple)
        or len(result) != 3
    ):

        await state.clear()

        await message.answer(
            "❌ Сервер вернул некорректный ответ.",
            reply_markup=cabinet_keyboard(),
        )

        return

    success, result_message, days = result

    # --------------------------------------------------------
    # Ошибка
    # --------------------------------------------------------

    if not success:

        await state.clear()

        await message.answer(
            f"❌ {result_message}",
            reply_markup=cabinet_keyboard(),
        )

        return

    # --------------------------------------------------------
    # Обновляем подписку
    # --------------------------------------------------------

    try:

        update_subscription_file(
            user_id
        )

    except Exception as e:

        print(
            f"⚠️ Ошибка обновления "
            f"подписки {user_id}: {e}"
        )

    # --------------------------------------------------------
    # Получаем новую дату
    # --------------------------------------------------------

    updated_user = get_current_user(
        user_id
    )

    new_date = None

    if updated_user:

        new_date = updated_user.get(
            "subscription_until"
        )

    date_text = format_date_ru(
        new_date
    )

    subscription_url = get_subscription_url(
        user_id
    )

    await state.clear()

    # --------------------------------------------------------
    # Результат
    # --------------------------------------------------------

    await message.answer(
        (
            "🎉 <b>Промокод активирован</b>\n\n"
            "🎟 Код:\n"
            f"<code>{code}</code>\n\n"
            "➕ Начислено:\n"
            f"<b>{days} дней</b>\n\n"
            "📅 Подписка до:\n"
            f"<b>{date_text}</b>\n\n"
            "🔄 Подписка обновлена.\n\n"
            "🔗 Ваша постоянная ссылка:\n"
            f"<code>{subscription_url}</code>"
        ),
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ============================================================
# ПРОДЛЕНИЕ
# ============================================================

@router.callback_query(
    F.data == "renew"
)
async def renew(
    callback: CallbackQuery,
):

    await callback.message.answer(
        (
            "☂️ <b>Продление ixxy VPN</b>\n\n"
            "Выберите способ оплаты:"
        ),
        reply_markup=payment_method_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()