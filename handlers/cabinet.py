from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from datetime import datetime, timedelta

from database import (
    get_user,
    check_user_subscription,
    extend_subscription,
    get_promocode
)

from keyboards import (
    cabinet_keyboard,
    payment_method_keyboard
)

from github_update import (
    update_subscription_file
)


router = Router()


# =====================
# ПРОМОКОД
# =====================

class PromoUse(StatesGroup):

    code = State()


# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet(message: Message):

    await show_cabinet(message)


async def show_cabinet(message: Message):

    user_id = message.from_user.id

    # Проверяем срок подписки
    check_user_subscription(user_id)

    user = get_user(user_id)

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    subscription = user[3]
    until = user[4]
    link = user[5]

    # =====================
    # ТАРИФ
    # =====================

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "❌ Нет подписки"

    # =====================
    # СТАТУС
    # =====================

    status = "❌ Не активна"
    until_text = "—"
    days = 0

    if until:

        try:

            date = datetime.strptime(
                until,
                "%Y-%m-%d"
            )

            until_text = date.strftime(
                "%d.%m.%Y"
            )

            seconds = (
                date - datetime.now()
            ).total_seconds()

            if seconds > 0:

                status = "🟢 Активна"

                days = max(
                    1,
                    int(seconds // 86400)
                )

            else:

                status = "🔴 Истекла"

        except:

            pass

    # =====================
    # КАБИНЕТ
    # =====================

    text = f"""
☂️ ixxy VPN

👤 Личный кабинет

━━━━━━━━━━━━━━

🆔 ID: <code>{user_id}</code>

🎫 Тариф: {tariff}

📊 Статус: {status}

📅 До: {until_text}

⏳ Осталось: {days} дней

🔗 Подписка: {"✅ Активна" if link else "❌ Нет ссылки"}

━━━━━━━━━━━━━━
"""

    await message.answer(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )


# =====================
# ПРОМОКОД
# =====================

@router.callback_query(
    F.data == "promo_use"
)
async def promo_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        PromoUse.code
    )

    await callback.message.answer(
        """
🎟 Промокод

Введите промокод:
"""
    )

    await callback.answer()


# =====================
# ПРОВЕРКА ПРОМОКОДА
# =====================

@router.message(
    PromoUse.code
)
async def promo_enter(
    message: Message,
    state: FSMContext
):

    user_id = message.from_user.id

    code = message.text.strip().upper()

    # =====================
    # ПОЛУЧАЕМ ДНИ
    # =====================

    days = get_promocode(code)

    if not days:

        await message.answer(
            """
❌ Промокод не найден.

Проверьте правильность написания.
"""
        )

        await state.clear()

        return

    # =====================
    # ПОЛЬЗОВАТЕЛЬ
    # =====================

    user = get_user(user_id)

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        await state.clear()

        return

    # =====================
    # ПРОДЛЕВАЕМ
    # =====================

    try:

        new_date = extend_subscription(
            user_id,
            days
        )

        # =====================
        # ОБНОВЛЯЕМ GITHUB
        # =====================

        update_subscription_file(
            user_id,
            new_date
        )

    except Exception as e:

        print(
            f"❌ PROMO ERROR {user_id}: {e}"
        )

        await message.answer(
            """
❌ Не удалось активировать промокод.

Попробуйте ещё раз позже.
"""
        )

        await state.clear()

        return

    # =====================
    # УСПЕШНО
    # =====================

    await message.answer(
        f"""
🎉 Промокод активирован!

🎟 Код:
{code}

➕ Начислено:
{days} дней

📅 Подписка до:
{new_date}

🔗 Ссылка осталась прежней.
""",
        reply_markup=cabinet_keyboard()
    )

    await state.clear()


# =====================
# ОБНОВИТЬ СЕРВЕРА
# =====================

@router.callback_query(
    F.data == "refresh_subscription"
)
async def refresh_subscription(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    if not check_user_subscription(user_id):

        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True
        )

        return

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    until = user[4]

    if not until:

        await callback.answer(
            "❌ Нет активной подписки",
            show_alert=True
        )

        return

    try:

        date = datetime.strptime(
            until,
            "%Y-%m-%d"
        )

        date_text = date.strftime(
            "%d.%m.%Y"
        )

    except:

        await callback.answer(
            "❌ Ошибка даты подписки",
            show_alert=True
        )

        return

    await callback.answer(
        "🔄 Обновляю серверы..."
    )

    try:

        update_subscription_file(
            user_id,
            date_text
        )

        await callback.message.answer(
            """
✅ Серверы обновлены!

🔗 Ваша ссылка осталась прежней.
"""
        )

    except Exception as e:

        print(
            f"❌ Ошибка обновления серверов "
            f"{user_id}: {e}"
        )

        await callback.message.answer(
            """
❌ Не удалось обновить серверы.

Попробуйте ещё раз.
"""
        )


# =====================
# ПОЛУЧИТЬ ССЫЛКУ
# =====================

@router.callback_query(
    F.data == "get_link"
)
async def get_link(
    callback: CallbackQuery
):

    user = get_user(
        callback.from_user.id
    )

    if not user or not user[5]:

        await callback.message.answer(
            "❌ Ссылка отсутствует."
        )

    else:

        await callback.message.answer(
            f"""
🔗 Ваша подписка:

{user[5]}

📲 Добавьте её в Happ.
"""
        )

    await callback.answer()


# =====================
# ПРОДЛЕНИЕ
# =====================

@router.callback_query(
    F.data == "renew"
)
async def renew(
    callback: CallbackQuery
):

    await callback.message.answer(
        """
☂️ Продление ixxy VPN

Выберите способ оплаты:
""",
        reply_markup=payment_method_keyboard()
    )

    await callback.answer()