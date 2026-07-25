from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import SUPPORT

from database import (
    add_user,
    get_user,
    activate_trial,
    check_trial,
    get_subscription_link
)

from keyboards import (
    main_menu,
    buy_keyboard
)

from github_update import (
    create_user_subscription,
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
        message.from_user.username
    )


    # берём ссылку из базы
    link = get_subscription_link(
        user_id
    )


    # если ссылки нет - создаём файл GitHub
    if not link:

        link = create_user_subscription(
            user_id
        )


    await message.answer(
        f"""
🦅 Добро пожаловать в Орёл VPN!


🔗 Ваша ссылка на подписку:

{link}


📲 Добавьте её в приложение Happ.


🎁 Пробный период доступен в меню.
""",
        reply_markup=main_menu()
    )





# =====================
# КУПИТЬ ПОДПИСКУ
# =====================

@router.message(
    F.text == "👑 Купить подписку"
)
async def buy(message: Message):

    await message.answer(
        """
🦅 Орёл VPN

Выберите срок подписки:
""",
        reply_markup=buy_keyboard()
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
        message.from_user.username
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


🔗 Ваша подписка:

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
        f"💬 Поддержка:\n\n{SUPPORT}"
    )