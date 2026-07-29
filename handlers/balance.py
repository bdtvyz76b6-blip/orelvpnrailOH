from aiogram import Router, F
from aiogram.types import Message

from database import get_balance


router = Router()


@router.message(F.text == "💰 Баланс")
async def balance(message: Message):

    money = get_balance(message.from_user.id)

    await message.answer(
        f"💰 Ваш баланс: {money} ₽\n\n"
        "Пополнить баланс можно в разделе покупки подписки."
    )