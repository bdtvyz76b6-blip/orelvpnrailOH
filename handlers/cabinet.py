from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from datetime import datetime

from database import (
    get_user,
    check_user_subscription
)

from keyboards import (
    cabinet_keyboard,
    payment_method_keyboard
)


router = Router()


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


    # проверяем срок
    check_user_subscription(
        user_id
    )


    user = get_user(
        user_id
    )


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
    # ДАТА И СТАТУС
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


            days = (
                date - datetime.now()
            ).days



            if days >= 0:

                status = "🟢 Активна"


            else:

                status = "🔴 Истекла"
                days = 0



        except:

            pass



    # =====================
    # ТЕКСТ
    # =====================

    text = f"""
☂️ ixxy VPN

👤 Личный кабинет

━━━━━━━━━━━━━━

🆔 ID:
<code>{user_id}</code>

🎫 Тариф:
{tariff}

📊 Статус:
{status}

📅 Действует до:
{until_text}

⏳ Осталось:
{days} дней

━━━━━━━━━━━━━━

🌍 Серверы:
Все серверы ixxy

📱 Устройства:
∞ Без ограничений

🔗 Подписка:
{"✅ Доступна" if link else "❌ Нет ссылки"}

━━━━━━━━━━━━━━
"""


    await message.answer(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )



# =====================
# ОБНОВИТЬ
# =====================

@router.callback_query(
    F.data == "refresh_cabinet"
)
async def refresh(
    callback: CallbackQuery
):

    await callback.message.delete()

    await show_cabinet(
        callback.message
    )

    await callback.answer()



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
🔗 Ваша подписка ixxy:

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