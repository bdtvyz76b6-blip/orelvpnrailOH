from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command


from config import SUPPORT


from database import (
    add_user,
    get_subscription_link,
    check_trial,
    activate_trial
)


from keyboards import (
    main_menu,
    stars_buy_keyboard
)


from github_update import (
    create_subscription
)



router = Router()





# =====================
# START
# =====================

@router.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id


    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )



    link = get_subscription_link(
        user_id
    )



    await message.answer(
f"""
🦅 Добро пожаловать в Орёл VPN!


🎫 Ваша подписка:

{"Активна" if link else "Нет активной подписки"}


Выберите действие ниже.
""",
        reply_markup=main_menu()
    )





# =====================
# КУПИТЬ ПОДПИСКУ
# =====================

@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy_subscription(message: Message):


    await message.answer(
"""
🦅 Орёл VPN VIP


Выберите срок подписки:

⭐ Оплата через Telegram Stars
""",
        reply_markup=stars_buy_keyboard()
    )





# =====================
# ПРОБНЫЙ ПЕРИОД
# =====================

@router.message(
    F.text == "🎁 Пробный период"
)
async def trial(message: Message):

    user_id = message.from_user.id



    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )



    if check_trial(user_id):

        await message.answer(
            "❌ Вы уже использовали пробный период."
        )

        return



    link = create_subscription(
        user_id,
        days=3
    )



    activate_trial(
        user_id,
        link
    )



    await message.answer(
f"""
🎁 Пробный период активирован!


⏳ Срок:
3 дня


🔗 Ваша ссылка:

{link}
"""
    )





# =====================
# ПОДДЕРЖКА
# =====================

@router.message(
    F.text == "💬 Поддержка"
)
async def support(message: Message):

    await message.answer(
f"""
💬 Поддержка:

{SUPPORT}
"""
    )