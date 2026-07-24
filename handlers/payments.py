from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import (
    ADMIN_ID,
    BS_LINK
)

from keyboards import approve_keyboard

from database import (
    add_payment,
    activate_subscription
)


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(message: Message):


    photo = message.photo[-1].file_id


    # пока 30 дней
    # позже подключим выбор тарифа

    add_payment(
        message.from_user.id,
        photo,
        30
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


🆔 ID:
{message.from_user.id}


👤 Username:
@{message.from_user.username}


📅 Срок:
30 дней
""",

        reply_markup=approve_keyboard(
            message.from_user.id
        )

    )





# =====================
# ВЫДАТЬ
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



    activate_subscription(

        user_id,

        BS_LINK,

        30

    )



    await callback.bot.send_message(

        user_id,

        f"""
🎉 Оплата подтверждена!


👑 Орёл VPN активирован


📅 Срок:
30 дней


🔗 Подписка:

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

        "❌ Оплата отклонена."

    )



    await callback.message.edit_caption(

        caption=
        "❌ Чек отклонён"

    )


    await callback.answer()