from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import (
    ADMIN_ID,
    BS_LINK
)

from database import (
    add_payment,
    get_pending_days,
    activate_subscription
)

from keyboards import approve_keyboard


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(message: Message):


    photo = message.photo[-1].file_id


    days = get_pending_days(
        message.from_user.id
    )


    add_payment(
        message.from_user.id,
        photo,
        days
    )



    await message.answer(
        "✅ Скриншот отправлен администратору.\n\n"
        "Ожидайте проверки."
    )



    await message.bot.send_photo(

        ADMIN_ID,

        photo,

        caption=f"""
💳 Новый чек


👤 Пользователь:
{message.from_user.full_name}


🆔 ID:
{message.from_user.id}


📅 Срок:
{days} дней
""",

        reply_markup=approve_keyboard(
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


    # пока берём срок из базы

    days = get_pending_days(
        user_id
    )



    activate_subscription(

        user_id,

        BS_LINK,

        days

    )



    await callback.bot.send_message(

        user_id,

        f"""
🎉 Оплата подтверждена!


🦅 Орёл VPN активирован


📅 Срок:
{days} дней


🔗 Ваша подписка:

{BS_LINK}
"""
    )



    await callback.message.edit_caption(

        caption=
        "✅ Подписка выдана"

    )


    await callback.answer(
        "Готово"
    )







# =====================
# ОТКЛОНЕНИЕ
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

        "❌ Оплата отклонена.\n"
        "Обратитесь в поддержку."

    )



    await callback.message.edit_caption(

        caption=
        "❌ Чек отклонён"

    )


    await callback.answer()