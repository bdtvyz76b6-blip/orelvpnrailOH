from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from datetime import datetime

from database import (
    add_user,
    get_user,
    get_subscription_link,
    save_subscription_link,
    check_trial,
    activate_trial
)

from keyboards import (
    main_menu,
    payment_method_keyboard,
    stars_buy_keyboard,
    transfer_buy_keyboard
)

from github_update import (
    create_user_subscription,
    activate_user_subscription
)


router = Router()



# =====================
# START
# =====================

@router.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id


    # создаём пользователя

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )



    # получаем ссылку

    link = get_subscription_link(
        user_id
    )


    # если ссылки нет — создаём GitHub файл

    if not link:

        link = create_user_subscription(
            user_id
        )


        save_subscription_link(
            user_id,
            link
        )



    user = get_user(
        user_id
    )



    status = "❌ Не активна"



    if user:

        subscription = user[3]

        until = user[4]


        if subscription in (
            "vip",
            "trial"
        ) and until:


            try:

                date = datetime.strptime(
                    until,
                    "%Y-%m-%d"
                )


                if date >= datetime.now():

                    status = "✅ Активна"


                else:

                    status = "⛔ Истекла"



            except:

                status = "❌ Не активна"



    await message.answer(

f"""
🦅 Добро пожаловать в Орёл VPN!


🎫 Ваша подписка:

{status}


🔗 Ваша ссылка:

{link}


📲 Добавьте её в Happ.


Выберите действие ниже.
""",

        reply_markup=main_menu()

    )





# =====================
# КУПИТЬ
# =====================


@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy_subscription(
        message: Message
):

    await message.answer(

"""
🦅 Орёл VPN VIP


Выберите способ оплаты:
""",

        reply_markup=payment_method_keyboard()

    )





# =====================
# STARS
# =====================


@router.callback_query(
    F.data == "pay_stars"
)
async def pay_stars(
        callback: CallbackQuery
):

    await callback.message.answer(

"""
⭐ Telegram Stars


Выберите срок:
""",

        reply_markup=stars_buy_keyboard()

    )


    await callback.answer()





# =====================
# ПЕРЕВОД
# =====================


@router.callback_query(
    F.data == "pay_transfer"
)
async def pay_transfer(
        callback: CallbackQuery
):

    await callback.message.answer(

"""
💳 Оплата переводом


Выберите срок:
""",

        reply_markup=transfer_buy_keyboard()

    )


    await callback.answer()





# =====================
# ПРОБНЫЙ ПЕРИОД
# =====================


@router.message(
    F.text == "🎁 Пробный период"
)
async def trial(
        message: Message
):

    user_id = message.from_user.id


    if check_trial(user_id):

        await message.answer(
            "❌ Пробный период уже использован."
        )

        return



    link = activate_user_subscription(
        user_id,
        days=3
    )



    activate_trial(
        user_id,
        link
    )



    save_subscription_link(
        user_id,
        link
    )



    await message.answer(

f"""
🎁 Пробный период активирован!


⏳ Срок:
3 дня


🔗 Ваша подписка:

{link}
"""

    )





# =====================
# ДОКУМЕНТЫ
# =====================


@router.message(
    F.text == "📄 Документы"
)
async def documents(
        message: Message
):

    await message.answer(
"""
📄 Документы:

https://bdtvyz76b6-blip.github.io/managerorlvpnsite/
"""
    )





# =====================
# ПОДДЕРЖКА
# =====================


@router.message(
    F.text == "💬 Поддержка"
)
async def support(
        message: Message
):

    from config import SUPPORT


    await message.answer(

f"""
💬 Поддержка:

{SUPPORT}
"""

    )