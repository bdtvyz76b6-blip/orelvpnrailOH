from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

SBP_30 = "https://payform.cashera.cash/019fa3f1-5d16-7213-ae29-edac85c38315"
SBP_90 = "https://payform.cashera.cash/019fa3f2-eb0e-72a3-8eda-8a7d7904a901"
SBP_180 = "https://payform.cashera.cash/019fa3f4-1873-73e0-8316-d2adc7c4a4b9"
SBP_365 = "https://payform.cashera.cash/019fa3f5-0ea3-7147-9ac6-74ada9e53c2a"


@router.callback_query(F.data == "pay_sbp")
async def pay_sbp(callback: CallbackQuery):

    await callback.message.answer(
"""
💳 Оплата через СБП

Выберите тариф:
""",
        reply_markup=None
    )

    await callback.message.answer(
        "1 месяц — нажмите кнопку 99 ₽\n"
        "3 месяца — нажмите кнопку 249 ₽\n"
        "6 месяцев — нажмите кнопку 599 ₽\n"
        "12 месяцев — нажмите кнопку 999 ₽"
    )

    await callback.answer()


@router.callback_query(F.data == "sbp_30")
async def sbp_30(callback: CallbackQuery):

    await callback.message.answer(
f"""
☂️ ixxy vip

📅 1 месяц

💰 Стоимость: 99 ₽

💳 Оплатить:

{SBP_30}
"""
    )

    await callback.answer()


@router.callback_query(F.data == "sbp_90")
async def sbp_90(callback: CallbackQuery):

    await callback.message.answer(
f"""
☂️ ixxy vip

📅 3 месяца

💰 Стоимость: 249 ₽

💳 Оплатить:

{SBP_90}
"""
    )

    await callback.answer()


@router.callback_query(F.data == "sbp_180")
async def sbp_180(callback: CallbackQuery):

    await callback.message.answer(
f"""
☂️ ixxy vip

📅 6 месяцев

💰 Стоимость: 599 ₽

💳 Оплатить:

{SBP_180}
"""
    )

    await callback.answer()


@router.callback_query(F.data == "sbp_365")
async def sbp_365(callback: CallbackQuery):

    await callback.message.answer(
f"""
☂️ ixxy vip

📅 12 месяцев

💰 Стоимость: 999 ₽

💳 Оплатить:

{SBP_365}
"""
    )

    await callback.answer()