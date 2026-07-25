from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER
)

from database import (
    add_payment,
    activate_subscription,
    set_pending_days,
    get_payment_days
)

from github_update import create_subscription
from keyboards import approve_keyboard


router = Router()



# =====================
# ВЫБОР ТАРИФА
# =====================

@router.callback_query(F.data.startswith("buy_"))
async def buy(callback: CallbackQuery):

    days_map = {
        "buy_7": 7,
        "buy_30": 30,
        "buy_90": 90,
        "buy_365": 365
    }


    prices = {
        7: "35₽",
        30: "85₽",
        90: "245₽",
        365: "605₽"
    }


    if callback.data not in days_map:

        await callback.answer(
            "❌ Ошибка тарифа"
        )

        return


    days = days_map[callback.data]


    set_pending_days(
        callback.from_user.id,
        days
    )


    print(
        "SAVED DAYS:",
        days
    )


    await callback.message.answer(
        f"""
💳 Оплата

📅 Срок:
{days} дней

💰 Стоимость:
{prices[days]}


💳 Карта:
{CARD_NUMBER}


👤 Получатель:
{CARD_OWNER}


После оплаты отправьте сюда скриншот.
"""
    )


    await callback.answer()



# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(message: Message):

    photo = message.photo[-1].file_id


    days = get_payment_days(
        message.from_user.id
    )


    add_payment(
        message.from_user.id,
        photo,
        days
    )


    await message.answer(
        "✅ Скриншот отправлен администратору.\n\n"
        "Ожидайте проверки."
    )


    await message.bot.send_photo(
        ADMIN_ID,
        photo,
        caption=f"""
💳 Новый чек


👤 Пользователь:
{message.from_user.full_name}


🆔 ID:
{message.from_user.id}


👤 Username:
@{message.from_user.username}


📅 Срок:
{days} дней
""",
        reply_markup=approve_keyboard(
            message.from_user.id
        )
    )



# =====================
# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# =====================

@router.callback_query(F.data.startswith("approve_"))
async def approve(callback: CallbackQuery):

    user_id = int(
        callback.data.split("_")[1]
    )


    days = get_payment_days(
        user_id
    )


    print(
        "APPROVE USER:",
        user_id
    )

    print(
        "DAYS:",
        days
    )


    link = create_subscription(
        user_id,
        days=days
    )


    activate_subscription(
        user_id,
        link,
        days
    )


    await callback.bot.send_message(
        user_id,
        f"""
🎉 Оплата подтверждена!


🦅 Орёл VPN активирован


📅 Срок:
{days} дней


🔗 Ваша подписка:

{link}
"""
    )


    await callback.message.edit_caption(
        caption="✅ Подписка выдана"
    )


    await callback.answer(
        "Готово"
    )



# =====================
# ОТКЛОНЕНИЕ
# =====================

@router.callback_query(F.data.startswith("reject_"))
async def reject(callback: CallbackQuery):

    user_id = int(
        callback.data.split("_")[1]
    )


    await callback.bot.send_message(
        user_id,
        """
❌ Оплата отклонена.

Если произошла ошибка —
обратитесь в поддержку.
"""
    )


    await callback.message.edit_caption(
        caption="❌ Чек отклонён"
    )


    await callback.answer()