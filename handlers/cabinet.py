from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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


# =========================================================
# НАСТРОЙКИ
# =========================================================
 
HAPP_URL = "https://apps.apple.com/app/happ-proxy-utility/id6504287215"

INCY_URL = "https://apps.apple.com/app/incy/id6477785520"


# =========================================================
# ПРОМОКОД
# =========================================================

class PromoState(StatesGroup):
    waiting_code = State()


# =========================================================
# ЛИЧНЫЙ КАБИНЕТ
# =========================================================

@router.message(F.text == "👤 Личный кабинет")
async def cabinet(message: Message):

    await show_cabinet(message)


# =========================================================
# ПОКАЗ КАБИНЕТА
# =========================================================

async def show_cabinet(message: Message):

    user_id = message.from_user.id

    # Проверяем срок подписки
    try:
        check_user_subscription(user_id)
    except Exception as e:
        print(f"❌ CHECK SUB ERROR {user_id}: {e}")

    user = get_user(user_id)

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    subscription = user[3]
    until = user[4]
    link = user[5]

    # =====================================================
    # ТАРИФ
    # =====================================================

    if subscription == "vip":

        tariff = "👑 ixxy VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "❌ Нет подписки"

    # =====================================================
    # СТАТУС
    # =====================================================

    status = "❌ Не активна"
    until_text = "—"
    days = 0

    if until:

        try:

            expire_date = datetime.strptime(
                str(until),
                "%Y-%m-%d"
            )

            until_text = expire_date.strftime(
                "%d.%m.%Y"
            )

            now = datetime.now()

            if expire_date > now:

                status = "🟢 Активна"

                seconds = (
                    expire_date - now
                ).total_seconds()

                days = max(
                    1,
                    int(seconds // 86400)
                )

            else:

                status = "🔴 Истекла"

        except Exception as e:

            print(
                f"❌ DATE ERROR {user_id}: {e}"
            )

    # =====================================================
    # КАБИНЕТ
    # =====================================================

    text = f"""
☂️ <b>ixxy VPN</b>

👤 <b>Личный кабинет</b>

━━━━━━━━━━━━━━━━━━

🆔 ID:
<code>{user_id}</code>

🎫 Тариф:
<b>{tariff}</b>

📊 Статус:
<b>{status}</b>

📅 Активна до:
<b>{until_text}</b>

⏳ Осталось:
<b>{days} дн.</b>

━━━━━━━━━━━━━━━━━━

🔗 <b>Ваша подписка</b>

<code>{link if link else "Ссылка отсутствует"}</code>

━━━━━━━━━━━━━━━━━━

📲 Добавьте подписку в приложение
"""

    await message.answer(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# ССЫЛКА
# =========================================================

@router.callback_query(F.data == "get_link")
async def get_link(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return

    link = user[5]

    if not link:

        await callback.answer(
            "❌ Ссылка ещё не создана",
            show_alert=True
        )

        return

    await callback.message.answer(
        f"""
🔗 <b>Ваша ссылка подписки</b>

<code>{link}</code>

📲 Выберите приложение ниже.
""",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# HAPP
# =========================================================

@router.callback_query(F.data == "add_happ")
async def add_happ(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    user = get_user(user_id)

    if not user or not user[5]:

        await callback.answer(
            "❌ Ссылка подписки отсутствует",
            show_alert=True
        )

        return

    link = user[5]

    # Специальная ссылка Happ
    happ_link = (
        "happ://sync/"
        + link
    )

    await callback.message.answer(
        f"""
📲 <b>Добавление в Happ</b>

Нажмите кнопку ниже.

После открытия Happ подписка будет добавлена автоматически.

🔗 Если автоматическое добавление не сработало:

<code>{link}</code>
""",
        reply_markup={
            "inline_keyboard": [
                [
                    {
                        "text": "📲 Открыть Happ",
                        "url": happ_link
                    }
                ]
            ]
        },
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# INCY
# =========================================================

@router.callback_query(F.data == "add_incy")
async def add_incy(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    user = get_user(user_id)

    if not user or not user[5]:

        await callback.answer(
            "❌ Ссылка подписки отсутствует",
            show_alert=True
        )

        return

    link = user[5]

    # Ссылка для добавления подписки в INCY
    incy_link = (
        "incy://import/"
        + link
    )

    await callback.message.answer(
        f"""
📲 <b>Добавление в INCY</b>

⭐ <b>Рекомендовано</b>

Нажмите кнопку ниже.

Если INCY не открылся автоматически,
скопируйте ссылку вручную:

<code>{link}</code>
""",
        reply_markup={
            "inline_keyboard": [
                [
                    {
                        "text": "📲 Открыть INCY ⭐ Рекомендовано",
                        "url": incy_link
                    }
                ]
            ]
        },
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ОБНОВИТЬ СЕРВЕРЫ
# =========================================================

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
            str(until),
            "%Y-%m-%d"
        )

        date_text = date.strftime(
            "%d.%m.%Y"
        )

    except Exception:

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
✅ <b>Серверы обновлены!</b>

🔗 Ваша ссылка осталась прежней.
📲 Можно продолжать пользоваться VPN.
""",
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"❌ REFRESH ERROR {user_id}: {e}"
        )

        await callback.message.answer(
            """
❌ <b>Не удалось обновить серверы.</b>

Попробуйте ещё раз немного позже.
""",
            parse_mode="HTML"
        )


# =========================================================
# ПРОМОКОД
# =========================================================

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
        """
🎟 <b>Активация промокода</b>

Введите промокод одним сообщением:
""",
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# АКТИВАЦИЯ ПРОМОКОДА
# =========================================================

@router.message(
    PromoState.waiting_code
)
async def activate_promo(
    message: Message,
    state: FSMContext
):

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

    try:

        result = use_promocode(
            user_id,
            code
        )

    except Exception as e:

        print(
            f"❌ PROMO ERROR {user_id}: {e}"
        )

        await state.clear()

        await message.answer(
            "❌ Произошла ошибка при активации промокода."
        )

        return

    reason = result.get(
        "reason"
    )

    if reason == "not_found":

        await state.clear()

        await message.answer(
            "❌ Промокод не найден."
        )

        return

    if reason == "already_used":

        await state.clear()

        await message.answer(
            "❌ Вы уже использовали этот промокод."
        )

        return

    if reason == "user_not_found":

        await state.clear()

        await message.answer(
            "❌ Пользователь не найден."
        )

        return

    if reason != "success":

        await state.clear()

        await message.answer(
            "❌ Не удалось активировать промокод."
        )

        return

    days = result["days"]
    new_date = result["date"]

    # Обновляем персональную подписку
    try:

        update_subscription_file(
            user_id,
            new_date
        )

    except Exception as e:

        print(
            f"❌ SUB UPDATE ERROR {user_id}: {e}"
        )

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

    await message.answer(
        f"""
🎉 <b>Промокод активирован!</b>

🎟 Код:
<code>{code}</code>

➕ Начислено:
<b>{days} дней</b>

📅 Подписка до:
<b>{date_text}</b>

🔄 Серверы обновлены.
""",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# ПРОДЛЕНИЕ
# =========================================================

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
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# НАЗАД В КАБИНЕТ
# =========================================================

@router.callback_query(
    F.data == "cabinet"
)
async def back_to_cabinet(
    callback: CallbackQuery
):

    try:

        await callback.message.delete()

    except Exception:

        pass

    await show_cabinet(
        callback.message
    )

    await callback.answer()