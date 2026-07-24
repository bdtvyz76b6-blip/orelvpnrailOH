from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID

from database import (
    add_payment,
    activate_bs,
    set_subscription_date
)

from github_update import create_subscription

from keyboards import payment_menu

from datetime import datetime, timedelta


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


    # Создаём или обновляем файл GitHub
    link = create_subscription(
        user_id
    )


    # Ставим 30 дней
    expire_date = (
        datetime.now()
        + timedelta(days=30)
    ).strftime(
        "%Y-%m-%d"
    )


    # Сохраняем в БД
    activate_bs(
        user_id,
        link
    )


    set_subscription_date(
        user_id,
        expire_date
    )


    await callback.bot.send_message(

        user_id,

        "🎉 Оплата подтверждена!\n\n"
        "🦅 Orel VPN активирован.\n\n"
        f"📅 Действует до: {expire_date}\n\n"
        "🔗 Ваша подписка:\n"
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