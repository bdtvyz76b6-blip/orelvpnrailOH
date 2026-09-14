from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from datetime import datetime, date

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

    Пример:

    https://ixxyweb.onrender.com/sub/2ix847xy6312016802

    Ссылка НЕ зависит от GitHub users/<id>.txt
    и не меняется при обновлении серверов.
    """

    return get_subscription_link(
        int(user_id)
    )


# ============================================================
# ДАТА
# ============================================================

def normalize_date(value):
    """
    Преобразует PostgreSQL datetime/date/строку
    в date.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    # PostgreSQL ISO datetime
    try:
        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        ).date()

    except Exception:
        pass

    # YYYY-MM-DD
    try:
        return datetime.strptime(
            text[:10],
            "%Y-%m-%d",
        ).date()

    except Exception:
        return None


def format_date_ru(value) -> str:
    """
    DD.MM.YYYY
    """

    parsed = normalize_date(
        value
    )

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

    user_id = message.from_user.id

    # --------------------------------------------------------
    # Проверяем подписку
    # --------------------------------------------------------

    try:

        check_user_subscription(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

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
    # PostgreSQL dict
    # --------------------------------------------------------

    until = user.get(
        "subscription_until"
    )

    subscription_active = bool(
        user.get(
            "subscription"
        )
    )

    expire_date = normalize_date(
        until
    )

    today = datetime.now().date()

    # --------------------------------------------------------
    # Если дата уже прошла
    # --------------------------------------------------------

    if (
        expire_date
        and expire_date < today
    ):

        subscription_active = False

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    until_text = format_date_ru(
        until
    )

    days = 0

    if expire_date:

        days = max(
            0,
            (
                expire_date
                - today
            ).days,
        )

    # --------------------------------------------------------
    # Статус
    # --------------------------------------------------------

    if subscription_active and days > 0:

        status_text = "🟢 Активна"

    else:

        status_text = "🔴 Не активна"
        days = 0

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
    # Проверка подписки
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

        user = None

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # ========================================================
    # ПОСТОЯННАЯ ССЫЛКА IXXY
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
    # Постоянная ссылка
    # --------------------------------------------------------

    subscription_url = get_subscription_url(
        user_id
    )

    # --------------------------------------------------------
    # Отправляем
    # --------------------------------------------------------

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
    # Проверка подписки
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
    # Дата подписки
    # --------------------------------------------------------

    until = user.get(
        "subscription_until"
    )

    if not until:

        await callback.answer(
            "❌ Нет активной подписки",
            show_alert=True,
        )

        return

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
    # Обновляем содержимое подписки
    #
    # ВАЖНО:
    # GitHub users/<id>.txt здесь больше НЕТ.
    #
    # github_update.py:
    # 1. берёт актуальный список серверов;
    # 2. собирает профиль;
    # 3. сохраняет его в PostgreSQL;
    # 4. постоянная ссылка остаётся прежней.
    # --------------------------------------------------------

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    try:

        update_subscription_file(
            user_id,
            expire_date,
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
# ПРОМОКОД — АКТИВАЦИЯ
# ============================================================

@router.message(
    PromoState.waiting_code
)
async def activate_promo(
    message: Message,
    state: FSMContext,
):

    user_id = message.from_user.id

    if not message.text:

        await message.answer(
            "❌ Введите промокод текстом."
        )

        return

    # --------------------------------------------------------
    # Код
    # --------------------------------------------------------

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
    # Активируем
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
            "❌ Произошла ошибка при активации."
        )

        return

    if not isinstance(
        result,
        dict,
    ):

        await state.clear()

        await message.answer(
            "❌ Сервер вернул некорректный ответ."
        )

        return

    # --------------------------------------------------------
    # Не найден
    # --------------------------------------------------------

    if result.get(
        "reason"
    ) == "not_found":

        await state.clear()

        await message.answer(
            "❌ Промокод не найден."
        )

        return

    # --------------------------------------------------------
    # Уже использован
    # --------------------------------------------------------

    if result.get(
        "reason"
    ) == "already_used":

        await state.clear()

        await message.answer(
            "❌ Вы уже использовали этот промокод."
        )

        return

    # --------------------------------------------------------
    # Пользователь не найден
    # --------------------------------------------------------

    if result.get(
        "reason"
    ) == "user_not_found":

        await state.clear()

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    # --------------------------------------------------------
    # Ошибка
    # --------------------------------------------------------

    if not result.get(
        "success"
    ):

        await state.clear()

        await message.answer(
            "❌ Не удалось активировать промокод."
        )

        return

    # --------------------------------------------------------
    # Данные
    # --------------------------------------------------------

    days = result.get(
        "days",
        0,
    )

    new_date = result.get(
        "date"
    )

    # --------------------------------------------------------
    # Обновляем подписку в PostgreSQL
    # --------------------------------------------------------

    try:

        if new_date:

            update_subscription_file(
                user_id,
                new_date,
            )

    except Exception as e:

        print(
            f"❌ Ошибка обновления "
            f"подписки {user_id}: {e}"
        )

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    date_text = format_date_ru(
        new_date
    )

    # --------------------------------------------------------
    # Постоянная ссылка
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