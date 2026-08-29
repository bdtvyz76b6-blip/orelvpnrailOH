import os

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from datetime import datetime

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
)


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
# ПЕРСОНАЛЬНАЯ СТРАНИЦА ПОДПИСКИ
# ============================================================

def get_subscription_page_url(user_id: int) -> str:

    token = f"{SUBSCRIPTION_PREFIX}{user_id}"

    return f"{PUBLIC_SITE_URL}/s/{token}"


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
async def cabinet(message: Message):

    await show_cabinet(message)


# ============================================================
# ПОКАЗ КАБИНЕТА
# ============================================================

async def show_cabinet(message: Message):

    user_id = message.from_user.id

    # --------------------------------------------------------
    # Проверяем подписку
    # --------------------------------------------------------

    try:

        check_user_subscription(user_id)

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

    # --------------------------------------------------------
    # Получаем пользователя
    # --------------------------------------------------------

    user = get_user(user_id)

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    # --------------------------------------------------------
    # Данные пользователя
    # --------------------------------------------------------

    subscription = user[3] or ""
    until = user[4] or ""

    # --------------------------------------------------------
    # Тариф
    # --------------------------------------------------------

    if subscription == "trial":

        tariff = "🎁 Пробный период"

    elif subscription == "vip":

        tariff = "🎫 Подписка"

    else:

        tariff = "—"

    # --------------------------------------------------------
    # Дата и оставшиеся дни
    # --------------------------------------------------------

    until_text = "—"
    days = 0

    if until:

        try:

            expire_date = datetime.strptime(
                str(until),
                "%Y-%m-%d"
            ).date()

            today = datetime.now().date()

            until_text = expire_date.strftime(
                "%d.%m.%Y"
            )

            days = max(
                0,
                (expire_date - today).days
            )

        except Exception as e:

            print(
                f"❌ Ошибка даты "
                f"{user_id}: {e}"
            )

    # ========================================================
    # ДЕЛОВОЙ ЛИЧНЫЙ КАБИНЕТ
    # ========================================================

    text = f"""
☂️ <b>ixxy VPN</b>

<b>Личный кабинет</b>

🎫 {tariff}

📅 До: <b>{until_text}</b>
⏳ Осталось: <b>{days} дн.</b>
"""

    # ========================================================
    # ВАЖНО:
    # cabinet_keyboard НЕ принимает user_id
    # ========================================================

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
async def get_link(callback: CallbackQuery):

    user_id = callback.from_user.id

    # --------------------------------------------------------
    # Проверяем подписку
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
    # Проверяем пользователя
    # --------------------------------------------------------

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Персональная страница
    # --------------------------------------------------------

    site_url = get_subscription_page_url(
        user_id
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Открыть страницу",
                    url=site_url,
                )
            ]
        ]
    )

    await callback.message.answer(
        """
⚡ <b>Подключение ixxy VPN</b>

Ваша персональная страница
подключения готова.

На ней можно:

• добавить VPN в Happ
• добавить VPN в INCY
• скопировать ссылку

👇
""",
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ОБНОВИТЬ СЕРВЕРА
# ============================================================

@router.callback_query(
    F.data == "refresh_subscription"
)
async def refresh_subscription(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    # --------------------------------------------------------
    # Проверяем подписку
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

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True,
        )

        return

    until = user[4] or ""

    if not until:

        await callback.answer(
            "❌ Нет активной подписки",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    try:

        date = datetime.strptime(
            str(until),
            "%Y-%m-%d"
        )

        date_text = date.strftime(
            "%d.%m.%Y"
        )

    except Exception as e:

        print(
            f"❌ Ошибка даты "
            f"{user_id}: {e}"
        )

        await callback.answer(
            "❌ Ошибка даты подписки",
            show_alert=True,
        )

        return

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    # --------------------------------------------------------
    # Обновляем
    # --------------------------------------------------------

    try:

        update_subscription_file(
            user_id,
            date_text,
        )

        await callback.message.answer(
            """
✅ <b>Серверы обновлены</b>

Ссылка подключения осталась прежней.
""",
            parse_mode="HTML",
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
    state: FSMContext
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
    state: FSMContext
):

    user_id = message.from_user.id

    # --------------------------------------------------------
    # Проверяем текст
    # --------------------------------------------------------

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
            "❌ Произошла ошибка "
            "при активации."
        )

        return

    # --------------------------------------------------------
    # Не найден
    # --------------------------------------------------------

    if result.get("reason") == "not_found":

        await state.clear()

        await message.answer(
            "❌ Промокод не найден."
        )

        return

    # --------------------------------------------------------
    # Уже использован
    # --------------------------------------------------------

    if result.get("reason") == "already_used":

        await state.clear()

        await message.answer(
            "❌ Вы уже использовали "
            "этот промокод."
        )

        return

    # --------------------------------------------------------
    # Пользователь не найден
    # --------------------------------------------------------

    if result.get("reason") == "user_not_found":

        await state.clear()

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    # --------------------------------------------------------
    # Общая ошибка
    # --------------------------------------------------------

    if not result.get("success"):

        await state.clear()

        await message.answer(
            "❌ Не удалось активировать "
            "промокод."
        )

        return

    # --------------------------------------------------------
    # Успешно
    # --------------------------------------------------------

    days = result.get(
        "days",
        0,
    )

    new_date = result.get(
        "date",
        "",
    )

    # --------------------------------------------------------
    # Обновляем подписку
    # --------------------------------------------------------

    try:

        update_subscription_file(
            user_id,
            new_date,
        )

    except Exception as e:

        print(
            f"❌ Ошибка обновления "
            f"серверов {user_id}: {e}"
        )

    # --------------------------------------------------------
    # Форматируем дату
    # --------------------------------------------------------

    try:

        date_text = datetime.strptime(
            str(new_date),
            "%Y-%m-%d"
        ).strftime(
            "%d.%m.%Y"
        )

    except Exception:

        date_text = str(new_date)

    await state.clear()

    # --------------------------------------------------------
    # Результат
    # --------------------------------------------------------

    await message.answer(
        f"""
🎉 <b>Промокод активирован</b>

🎟 Код: <code>{code}</code>
➕ Начислено: <b>{days} дней</b>
📅 Подписка до: <b>{date_text}</b>

🔄 Серверы обновлены.
""",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML",
    )


# ============================================================
# ПРОДЛЕНИЕ
# ============================================================

@router.callback_query(
    F.data == "renew"
)
async def renew(
    callback: CallbackQuery
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