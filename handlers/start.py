from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import (
    BS_LINK,
    SUPPORT,
    CARD_NUMBER,
    CARD_OWNER
)

from database import (
    add_user,
    get_user,
    set_pending_days,
    activate_trial,
    check_trial
)

from keyboards import (
    main_menu,
    buy_keyboard
)


router = Router()



# =====================
# START
# =====================

@router.message(Command("start"))
async def start(message: Message):

    add_user(
        message.from_user.id,
        message.from_user.username
    )


    await message.answer(
        "🦅 Орёл VPN\n\n"
        "Выберите раздел:",
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
👑 Орёл VPN

Выберите срок подписки:
""",
        reply_markup=buy_keyboard()
    )





# =====================
# ВЫБОР ТАРИФА
# =====================

@router.callback_query(
    F.data.startswith("buy_")
)

async def choose_tariff(
    callback: CallbackQuery
):


    days = int(
        callback.data.split("_")[1]
    )


    set_pending_days(
        callback.from_user.id,
        days
    )


    prices = {

        7: "35₽",

        30: "85₽",

        90: "245₽",

        365: "605₽"

    }


    await callback.message.answer(
        f"""
👑 Орёл VPN


📅 Срок:
{days} дней


💰 Цена:
{prices[days]}


💳 Оплата переводом:


Номер:
{CARD_NUMBER}


Получатель:
{CARD_OWNER}


После оплаты отправьте сюда скриншот.
"""
    )


    await callback.answer()





# =====================
# ПРОБНЫЙ ПЕРИОД
# =====================

@router.message(
    F.text == "🎁 Пробный период"
)

async def trial(message: Message):


    if check_trial(
        message.from_user.id
    ):

        await message.answer(
            "❌ Вы уже использовали пробный период."
        )

        return



    activate_trial(
        message.from_user.id,
        BS_LINK
    )


    await message.answer(
        f"""
🎁 Пробный период активирован!


⏳ Срок:
3 дня


🔗 Ваша подписка:

{BS_LINK}
"""
    )





# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

@router.message(
    F.text == "👤 Личный кабинет"
)

async def cabinet(message: Message):


    user = get_user(
        message.from_user.id
    )


    if not user:

        await message.answer(
            "Профиль не найден."
        )

        return



    await message.answer(
        f"""
👤 Личный кабинет


🆔 ID:
{user[0]}


👑 Тариф:
{user[2]}


📅 Действует до:
{user[4]}
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