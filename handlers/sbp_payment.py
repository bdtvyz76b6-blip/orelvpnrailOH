from aiogram import Router, F
from aiogram.types import CallbackQuery

from cashera_api import create_cashera_payment


router = Router()


# =====================
# СБП 1 МЕСЯЦ
# =====================

@router.callback_query(
    F.data == "sbp_30"
)
async def sbp_30(callback: CallbackQuery):

    payment = create_cashera_payment(
        user_id=callback.from_user.id,
        amount=99,
        days=30
    )

    link = payment.get(
        "payment_url"
    )


    await callback.message.answer(
f"""
🦅 Орёл VPN

💳 Оплата СБП

📅 Срок:
30 дней

💰 Цена:
99₽


🔗 Ссылка на оплату:

{link}
"""
    )

    await callback.answer()



# =====================
# СБП 3 МЕСЯЦА
# =====================

@router.callback_query(
    F.data == "sbp_90"
)
async def sbp_90(callback: CallbackQuery):

    payment = create_cashera_payment(
        user_id=callback.from_user.id,
        amount=249,
        days=90
    )

    link = payment.get(
        "payment_url"
    )


    await callback.message.answer(
f"""
🦅 Орёл VPN

💳 Оплата СБП

📅 Срок:
90 дней

💰 Цена:
249₽


🔗 Ссылка:

{link}
"""
    )

    await callback.answer()



# =====================
# СБП 6 МЕСЯЦЕВ
# =====================

@router.callback_query(
    F.data == "sbp_180"
)
async def sbp_180(callback: CallbackQuery):

    payment = create_cashera_payment(
        user_id=callback.from_user.id,
        amount=599,
        days=180
    )

    link = payment.get(
        "payment_url"
    )


    await callback.message.answer(
f"""
🦅 Орёл VPN

💳 Оплата СБП

📅 Срок:
180 дней

💰 Цена:
599₽


🔗 Ссылка:

{link}
"""
    )

    await callback.answer()



# =====================
# СБП 12 МЕСЯЦЕВ
# =====================

@router.callback_query(
    F.data == "sbp_365"
)
async def sbp_365(callback: CallbackQuery):

    payment = create_cashera_payment(
        user_id=callback.from_user.id,
        amount=999,
        days=365
    )

    link = payment.get(
        "payment_url"
    )


    await callback.message.answer(
f"""
🦅 Орёл VPN

💳 Оплата СБП

📅 Срок:
365 дней

💰 Цена:
999₽


🔗 Ссылка:

{link}
"""
    )

    await callback.answer()