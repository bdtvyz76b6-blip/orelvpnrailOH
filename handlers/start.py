from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from database import add_user, get_user
from keyboards import main_menu, buy_keyboard
from config import (
    WIFI_LINK,
    BS_LINK,
    SUPPORT
)

router = Router()


# /start
@router.message(CommandStart())
async def start(message: Message):
    add_user(
        message.from_user.id,
        message.from_user.username or "без_username"
    )

    await message.answer(
        "🦅 Орёл VPN\n\n"
        "Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )


# Wi-Fi
@router.message(F.text == "🆓 Wi-Fi")
async def wifi(message: Message):
    await message.answer(
        "🆓 Wi-Fi\n\n"
        "Ваша бесплатная ссылка:\n\n"
        f"{WIFI_LINK}"
    )


# Обход Б/С
@router.message(F.text == "👑 Обход Б/С")
async def bypass(message: Message):
    user = get_user(message.from_user.id)

    if user and user[3] == 1:
        await message.answer(
            "👑 Обход Б/С активен\n\n"
            "Ваша ссылка:\n\n"
            f"{BS_LINK}"
        )
    else:
        await message.answer(
            "👑 Обход Б/С\n\n"
            "Стоимость: 99₽\n\n"
            "Нажмите кнопку ниже для покупки:",
            reply_markup=buy_keyboard()
        )


# Личный кабинет
@router.message(F.text == "👤 Личный кабинет")
async def cabinet(message: Message):
    user = get_user(message.from_user.id)

    if not user:
        await message.answer(
            "Сначала нажмите /start"
        )
        return

    wifi_status = "✅ Активен"
    bs_status = "✅ Активен" if user[3] == 1 else "❌ Не активен"
    bs_link = BS_LINK if user[3] == 1 else "Нет доступа"

    await message.answer(
        f"""👤 Личный кабинет

🆔 ID: {user[0]}
👤 Username: @{user[1]}

🟢 Wi-Fi: {wifi_status}
🔗 {WIFI_LINK}

👑 Обход Б/С: {bs_status}
🔗 {bs_link}"""
    )


# Поддержка
@router.message(F.text == "💬 Поддержка")
async def support(message: Message):
    await message.answer(
        f"💬 Поддержка:\n\n{SUPPORT}"
    )