from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from database import extend_subscription, get_user


router = Router()



# =====================
# ВЫБОР СРОКА ПРОДЛЕНИЯ
# =====================

@router.callback_query(
    F.data.startswith("extend_")
    & ~F.data.startswith("extend_days_")
)
async def choose_extend(call: CallbackQuery):

    user_id = int(
        call.data.replace(
            "extend_",
            ""
        )
    )


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="7 дней",
                    callback_data=f"extend_days_{user_id}_7"
                )
            ],
            [
                InlineKeyboardButton(
                    text="30 дней",
                    callback_data=f"extend_days_{user_id}_30"
                )
            ],
            [
                InlineKeyboardButton(
                    text="90 дней",
                    callback_data=f"extend_days_{user_id}_90"
                )
            ],
            [
                InlineKeyboardButton(
                    text="180 дней",
                    callback_data=f"extend_days_{user_id}_180"
                )
            ],
            [
                InlineKeyboardButton(
                    text="365 дней",
                    callback_data=f"extend_days_{user_id}_365"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"admin_user_{user_id}"
                )
            ]
        ]
    )


    try:

        await call.message.edit_text(
            "⏳ Выберите срок продления:",
            reply_markup=keyboard
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise


    await call.answer()





# =====================
# ПРОДЛЕНИЕ
# =====================

@router.callback_query(
    F.data.startswith("extend_days_")
)
async def extend_days(call: CallbackQuery):


    parts = call.data.split("_")


    user_id = int(
        parts[2]
    )


    days = int(
        parts[3]
    )


    extend_subscription(
        user_id,
        days
    )


    user = get_user(
        user_id
    )


    await call.message.edit_text(
        f"✅ Подписка продлена!\n\n"
        f"👤 Пользователь: @{user[1] or 'нет'}\n"
        f"⏳ Добавлено: {days} дней\n"
        f"📅 Новый срок: {user[4]}"
    )


    await call.answer()