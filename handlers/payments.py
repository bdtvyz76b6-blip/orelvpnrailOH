from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER
)

from database import (
    add_payment,
    get_payment,
    activate_subscription,
    set_pending_days,
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


    days = days_map.get(
        callback.data
    )


    if not days:

        await callback.answer(
            "Ошибка тарифа"
        )

        return



    set_pending_days(
        callback.from_user.id,
        days
    )



    await callback.message.answer(
        f"""
💳 Оплата Орёл VPN


📅 Срок:
{days} дней


💰 Стоимость:
{prices[days]}


💳 Карта:
{CARD_NUMBER}


👤 Получатель:
{CARD_OWNER}


После оплаты отправьте скриншот.
"""
    )


    await callback.answer()





# =====================
# ПОЛУЧЕНИЕ ЧЕКА
# =====================

@router.message(F.photo)
async def payment_photo(message: Message):


    photo = message.photo[-1].file_id


    from database import get_pending_days


    days = get_pending_days(
        message.from_user.id
    )


    payment_id = add_payment(
        message.from_user.id,
        photo,
        days
    )


    await message.answer(
        """
✅ Чек отправлен.

Ожидайте проверки администратора.
"""
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


🧾 Платёж:
#{payment_id}
""",

        reply_markup=approve_keyboard(
            message.from_user.id,
            payment_id
        )

    )





# =====================
# ПОДТВЕРЖДЕНИЕ
# =====================

@router.callback_query(
    F.data.startswith("approve_")
)
async def approve(callback: CallbackQuery):


    data = callback.data.split("_")


    user_id = int(data[1])

    payment_id = int(data[2])



    payment = get_payment(
        payment_id
    )



    if not payment:

        await callback.answer(
            "Платёж не найден"
        )

        return



    days = payment[1]



    print(
        "PAYMENT APPROVED:",
        user_id,
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



    try:

        await callback.message.edit_caption(
            caption=f"✅ Подписка выдана\n\nСрок: {days} дней"
        )

    except:

        pass



    await callback.answer(
        "Готово"
    )





# =====================
# ОТКЛОНЕНИЕ
# =====================

@router.callback_query(
    F.data.startswith("reject_")
)
async def reject(callback: CallbackQuery):


    data = callback.data.split("_")


    user_id = int(data[1])


    await callback.bot.send_message(

        user_id,

        """
❌ Оплата отклонена.

Если произошла ошибка —
обратитесь в поддержку.
"""
    )



    try:

        await callback.message.edit_caption(
            caption="❌ Чек отклонён"
        )

    except:

        pass



    await callback.answer()