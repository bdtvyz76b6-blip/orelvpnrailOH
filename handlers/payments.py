from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery
)


from database import (
    add_payment,
    activate_subscription,
    get_payment
)


from github_update import (
    create_subscription
)


from keyboards import (
    approve_keyboard
)


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
# STARS
# =====================

@router.callback_query(
    F.data.startswith("stars_")
)
async def stars_buy(
    callback: CallbackQuery
):

    key = callback.data.replace(
        "stars_",
        ""
    )


    plan = PLANS.get(key)


    if not plan:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    await callback.message.answer_invoice(

        title="☂️ ixxy vpn",

        description=f"🎫 Подписка {plan['days']} дней",

        payload=f"vpn_{key}_{callback.from_user.id}",

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
# PRE CHECKOUT
# =====================

@router.pre_checkout_query()
async def checkout(
    query: PreCheckoutQuery
):

    await query.answer(
        ok=True
    )





# =====================
# УСПЕШНЫЕ STARS
# =====================

@router.message(
    F.successful_payment
)
async def stars_success(
    message: Message
):


    payment = message.successful_payment


    payload = payment.invoice_payload


    data = payload.split("_")


    days_key = data[1]


    user_id = int(
        data[2]
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


☂️ ixxy vip активирован


🎫 Срок:
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

    key = callback.data.replace(
        "transfer_",
        ""
    )


    plan = PLANS.get(key)


    if not plan:

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
async def get_check(
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


Выберите действие:
""",

        reply_markup=approve_keyboard(
            message.from_user.id,
            30
        )

    )





# =====================
# ВЫДАТЬ ПОДПИСКУ
# =====================

@router.callback_query(
    F.data.startswith("approve_")
)
async def approve(
    callback: CallbackQuery
):

    data = callback.data.split("_")


    user_id = int(data[1])


    days = int(data[2])



    link = create_subscription(
        user_id,
        days
    )



    activate_subscription(
        user_id,
        link,
        days
    )



    await callback.bot.send_message(

        user_id,

f"""
🎉 Подписка активирована!


🦅 Орёл VPN


🎫 Срок:
{days} дней


🔗 Ваша ссылка:

{link}
"""

    )



    await callback.message.edit_caption(

        caption=f"""
✅ Подписка выдана


🎫 Срок:
{days} дней
"""

    )


    await callback.answer(
        "Готово"
    )





# =====================
# ОТКЛОНИТЬ
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

Обратитесь в поддержку.
"""

    )


    await callback.message.edit_caption(

        caption="❌ Платёж отклонён"

    )


    await callback.answer()