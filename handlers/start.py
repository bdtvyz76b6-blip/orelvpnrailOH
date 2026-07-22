from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import (
    WIFI_LINK,
    BS_LINK,
    FREE_TARIFF,
    PAID_TARIFF,
    SUPPORT,
    PRICE_BS,
    CARD_NUMBER,
    CARD_OWNER
)

from database import (
    add_user,
    get_user,
    activate_bs,
    set_tariff
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
# WI-FI
# =====================

@router.message(F.text == "🆓 Wi-Fi")
async def wifi(message: Message):

    set_tariff(
        message.from_user.id,
        FREE_TARIFF,
        WIFI_LINK
    )


    await message.answer(
        "🆓 Wi-Fi активен\n\n"
        "Ваша подписка:\n"
        f"{WIFI_LINK}"
    )



# =====================
# ОБХОД Б/С
# =====================

@router.message(F.text == "👑 Обход Б/С")
async def bs(message: Message):

    user = get_user(
        message.from_user.id
    )


    if user and user[5] == 1:

        await message.answer(
            "👑 Обход Б/С активен\n\n"
            f"{BS_LINK}"
        )

    else:

        await message.answer(
            "👑 Обход Б/С\n\n"
            f"Цена: {PRICE_BS}\n\n"
            "Нажмите кнопку покупки:",
            reply_markup=buy_keyboard()
        )



# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

@router.message(F.text == "👤 Личный кабинет")
async def cabinet(message: Message):

    user = get_user(
        message.from_user.id
    )


    if not user:
        await message.answer(
            "Профиль не найден."
        )
        return



    wifi = (
        "✅ Активен"
        if user[4]
        else
        "❌ Нет"
    )


    bs = (
        "✅ Активен"
        if user[5]
        else
        "❌ Нет"
    )


    await message.answer(

        f"""
👤 Личный кабинет

🆔 ID:
{user[0]}

👤 Username:
@{user[1]}

🆓 Wi-Fi:
{wifi}

👑 Обход Б/С:
{bs}

📅 Регистрация:
{user[6]}
"""
    )



# =====================
# ПОКУПКА
# =====================

@router.callback_query(F.data == "buy_bs")
async def buy_bs(callback: CallbackQuery):

    await callback.message.answer(

        f"""
👑 Покупка Обход Б/С

💰 Цена:
{PRICE_BS}

💳 Реквизиты:
{CARD_NUMBER}

👤 Получатель:
{CARD_OWNER}

После оплаты отправьте скриншот сюда.
"""
    )


    await callback.answer()



# =====================
# ПОДДЕРЖКА
# =====================

@router.message(F.text == "💬 Поддержка")
async def support(message: Message):

    await message.answer(
        "💬 Поддержка:\n\n"
        f"{SUPPORT}"
    )



# =====================
# НАЗАД
# =====================

@router.message(F.text == "⬅️ Назад")
async def back(message: Message):

    await message.answer(
        "Главное меню:",
        reply_markup=main_menu()
    )