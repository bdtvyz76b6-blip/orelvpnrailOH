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

    await show_cabinet(
        message
    )



async def show_cabinet(message: Message):

    user_id = message.from_user.id


    # проверяем срок подписки
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



    if subscription == "vip":

        tariff = "☂️ ixxy vip"


    elif subscription == "trial":

        tariff = "🎁 Пробный период"


    else:

        tariff = "Нет подписки"



    # дата окончания

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


📅 Действует до:
{until_text}


📡 Статус:
{status}


🌍 Серверы:
Все доступные серверы тарифа


📱 Устройства:
Без ограничений


⏳ Осталось:
{days} дней


🔗 Подписка:
{"Доступна кнопка ниже" if link else "Нет активной подписки"}


📄 Документы:
Пользовательское соглашение и политика конфиденциальности доступны на сайте.
""",

        reply_markup=cabinet_keyboard()

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
            "❌ У вас нет активной подписки."
        )


    else:

        await callback.message.answer(

f"""
🔗 Ваша подписка:

{user[5]}
"""

        )


    await callback.answer()





# =====================
# ПРОДЛИТЬ
# =====================

@router.callback_query(
    F.data == "renew"
)
async def renew(
    callback: CallbackQuery
):

    await callback.message.answer(
"""
🎫 Продление подписки

Выберите способ оплаты:
""",
        reply_markup=payment_method_keyboard()
    )


    await callback.answer()