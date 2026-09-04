from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment

from database import (
    add_payment,
    save_payment_id,
)

router = Router()


# ============================================================
# ТАРИФЫ СБП
# ============================================================
#
# Сейчас 30 дней = 1 ₽ для безопасного теста.
#
# После успешного теста:
# "sbp_30": {"amount": 129, "days": 30},
#
# Остальные цены уже реальные.
#

PAYMENTS = {
    "sbp_30": {
        "amount": 129,
        "days": 30,
    },

    "sbp_90": {
        "amount": 379,
        "days": 90,
    },

    "sbp_180": {
        "amount": 659,
        "days": 180,
    },

    "sbp_365": {
        "amount": 1089,
        "days": 365,
    },
}


# ============================================================
# СОЗДАНИЕ ПЛАТЕЖА
# ============================================================

@router.callback_query(F.data.startswith("sbp_"))
async def sbp_payment(callback: CallbackQuery):

    code = callback.data

    if code not in PAYMENTS:
        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True
        )
        return

    plan = PAYMENTS[code]

    amount = plan["amount"]
    days = plan["days"]

    user_id = callback.from_user.id

    try:

        # ----------------------------------------------------
        # Создаём платёж в Cashera
        # ----------------------------------------------------

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days
        )

        print(
            "💳 CASHeRA PAYMENT RESULT:",
            result
        )

        if not isinstance(result, dict):

            await callback.message.answer(
                "❌ Cashera вернула некорректный ответ."
            )

            await callback.answer()
            return

        # ----------------------------------------------------
        # UUID платежа
        # ----------------------------------------------------

        payment_uuid = (
            result.get("uuid")
            or result.get("id")
        )

        if not payment_uuid:

            await callback.message.answer(
                f"""
❌ Cashera не вернула ID платежа.

Ответ Cashera:

{result}
"""
            )

            await callback.answer()
            return

        # ----------------------------------------------------
        # Ссылка на оплату
        # ----------------------------------------------------

        payment_url = (
            result.get("payment_url")
            or result.get("url")
        )

        if not payment_url:

            await callback.message.answer(
                f"""
❌ Cashera не вернула ссылку на оплату.

Ответ Cashera:

{result}
"""
            )

            await callback.answer()
            return

        # ----------------------------------------------------
        # Сохраняем платёж в нашу БД
        # ----------------------------------------------------

        add_payment(
            user_id=user_id,
            photo="",
            days=days
        )

        save_payment_id(
            user_id=user_id,
            payment_id=str(payment_uuid)
        )

        print(
            f"💾 PAYMENT SAVED: "
            f"user={user_id}, "
            f"payment={payment_uuid}, "
            f"days={days}, "
            f"amount={amount}"
        )

        # ----------------------------------------------------
        # Отправляем пользователю ссылку
        # ----------------------------------------------------

        await callback.message.answer(
            f"""
☂️ ixxy VPN

💳 Оплата через СБП

📅 Срок: {days} дней

💰 Цена: {amount} ₽

🔗 Оплатить:

{payment_url}

После успешной оплаты подписка
активируется автоматически.

⚠️ Не закрывайте страницу оплаты,
пока платёж не будет завершён.
"""
        )

    except Exception as e:

        print(
            "❌ SBP ERROR:",
            repr(e)
        )

        await callback.message.answer(
            f"""
❌ Ошибка создания платежа.

Попробуйте ещё раз немного позже.
"""
        )

    await callback.answer()