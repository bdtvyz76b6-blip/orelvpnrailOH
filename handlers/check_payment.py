from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID

from database import (
    add_payment,
    activate_bs
)

from github_update import create_subscription

from keyboards import payment_menu


router = Router()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def get_check(message: Message):

    photo = message.photo[-1].file_id


    add_payment(
        message.from_user.id,
        photo
    )


    await message.answer(
        "✅ Чек отправлен.\n"
        "Ожидайте подтверждения."
    )


    await message.bot.send_photo(

        ADMIN_ID,

        photo,

        caption=
        f"""
💳 Новая заявка

👤 Пользователь:
{message.from_user.full_name}

🆔 ID:
{message.from_user.id}
""",

        reply_markup=payment_menu(
            message.from_user.id
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

    user_id = int(
        callback.data.split("_")[1]
    )


    # Создаём персональный файл на GitHub
    link = create_subscription(
        user_id
    )


    # Сохраняем ссылку в базе
    activate_bs(
        user_id,
        link
    )


    await callback.bot.send_message(
        user_id,

        "🎉 Оплата подтверждена!\n\n"
        "🦅 Orel VPN активирован.\n\n"
        "Ваша персональная ссылка:\n"
        f"{link}"
    )


    await callback.message.edit_caption(
        caption=
        "✅ Подписка выдана"
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

        "❌ Оплата отклонена.\n"
        "Свяжитесь с поддержкой."
    )


    await callback.message.edit_caption(
        caption=
        "❌ Заявка отклонена"
    )


    await callback.answer(
        "Отклонено"
    )