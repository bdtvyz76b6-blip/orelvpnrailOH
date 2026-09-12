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
# TELEGRAM
# ============================================================

TELEGRAM_URL = "https://t.me/orelvpntopbot"


# ============================================================
# GITHUB RAW — ПРЯМАЯ ССЫЛКА ПОДПИСКИ
# ============================================================

GITHUB_RAW_URL = (
    "https://raw.githubusercontent.com/"
    "bdtvyz76b6-blip/vpn-sub/main/users"
)


def get_subscription_url(user_id: int) -> str:
    """
    Возвращает постоянную прямую ссылку
    на персональный файл пользователя GitHub.
    """

    return (
        f"{GITHUB_RAW_URL}/"
        f"{user_id}.txt"
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
    # Дата окончания
    # --------------------------------------------------------

    until = user[4] or ""

    until_text = "—"

    days = 0

    if until:

        try:

            expire_date = datetime.strptime(
                str(until),
                "%Y-%m-%d",
            ).date()

            today = datetime.now().date()

            until_text = expire_date.strftime(
                "%d.%m.%Y"
            )

            days = max(
                0,
                (
                    expire_date
                    - today
                ).days,
            )

        except Exception as e:

            print(
                f"❌ Ошибка даты "
                f"{user_id}: {e}"
            )

    # ========================================================
    # КАБИНЕТ
    # ========================================================

    text = f"""
☂️ <b>ixxy VPN</b>

👤 <b>Личный кабинет</b>

━━━━━━━━━━━━━━━━━━

🎫 <b>Подписка</b>

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
    # ПРЯМАЯ GITHUB RAW ССЫЛКА
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
    # Прямая ссылка
    # --------------------------------------------------------

    subscription_url = get_subscription_url(
        user_id
    )

    # --------------------------------------------------------
    # Отправляем ссылку
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

    # --------------------------------------------------------
    # Дата
    # --------------------------------------------------------

    until = user[4] or ""

    if not until:

        await callback.answer(
            "❌ Нет активной подписки",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Парсим дату
    # --------------------------------------------------------

    try:

        date = datetime.strptime(
            str(until),
            "%Y-%m-%d",
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

    # --------------------------------------------------------
    # Обновление GitHub
    # --------------------------------------------------------

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    try:

        update_subscription_file(
            user_id,
            date_text,
        )

        subscription_url = get_subscription_url(
            user_id
        )

        await callback.message.answer(
            f"""
✅ <b>Серверы обновлены</b>

🔗 Ссылка осталась прежней:

<code>{subscription_url}</code>
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
    # Пользователь
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
        "date",
        "",
    )

    # --------------------------------------------------------
    # Обновляем GitHub-файл
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
    # Формат даты
    # --------------------------------------------------------

    try:

        date_text = datetime.strptime(
            str(new_date),
            "%Y-%m-%d",
        ).strftime(
            "%d.%m.%Y"
        )

    except Exception:

        date_text = str(
            new_date
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