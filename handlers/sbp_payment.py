from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment

from database import (
    add_payment,
    save_payment_id,
)


router = Router()


# ============================================================
# СБП ТАРИФЫ
# ============================================================

PAYMENTS = {
    "sbp_30": {
        "amount": 1,
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
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ
# ============================================================

def find_value(data, *keys):
    """
    Ищет значение по ключам даже если Cashera
    завернула ответ внутрь transaction/data/result.
    """

    if not isinstance(data, dict):
        return None

    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value

    for key in ("transaction", "data", "result"):
        nested = data.get(key)

        if isinstance(nested, dict):
            value = find_value(nested, *keys)

            if value not in (None, ""):
                return value

    return None


# ============================================================
# СОЗДАНИЕ СБП ПЛАТЕЖА
# ============================================================

@router.callback_query(
    F.data.startswith("sbp_")
)
async def sbp_payment(
    callback: CallbackQuery
):

    code = callback.data

    plan = PAYMENTS.get(code)

    if not plan:
        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True
        )
        return

    amount = plan["amount"]
    days = plan["days"]
    user_id = callback.from_user.id

    try:

        # ----------------------------------------------------
        # СОЗДАЁМ ПЛАТЁЖ В CASHERA
        # ----------------------------------------------------

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days
        )

        print("💳 CASHERA PAYMENT RESULT:")
        print(result)

        if not isinstance(result, dict):
            raise RuntimeError(
                "Cashera вернула некорректный ответ"
            )

        # ----------------------------------------------------
        # UUID
        # ----------------------------------------------------

        payment_uuid = find_value(
            result,
            "uuid",
            "id",
            "transaction_id"
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

        payment_uuid = str(payment_uuid)

        print(
            f"🆔 CASHERA UUID: {payment_uuid}"
        )

        # ----------------------------------------------------
        # ССЫЛКА НА ОПЛАТУ
        # ----------------------------------------------------

        payment_url = find_value(
            result,
            "payment_url",
            "url",
            "pay_url",
            "payment_link"
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

        payment_url = str(payment_url)

        print(
            f"🔗 CASHERA URL: {payment_url}"
        )

        # ----------------------------------------------------
        # СОХРАНЯЕМ ПЛАТЁЖ
        # ----------------------------------------------------

        add_payment(
            user_id=user_id,
            photo="",
            days=days
        )

        # Привязываем UUID Cashera к созданному платежу
        save_payment_id(
            user_id=user_id,
            payment_id=payment_uuid
        )

        print(
            f"💾 Платёж сохранён: "
            f"user={user_id}, "
            f"uuid={payment_uuid}, "
            f"days={days}"
        )

        # ----------------------------------------------------
        # ОТПРАВЛЯЕМ ПОЛЬЗОВАТЕЛЮ
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
выдастся автоматически.

⚠️ Не закрывайте оплату до завершения платежа.
"""
        )

    except Exception as e:

        print(
            f"❌ SBP ERROR: {type(e).__name__}: {e}"
        )

        await callback.message.answer(
            f"""
❌ Не удалось создать платёж.

Попробуйте ещё раз немного позже.
"""
        )

    await callback.answer()