from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER,
    PRICE_BS,
    BS_LINK,
    PAID_TARIFF
)

from database import activate_bs

from keyboards import (
    buy_keyboard,
    approve_keyboard
)


router = Router()


# =========================
# Кнопка покупки
# =========================

@router.callback_query(F.data == "buy_bs")
async def buy_bs(callback: CallbackQuery):

    await callback.message.answer(
        "👑 Обход Б/С\n\n"
        f"Стоимость: {PRICE_BS}\n\n"
        "Перевод:\n"
        f"💳 {CARD_NUMBER}\n\n"
        f"Получатель: {CARD_OWNER}\n\n"
        "После оплаты нажмите кнопку:\n"
        "✅ Я оплатил"
    )

    await callback.message.answer(
        "После оплаты:",
        reply_markup=payment_done_keyboard()
    )


# =========================
# Кнопка Я оплатил
# =========================

@router.callback_query(F.data == "paid")
async def paid(callback: CallbackQuery):

    await callback.message.answer(
        "📎 Отправьте чек оплаты сюда."
    )


    await callback.answer()



# =========================
# Получение чека
# =========================

@router.message(F.photo)