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
    check_user_subscription,
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
# TELEGRAM
# ============================================================

TELEGRAM_URL = "https://t.me/orelvpntopbot"


# ============================================================
# ССЫЛКА ПОДПИСКИ
# ============================================================

def get_subscription_url(user_id: int) -> str:
    """
    Постоянная ссылка ixxy VPN.

    Формат:

    https://ixxyweb.onrender.com/sub/2ix847xy<ID>
    """

    try:
        link = get_subscription_link(int(user_id))

        if link:
            return str(link).strip()

    except Exception as e:
        print(
            f"⚠️ Ошибка получения subscription link "
            f"{user_id}: {e}"
        )

    return (
        "https://ixxyweb.onrender.com/sub/"
        f"2ix847xy{int(user_id)}"
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
    Главный источник истины — subscription_until.

    Если дата окончания сегодня или позже,
    подписка считается активной.

    BOOLEAN subscription используется только
    как дополнительное состояние.
    """

    if not isinstance(user, dict):
        return False

    until = normalize_date(
        user.get("subscription_until")
    )

    if not until:
        return False

    today = datetime.now(
        timezone.utc
    ).date()

    return until >= today


# ============================================================
# ЛИЧНЫЙ КАБИНЕТ
# ============================================================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet(
    message: Message,
):
    await show_cabinet(message)


# ============================================================
# ПОКАЗ КАБИНЕТА
# ============================================================

async def show_cabinet(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    # --------------------------------------------------------
    # Синхронизируем статус в БД
    # --------------------------------------------------------

    try:

        subscription_active = check_user_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

        subscription_active = False

    # --------------------------------------------------------
    # Получаем пользователя
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

        user = None

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    # --------------------------------------------------------
    # Дата окончания
    # --------------------------------------------------------

    until = user.get(
        "subscription_until"
    )

    expire_date = normalize_date(
        until
    )

    today = datetime.now(
        timezone.utc
    ).date()

    # --------------------------------------------------------
    # Проверяем именно дату
    # --------------------------------------------------------

    if expire_date:

        subscription_active = (
            expire_date >= today
        )

    else:

        subscription_active = False

    # --------------------------------------------------------
    # Количество дней
    # --------------------------------------------------------

    days = 0

    if expire_date:

        days = max(
            0,
            (
                expire_date - today
            ).days,
        )

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    if subscription_active:

        status_text = "🟢 Активна"

    else:

        status_text = "🔴 Не активна"
        days = 0

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    until_text = format_date_ru(
        until
    )

    # ========================================================
    # КАБИНЕТ
    # ========================================================

    text = f"""
☂️ <b>ixxy VPN</b>

👤 <b>Личный кабинет</b>

━━━━━━━━━━━━━━━━━━

🎫 <b>Подписка</b>

📊 Статус:
<b>{status_text}</b>

📅 Активна до:
<b>{until_text}</b>

⏳ Осталось:
<b>{days} дн.</b>

━━━━━━━━━━━━━━━━━━

Выберите действие ниже 👇
"""

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
    # Проверяем по дате
    # --------------------------------------------------------

    try:

        is_active = check_user_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

        is_active = False

    if not is_active:

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Получаем пользователя
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

        user = None

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

    # ========================================================
    # ПОСТОЯННАЯ ССЫЛКА
    # ========================================================

    subscription_url = get_subscription_url(
        user_id
    )

    # ========================================================
    # КНОПКИ
    # ========================================================

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

    # ========================================================
    # СООБЩЕНИЕ
    # ========================================================

    text = f"""
⚡ <b>Подключение ixxy VPN</b>

🔗 <b>Ваша ссылка подписки:</b>

<code>{subscription_url}</code>

━━━━━━━━━━━━━━━━━━

📲 Скопируйте ссылку и добавьте
её в VPN-клиент.

☂️ Ссылка постоянная и не меняется.

🔄 При обновлении серверов
ссылка останется прежней.

👇 <b>Выберите действие:</b>
"""

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

    # --------------------------------------------------------
    # Проверка
    # --------------------------------------------------------

    try:

        is_active = check_user_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

        is_active = False

    if not is_active:

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
        f"""
🔗 <b>Ваша ссылка подписки</b>

<code>{subscription_url}</code>

━━━━━━━━━━━━━━━━━━

📲 Скопируйте ссылку и добавьте
её в VPN-клиент.

☂️ Ссылка постоянная.
""",
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

    # --------------------------------------------------------
    # Проверка
    # --------------------------------------------------------

    try:

        is_active = check_user_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

        is_active = False

    if not is_active:

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Получаем пользователя
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

        user = None

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Проверка даты
    # --------------------------------------------------------

    if not is_subscription_active(user):

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True,
        )

        return

    until = user.get(
        "subscription_until"
    )

    expire_date = normalize_date(
        until
    )

    if not expire_date:

        await callback.answer(
            "❌ Ошибка даты подписки",
            show_alert=True,
        )

        return

    date_text = format_date_ru(
        expire_date
    )

    # --------------------------------------------------------
    # Обновление
    # --------------------------------------------------------

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    try:

        update_subscription_file(
            user_id
        )

        subscription_url = get_subscription_url(
            user_id
        )

        await callback.message.answer(
            f"""
✅ <b>Серверы обновлены</b>

📅 Подписка до:
<b>{date_text}</b>

🔗 Постоянная ссылка:

<code>{subscription_url}</code>

☂️ Ссылка не изменилась.
""",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except Exception as e:

        print(
            f"❌ Ошибка обновления "
            f"{user_id}: {e}"
        )

        await callback.message.answer(
            """
❌ <b>Не удалось обновить серверы</b>

Попробуйте ещё раз.
""",
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
    # Активируем промокод
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

    # ========================================================
    # ТВОЯ DATABASE.PY:
    #
    # use_promocode() возвращает:
    #
    # (success, message, days)
    # ========================================================

    if not isinstance(
        result,
        tuple,
    ) or len(result) != 3:

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
    # Обновляем subscription content
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

    try:

        updated_user = get_user(
            user_id
        )

    except Exception as e:

        print(
            f"⚠️ Ошибка получения "
            f"обновлённого пользователя: {e}"
        )

        updated_user = None

    new_date = None

    if updated_user:

        new_date = updated_user.get(
            "subscription_until"
        )

    date_text = format_date_ru(
        new_date
    )

    # --------------------------------------------------------
    # Ссылка
    # --------------------------------------------------------

    subscription_url = get_subscription_url(
        user_id
    )

    await state.clear()

    # --------------------------------------------------------
    # Результат
    # --------------------------------------------------------

    await message.answer(
        f"""
🎉 <b>Промокод активирован</b>

🎟 Код:
<code>{code}</code>

➕ Начислено:
<b>{days} дней</b>

📅 Подписка до:
<b>{date_text}</b>

🔄 Подписка обновлена.

🔗 Ваша постоянная ссылка:
<code>{subscription_url}</code>
""",
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
        """
☂️ <b>Продление ixxy VPN</b>

Выберите способ оплаты:
""",
        reply_markup=payment_method_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()