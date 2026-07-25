from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from datetime import datetime

from database import get_user

from keyboards import cabinet_keyboard


router = Router()



# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet(message: Message):

    show_cabinet(
        message
    )





async def show_cabinet(message):

    user_id = message.from_user.id


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

    link = user[6]



    if subscription == "vip":

        tariff = "🦅 Орёл VPN VIP"

    elif subscription == "trial":

        tariff = "🎁 Пробный период"

    else:

        tariff = "Нет подписки"



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


            if days < 0:

                status = "❌ Истекла"

                days = 0

            else:

                status = "✅ Активна"


        except:

            until_text = "—"
            status = "❌ Не активна"
            days = 0


    else:

        until_text = "—"
        status = "❌ Не активна"
        days = 0





    await message.answer(
f"""
👤 Личный кабинет


🆔 ID:
{user_id}


🎫 Подписка:
{tariff}


📅 До:
{until_text}


📡 Статус:
{status}


🌍 Серверов:
5


📱 Устройства:
—


⏳ Осталось:
{days} дней


🔗 Подписка:
{"Нажмите кнопку ниже" if link else "Нет ссылки"}
""",
        reply_markup=cabinet_keyboard()
    )





# =====================
# ОБНОВИТЬ КАБИНЕТ
# =====================

@router.callback_query(
    F.data == "refresh_cabinet"
)
async def refresh(callback: CallbackQuery):

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
async def get_link(callback: CallbackQuery):

    user = get_user(
        callback.from_user.id
    )


    if not user or not user[6]:

        await callback.message.answer(
            "❌ У вас нет активной подписки."
        )

    else:

        await callback.message.answer(
f"""
🔗 Ваша подписка:

{user[6]}
"""
        )


    await callback.answer()