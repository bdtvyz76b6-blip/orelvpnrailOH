from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment


router = Router()



# =====================
# СБП ПЛАТЕЖИ
# =====================

payments = {

    "sbp_30": {
        "amount": 99,
        "days": 30
    },

    "sbp_90": {
        "amount": 249,
        "days": 90
    },

    "sbp_180": {
        "amount": 599,
        "days": 180
    },

    "sbp_365": {
        "amount": 999,
        "days": 365
    }

}



@router.callback_query(
    F.data.startswith("sbp_")
)
async def sbp_payment(
    callback: CallbackQuery
):

    code = callback.data


    if code not in payments:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    amount = payments[code]["amount"]

    days = payments[code]["days"]



    try:

        result = create_cashera_payment(

            user_id=callback.from_user.id,

            amount=amount,

            days=days

        )



        print(
            "💳 PAYMENT RESULT:",
            result
        )



        link = (

            result.get("payment_url")

            or

            result.get("url")

        )



        if not link:

            await callback.message.answer(
f"""
❌ Не удалось создать платёж.

Ответ Cashera:

{result}
"""
            )

            return



        await callback.message.answer(
f"""
☂️ ixxy vpn

💳 Оплата СБП


📅 Срок:
{days} дней


💰 Цена:
{amount}₽


🔗 Оплатить:

{link}


После успешной оплаты подписка будет выдана автоматически.
"""
        )



    except Exception as e:


        await callback.message.answer(
f"""
❌ Ошибка создания платежа:

{e}
"""
        )



    await callback.answer()