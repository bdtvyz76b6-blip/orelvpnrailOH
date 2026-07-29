from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_payments

router = Router()


@router.callback_query(F.data == "admin_payments")
async def payments(call: CallbackQuery):

    payments = get_payments()

    if not payments:
        await call.message.edit_text(
            "💳 Платежей нет"
        )
        return


    buttons = []

    for pay in payments[:20]:

        payment_id = pay[0]
        user_id = pay[1]
        days = pay[3]

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"💳 {user_id} | {days} дней",
                    callback_data=f"payment_{payment_id}"
                )
            ]
        )


    await call.message.edit_text(
        "💳 Ожидают проверки:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(F.data.startswith("payment_"))
async def payment_card(call: CallbackQuery):

    payment_id = int(
        call.data.replace("payment_", "")
    )


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"approve_{payment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{payment_id}"
                )
            ]
        ]
    )


    await call.message.edit_text(
        f"💳 Платёж #{payment_id}\n\n"
        "Проверь оплату:",
        reply_markup=keyboard
    )