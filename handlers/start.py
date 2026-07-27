from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from datetime import datetime

from config import SUPPORT

from database import (
    add_user,
    get_user,
    get_subscription_link,
    save_subscription_link,
    check_trial,
    activate_trial,
    has_accepted_terms,
    accept_terms
)

from keyboards import (
    main_menu,
    payment_method_keyboard,
    stars_buy_keyboard,
    transfer_buy_keyboard,
    accept_terms_keyboard
)

from github_update import (
    create_subscription,
    create_user_subscription
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


    # =====================
    # ПРОВЕРКА УСЛОВИЙ
    # =====================

    if not has_accepted_terms(user_id):

        await message.answer(
"""
🦅 Орёл VPN


Перед использованием сервиса необходимо ознакомиться с документами.


После ознакомления нажмите кнопку:
✅ Принимаю
""",
            reply_markup=accept_terms_keyboard()
        )

        return



    link = get_subscription_link(user_id)


    # если файла ещё нет
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


📲 Добавьте ссылку в приложение Happ.
""",
        reply_markup=main_menu()
    )



# =====================
# ПРИНЯТИЕ УСЛОВИЙ
# =====================

@router.callback_query(
    F.data == "accept_terms"
)
async def accept(callback: CallbackQuery):

    accept_terms(
        callback.from_user.id
    )


    await callback.message.delete()


    await callback.message.answer(
"""
✅ Условия приняты!


Добро пожаловать в Орёл VPN 🦅
""",
        reply_markup=main_menu()
    )


    await callback.answer()



# =====================
# КУПИТЬ
# =====================

@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy(message: Message):

    await message.answer(
"""
🦅 Орёл VPN

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
async def stars(callback: CallbackQuery):

    await callback.message.answer(
"""
⭐ Оплата Telegram Stars


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
async def transfer(callback: CallbackQuery):

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


📲 Добавьте её в Happ.
"""
    )



# =====================
# ДОКУМЕНТЫ
# =====================

@router.message(
    F.text == "📄 Документы"
)
async def documents(message: Message):

    await message.answer(
"""
📄 Документы Орёл VPN:


Все документы находятся на сайте:

https://bdtvyz76b6-blip.github.io/managerorlvpnsite/
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