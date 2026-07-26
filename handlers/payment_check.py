from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_ID

from database import (
    add_payment,
    get_pending_days
)

from keyboards import approve_keyboard


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(
    message: Message
):

    user_id = message.from_user.id


    photo = message.photo[-1].file_id



    days = get_pending_days(
        user_id
    )


    if not days:

        await message.answer(
            """
❌ Сначала выберите срок подписки.
"""
        )

        return



    payment_id = add_payment(
        user_id,
        photo,
        days
    )



    await message.answer(
        """
✅ Чек отправлен.

Ожидайте проверки.
"""
    )



    await message.bot.send_photo(

        ADMIN_ID,

        photo,

        caption=f"""
💳 Новый чек

👤 Пользователь:
{message.from_user.full_name}

🆔 ID:
{user_id}

👤 Username:
@{message.from_user.username}

📅 Срок:
{days} дней

🧾 Платёж:
#{payment_id}
""",

        reply_markup=approve_keyboard(
            user_id,
            payment_id
        )

    )