from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery
)

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER
)

from database import (
    add_payment,
    get_payment,
    activate_subscription,
    set_pending_days,
    get_pending_days
)

from github_update import create_subscription

from keyboards import (
    approve_keyboard
)


router = Router()



# =====================
# STARS ТАРИФЫ
# =====================

STARS_PRICES = {

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
# СОЗДАНИЕ STARS СЧЁТА
# =====================

@router.callback_query(
    F.data.startswith("stars_")
)
async def stars_buy(
    callback: CallbackQuery
):

    tariff = STARS_PRICES.get(
        callback.data
    )


    if not tariff:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    await callback.bot.send_invoice(

        chat_id=callback.from_user.id,

        title="🦅 Орёл VPN VIP",

        description=f"Подписка на {tariff['days']} дней",

        payload=f"vpn_{tariff['days']}",

        currency="XTR",

        prices=[

            LabeledPrice(

                label="Telegram Stars",

                amount=tariff["stars"]

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
# УСПЕШНАЯ ОПЛАТА STARS
# =====================

@router.message(
    F.successful_payment
)
async def successful_payment(
    message: Message
):

    payment = message.successful_payment


    days = int(
        payment.invoice_payload.split("_")[1]
    )


    user_id = message.from_user.id



    link = create_subscription(
        user_id,
        days
    )


    activate_subscription(
        user_id,
        link,
        days
    )



    await message.answer(
f"""
🎉 Оплата получена!


🦅 Орёл VPN VIP активирован


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
    F.data == "pay_transfer"
)
async def transfer(
    callback: CallbackQuery
):

    await callback.message.answer(
f"""
💳 Оплата переводом


💰 Карта:
{CARD_NUMBER}


👤 Получатель:
{CARD_OWNER}


После оплаты отправьте скриншот.
"""
    )


    await callback.answer()





# =====================
# ВЫБОР ПЕРЕВОДА
# =====================

@router.callback_query(
    F.data.startswith("transfer_")
)
async def transfer_tariff(
    callback: CallbackQuery
):

    days = int(
        callback.data.split("_")[1]
    )


    set_pending_days(
        callback.from_user.id,
        days
    )


    await callback.message.answer(
f"""
💳 Перевод


📅 Срок:
{days} дней


Отправьте чек после оплаты.
"""
    )


    await callback.answer()





# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(
    F.photo
)
async def get_check(
    message: Message
):

    photo = message.photo[-1].file_id


    days = get_pending_days(
        message.from_user.id
    )


    payment_id = add_payment(
        message.from_user.id,
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
💳 Новый платёж


👤 Пользователь:
{message.from_user.full_name}


🆔 ID:
{message.from_user.id}


📅 Срок:
{days} дней


🧾 Заявка:
#{payment_id}
""",

        reply_markup=approve_keyboard(
            message.from_user.id,
            payment_id
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

    payment_id = int(data[2])



    payment = get_payment(
        payment_id
    )


    if not payment:

        await callback.answer(
            "Платёж не найден"
        )

        return



    days = payment[1]



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
🎉 Оплата подтверждена!


🦅 Орёл VPN VIP


📅 Срок:
{days} дней


🔗 Ссылка:

{link}
"""

    )


    await callback.answer(
        "Выдано"
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


    await callback.answer(
        "Отклонено"
    )