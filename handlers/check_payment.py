from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID

from database import (
    add_payment,
    activate_bs,
    set_subscription_date,
    get_payment_days
)

from github_update import create_subscription

from keyboards import payment_menu

from datetime import datetime, timedelta


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def get_check(message: Message):

    photo = message.photo[-1].file_id


    # сохраняем чек
    add_payment(
        message.from_user.id,
        photo
    )


    await message.answer(
        "✅ Чек отправлен.\n"
        "Ожидайте подтверждения."
    )


    await message.bot.send_photo(

        ADMIN_ID,

        photo,

        caption=
        f"""
💳 Новая заявка


👤 Пользователь:
{message.from_user.full_name}


🆔 ID:
{message.from_user.id}
""",

        reply_markup=payment_menu(
            message.from_user.id
        )
    )





# =====================
# ВЫДАТЬ ПОДПИСКУ
# =====================

@router.callback_query(
    F.data.startswith("approve_")
)
async def approve(
    callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    # берём срок из последнего платежа
    days = get_payment_days(
        user_id
    )


    print(
        "PAYMENT APPROVED:",
        user_id,
        days
    )


    # создаём подписку с правильным сроком
    link = create_subscription(
        user_id,
        days=days
    )


    expire_date = (
        datetime.now()
        +
        timedelta(days=days)
    ).strftime(
        "%Y-%m-%d"
    )


    # сохраняем в базу
    activate_bs(
        user_id,
        link
    )


    set_subscription_date(
        user_id,
        expire_date
    )



    await callback.bot.send_message(

        user_id,

        f"""
🎉 Оплата подтверждена!


🦅 Orel VPN активирован


📅 Срок:
{days} дней


📅 Действует до:
{expire_date}


🔗 Ваша подписка:

{link}
"""

    )


    await callback.message.edit_caption(
        caption=
        "✅ Подписка выдана"
    )


    await callback.answer(
        "Выдано"
    )





# =====================
# ОТКЛОНИТЬ
# =====================

@router.callback_query(
    F.data.startswith("reject_")
)
async def reject(
    callback: CallbackQuery
):

    user_id = int(
        callback.data.split("_")[1]
    )


    await callback.bot.send_message(

        user_id,

        """
❌ Оплата отклонена.

Свяжитесь с поддержкой.
"""

    )


    await callback.message.edit_caption(
        caption=
        "❌ Заявка отклонена"
    )


    await callback.answer(
        "Отклонено"
    )