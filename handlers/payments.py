from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID

from database import (
    add_payment,
    activate_subscription
)

from github_update import create_subscription

from keyboards import approve_keyboard


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(message: Message):

    photo = message.photo[-1].file_id


    add_payment(
        message.from_user.id,
        photo
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


👤 Username:
@{message.from_user.username}
""",

        reply_markup=approve_keyboard(
            message.from_user.id
        )

    )





# =====================
# ПОДТВЕРЖДЕНИЕ
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


    # срок пока 30 дней
    days = 30



    # создаём персональную ссылку
    link = create_subscription(
        user_id
    )



    activate_subscription(

        user_id,

        link,

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

{link}
"""
    )



    await callback.message.edit_caption(
        caption="✅ Подписка выдана"
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

        """
❌ Оплата отклонена.

Если произошла ошибка —
обратитесь в поддержку.
"""

    )


    await callback.message.edit_caption(
        caption="❌ Чек отклонён"
    )


    await callback.answer()