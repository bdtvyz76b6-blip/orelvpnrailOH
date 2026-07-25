from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    Message
)

from database import (
    activate_subscription,
    add_stars_payment
)

from github_update import create_subscription


router = Router()



# =====================
# ТАРИФЫ
# =====================

PLANS = {

    "stars_30": {
        "days": 30,
        "stars": 70
    },

    "stars_90": {
        "days": 90,
        "stars": 190
    },

    "stars_180": {
        "days": 180,
        "stars": 350
    },

    "stars_365": {
        "days": 365,
        "stars": 700
    }

}





# =====================
# СОЗДАНИЕ СЧЁТА
# =====================

@router.callback_query(
    F.data.startswith("stars_")
)
async def stars_buy(
    callback: CallbackQuery
):

    plan = PLANS.get(
        callback.data
    )


    if not plan:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    await callback.message.answer_invoice(
        
        title="🦅 Орёл VPN VIP",

        description=
        f"Подписка на {plan['days']} дней",

        payload=
        f"vpn_{callback.from_user.id}_{plan['days']}",

        currency="XTR",

        prices=[

            LabeledPrice(
                label="Telegram Stars",
                amount=plan["stars"]
            )

        ]

    )


    await callback.answer()





# =====================
# ПРОВЕРКА ПЕРЕД ОПЛАТОЙ
# =====================

@router.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery
):

    await query.answer(
        ok=True
    )





# =====================
# УСПЕШНАЯ ОПЛАТА
# =====================

@router.message(
    F.successful_payment
)
async def successful_payment(
    message: Message
):

    payment = message.successful_payment


    payload = payment.invoice_payload


    parts = payload.split("_")


    user_id = int(
        parts[1]
    )


    days = int(
        parts[2]
    )



    # создаём ссылку подписки

    link = create_subscription(
        user_id,
        days
    )



    activate_subscription(
        user_id,
        link,
        days
    )



    add_stars_payment(
        user_id,
        payment.total_amount,
        days,
        payment.telegram_payment_charge_id
    )



    await message.answer(
f"""
🎉 Оплата получена!


🦅 Орёл VPN VIP активирован


⏳ Срок:
{days} дней


🔗 Ваша подписка:

{link}
"""
    )