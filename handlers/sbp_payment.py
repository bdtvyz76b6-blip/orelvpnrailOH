from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment

from database import add_payment


router = Router()


# =====================
# СБП ТАРИФЫ
# =====================

payments = {

    "sbp_30": {
        "amount": 129,
        "days": 30
    },

    "sbp_90": {
        "amount": 379,
        "days": 90
    },

    "sbp_180": {
        "amount": 659,
        "days": 180
    },

    "sbp_365": {
        "amount": 1089,
        "days": 365
    }

}


# =====================
# СОЗДАНИЕ ПЛАТЕЖА
# =====================

@router.callback_query(
    F.data.startswith("sbp_")
)
async def sbp_payment(
    callback: CallbackQuery
):

    code = callback.data

    if code not in payments:

        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True
        )

        return


    amount = payments[code]["amount"]
    days = payments[code]["days"]

    user_id = callback.from_user.id


    try:

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days
        )

        print(
            "💳 PAYMENT RESULT:",
            result
        )


        # =====================
        # UUID ПЛАТЕЖА
        # =====================

        payment_uuid = (
            result.get("uuid")
            or result.get("id")
        )


        if not payment_uuid:

            await callback.message.answer(
                f"""
❌ Cashera не вернула ID платежа.

Ответ:

{result}
"""
            )

            await callback.answer()

            return


        # =====================
        # ССЫЛКА
        # =====================

        link = (
            result.get("payment_url")
            or result.get("url")
        )


        if not link:

            await callback.message.answer(
                f"""
❌ Не удалось создать платёж.

Ответ Cashera:

{result}
"""
            )

            await callback.answer()

            return


        # =====================
        # СОХРАНЯЕМ ПЛАТЁЖ
        # =====================

        add_payment(
            user_id=user_id,
            photo="",
            days=days
        )


        # Сохраняем UUID платежа
        # в отдельной записи через функцию ниже
        from database import save_payment_id

        save_payment_id(
            user_id=user_id,
            payment_id=payment_uuid
        )


        # =====================
        # ОТПРАВЛЯЕМ ССЫЛКУ
        # =====================

        await callback.message.answer(
f"""
☂️ ixxy VPN

💳 Оплата СБП

📅 Срок: {days} дней

💰 Цена: {amount}₽

🔗 Оплатить:

{link}

После успешной оплаты подписка
выдастся автоматически.
"""
        )


    except Exception as e:

        print(
            "❌ SBP ERROR:",
            e
        )

        await callback.message.answer(
f"""
❌ Ошибка создания платежа:

{e}
"""
        )


    await callback.answer()