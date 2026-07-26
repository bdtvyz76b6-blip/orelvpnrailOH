from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import ADMIN_ID

from database import (
    get_payment,
    activate_subscription
)

from github_update import create_subscription


router = Router()



# =====================
# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# =====================

@router.callback_query(
    F.data.startswith("approve_")
)
async def approve_payment(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "Нет доступа",
            show_alert=True
        )

        return



    data = callback.data.split("_")


    user_id = int(data[1])

    payment_id = int(data[2])



    payment = get_payment(
        payment_id
    )


    if not payment:

        await callback.answer(
            "Платёж не найден",
            show_alert=True
        )

        return



    days = payment[1]



    # создаём GitHub подписку

    link = create_subscription(
        user_id,
        days
    )



    # активируем в базе

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
        caption=f"""
✅ Подписка выдана

👤 ID:
{user_id}

📅 Срок:
{days} дней
"""
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
async def reject_payment(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "Нет доступа",
            show_alert=True
        )

        return



    data = callback.data.split("_")


    user_id = int(
        data[1]
    )



    await callback.bot.send_message(

        user_id,

        """
❌ Оплата отклонена.

Если это ошибка — обратитесь в поддержку.
"""
    )



    await callback.message.edit_caption(
        caption="❌ Оплата отклонена"
    )


    await callback.answer()