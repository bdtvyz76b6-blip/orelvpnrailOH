from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment

from database import (
    create_payment,
)

router = Router()


# ============================================================
# ТАРИФЫ СБП
# ============================================================

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

    # ========================================================
    # ПРОВЕРКА ТАРИФА
    # ========================================================

    if code not in PAYMENTS:

        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True,
        )

        return

    plan = PAYMENTS[code]

    amount = plan["amount"]
    days = plan["days"]

    user_id = callback.from_user.id

    try:

        # ====================================================
        # СОЗДАЁМ ПЛАТЁЖ В CASHERA
        # ====================================================

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days,
        )

        print(
            "💳 CASHERA PAYMENT RESULT:"
        )

        print(
            result
        )

        # ====================================================
        # ПРОВЕРКА ОТВЕТА
        # ====================================================

        if not isinstance(
            result,
            dict,
        ):

            await callback.message.answer(
                "❌ CasheRa вернула некорректный ответ."
            )

            await callback.answer()

            return

        # ====================================================
        # UUID ПЛАТЕЖА
        # ====================================================

        payment_uuid = (
            result.get("uuid")
            or result.get("id")
        )

        if not payment_uuid:

            await callback.message.answer(
                f"""
❌ <b>CasheRa не вернула ID платежа.</b>

Ответ CasheRa:

<code>{result}</code>
""",
                parse_mode="HTML",
            )

            await callback.answer()

            return

        payment_uuid = str(
            payment_uuid
        )

        # ====================================================
        # ССЫЛКА НА ОПЛАТУ
        # ====================================================

        payment_url = (
            result.get("payment_url")
            or result.get("url")
        )

        if not payment_url:

            await callback.message.answer(
                f"""
❌ <b>CasheRa не вернула ссылку на оплату.</b>

ID платежа:

<code>{payment_uuid}</code>
""",
                parse_mode="HTML",
            )

            await callback.answer()

            return

        payment_url = str(
            payment_url
        )

        # ====================================================
        # СОХРАНЯЕМ ПЛАТЁЖ В POSTGRESQL
        # ====================================================

        saved = create_payment(
            user_id=user_id,
            payment_id=payment_uuid,
            amount=amount * 100,
            days=days,
            provider="cashera",
        )

        if not saved:

            print(
                "⚠️ Платёж уже существует:"
            )

            print(
                payment_uuid
            )

        else:

            print(
                "💾 CASHERA PAYMENT SAVED"
            )

            print(
                f"user={user_id}"
            )

            print(
                f"payment={payment_uuid}"
            )

            print(
                f"amount={amount * 100}"
            )

            print(
                f"days={days}"
            )

        # ====================================================
        # ОТПРАВЛЯЕМ ССЫЛКУ ПОЛЬЗОВАТЕЛЮ
        # ====================================================

        await callback.message.answer(
            f"""
☂️ <b>ixxy VPN</b>

💳 <b>Оплата через СБП</b>

📅 Срок:
<b>{days} дней</b>

💰 Цена:
<b>{amount} ₽</b>

🔗 <b>Ссылка на оплату:</b>

{payment_url}

После успешной оплаты подписка
активируется автоматически.

⚠️ После оплаты не нужно нажимать
ничего дополнительно.

Дождитесь уведомления от бота.
""",
            parse_mode="HTML",
        )

        print(
            "✅ Ссылка на оплату отправлена"
        )

    # ========================================================
    # ОШИБКА
    # ========================================================

    except Exception as e:

        print(
            "❌ SBP ERROR:"
        )

        print(
            f"{type(e).__name__}: {e}"
        )

        try:

            await callback.message.answer(
                """
❌ <b>Не удалось создать платёж.</b>

Попробуйте ещё раз немного позже.
""",
                parse_mode="HTML",
            )

        except Exception as send_error:

            print(
                "❌ Ошибка отправки сообщения:"
            )

            print(
                send_error
            )

    # ========================================================
    # CALLBACK
    # ========================================================

    try:

        await callback.answer()

    except Exception:

        pass