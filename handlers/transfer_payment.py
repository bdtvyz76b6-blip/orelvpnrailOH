from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import (
    CARD_NUMBER,
    CARD_OWNER,
    PRICE_30,
    PRICE_90,
    PRICE_180,
    PRICE_365
)

from database import set_pending_days


router = Router()



@router.callback_query(
    F.data.startswith("transfer_")
)
async def transfer_buy(
    callback: CallbackQuery
):

    data = callback.data


    prices = {

        "transfer_30": (30, PRICE_30),

        "transfer_90": (90, PRICE_90),

        "transfer_180": (180, PRICE_180),

        "transfer_365": (365, PRICE_365)

    }



    if data not in prices:

        await callback.answer(
            "Ошибка"
        )

        return



    days, price = prices[data]



    set_pending_days(
        callback.from_user.id,
        days
    )



    await callback.message.answer(
f"""
💳 Оплата Орёл VPN


📅 Срок:
{days} дней


💰 Цена:
{price}


💳 Карта:
{CARD_NUMBER}


👤 Получатель:
{CARD_OWNER}


После оплаты отправьте скриншот сюда.
"""
    )


    await callback.answer()