from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_payments

router = Router()


@router.callback_query(F.data == "admin_payments")
async def admin_payments(call: CallbackQuery):

    payments = get_payments()

    if not payments:
        await call.message.edit_text(
            "💳 Платежей пока нет"
        )
        return


    buttons = []

    for payment in payments[:20]:

        payment_id = payment[0]
        user_id = payment[1]
        days = payment[2]

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"💳 #{payment_id} | {user_id} | {days} дней",
                    callback_data=f"payment_info_{payment_id}"
                )
            ]
        )


    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_back"
            )
        ]
    )


    await call.message.edit_text(
        "💳 История платежей СБП:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(F.data.startswith("payment_info_"))
async def payment_info(call: CallbackQuery):

    payment_id = int(
        call.data.replace("payment_info_", "")
    )


    await call.message.edit_text(
        f"💳 Платёж #{payment_id}\n\n"
        "✅ Оплата через СБП\n"
        "🤖 Статус: Автоматически подтверждён\n\n"
        "Подписка выдана автоматически."
    )