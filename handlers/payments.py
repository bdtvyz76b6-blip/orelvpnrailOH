from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery
)

from database import (
    add_payment,
    get_payment,
    activate_subscription
)

from github_update import (
    create_subscription
)

from keyboards import approve_keyboard

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER
)


router = Router()



# =====================
# ТАРИФЫ
# =====================

PLANS = {

    "30": {
        "days": 30,
        "stars": 70,
        "rub": 70
    },

    "90": {
        "days": 90,
        "stars": 190,
        "rub": 190
    },

    "180": {
        "days": 180,
        "stars": 350,
        "rub": 350
    },

    "365": {
        "days": 365,
        "stars": 700,
        "rub": 700
    }

}





# =====================
# STARS ПОКУПКА
# =====================

@router.callback_query(
    F.data.startswith("stars_")
)
async def stars_buy(
    callback: CallbackQuery
):

    days_key = callback.data.replace(
        "stars_",
        ""
    )


    plan = PLANS.get(
        days_key
    )


    if not plan:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    await callback.message.answer_invoice(

        title="🦅 Орёл VPN",

        description=f"🎫 Подписка на {plan['days']} дней",

        payload=f"vpn_{days_key}_{callback.from_user.id}",

        currency="XTR",

        prices=[

            LabeledPrice(
                label=f"{plan['days']} дней",
                amount=plan["stars"]
            )

        ]

    )


    await callback.answer()





# =====================
# ПРОВЕРКА ОПЛАТЫ
# =====================

@router.pre_checkout_query()
async def pre_checkout(
    query: PreCheckoutQuery
):

    await query.answer(
        ok=True
    )





# =====================
# УСПЕШНАЯ STARS ОПЛАТА
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


    days_key = parts[1]


    user_id = int(
        parts[2]
    )


    plan = PLANS.get(
        days_key
    )


    if not plan:

        return



    days = plan["days"]



    link = create_subscription(
        user_id,
        days
    )



    activate_subscription(
        user_id,
        link,
        days
    )



    add_payment(
        user_id,
        payment.total_amount,
        days,
        payment.telegram_payment_charge_id
    )



    await message.answer(
f"""
🎉 Оплата получена!


🎫 Орёл VPN активирован


📅 Срок:
{days} дней


🔗 Ваша подписка:

{link}
"""
    )





# =====================
# ПЕРЕВОД
# =====================

@router.callback_query(
    F.data.startswith("transfer_")
)
async def transfer_buy(
    callback: CallbackQuery
):

    days_key = callback.data.replace(
        "transfer_",
        ""
    )


    plan = PLANS.get(
        days_key
    )


    if not plan:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    await callback.message.answer(
f"""
💳 Оплата переводом


🎫 Срок:
{plan['days']} дней


💰 Сумма:
{plan['rub']}₽


💳 Карта:
{CARD_NUMBER}


👤 Получатель:
{CARD_OWNER}


После оплаты отправьте скриншот.
"""
    )


    await callback.answer()





# =====================
# ЧЕК
# =====================

@router.message(
    F.photo
)
async def payment_photo(
    message: Message
):

    photo = message.photo[-1].file_id



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
💳 Новый платёж


👤 Пользователь:
{message.from_user.full_name}


🆔 ID:
{message.from_user.id}


👤 Username:
@{message.from_user.username}


Подтвердите выдачу вручную.
""",

        reply_markup=approve_keyboard(
            message.from_user.id,
            30
        )

    )