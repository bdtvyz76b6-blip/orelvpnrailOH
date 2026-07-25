from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user


router = Router()


# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

@router.message(Command("cabinet"))
async def cabinet(message: Message):

    user_id = message.from_user.id

    user = get_user(user_id)


    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы.\n"
            "Нажмите /start"
        )
        return


    username = message.from_user.username

    if username:
        user_name = f"@{username}"
    else:
        user_name = "Без username"



    tariff = user["tariff"]
    expire = user["subscription_until"]
    link = user["subscription_link"]



    if tariff in ["none", "", None]:

        tariff_text = "❌ Нет подписки"
        status = "❌ Не активна"
        expire_text = "—"

    else:

        tariff_text = f"👑 {tariff}"
        status = "✅ Активна"
        expire_text = expire



    text = f"""
🦅 Личный кабинет Orel VPN


👤 Пользователь:
{user_name}


📌 Тариф:
{tariff_text}


📅 Дата окончания:
{expire_text}


📡 Статус:
{status}


🔗 Ваша подписка:
Нажмите кнопку ниже, чтобы получить ссылку 📋
"""


    await message.answer(
        text,
        reply_markup=cabinet_keyboard()
    )



# =====================
# КНОПКИ
# =====================

def cabinet_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📋 Скопировать ссылку",
                    callback_data="copy_link"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💎 Купить подписку",
                    callback_data="buy"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔄 Обновить статус",
                    callback_data="cabinet"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🆘 Поддержка",
                    url="https://t.me/orelvpntopbot"
                )
            ]

        ]
    )



# =====================
# ОТПРАВКА ССЫЛКИ
# =====================

@router.callback_query(F.data == "copy_link")
async def copy_link(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user(user_id)


    if not user:

        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )

        return



    link = user["subscription_link"]



    await callback.message.answer(
        f"📋 Ваша ссылка для копирования:\n\n{link}"
    )


    await callback.answer(
        "Ссылка отправлена ✅"
    )



# =====================
# ОБНОВЛЕНИЕ КАБИНЕТА
# =====================

@router.callback_query(F.data == "cabinet")
async def cabinet_refresh(callback: CallbackQuery):

    await callback.message.delete()

    await cabinet(callback.message)

    await callback.answer(
        "Обновлено ✅"
    )