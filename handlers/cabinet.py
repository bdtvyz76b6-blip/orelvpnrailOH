from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database import get_user

router = Router()


@router.message(Command("cabinet"))
async def cabinet(message: Message):

    user_id = message.from_user.id

    user = get_user(user_id)

    if not user:
        await message.answer(
            "❌ Вы ещё не зарегистрированы.\n"
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


    if tariff == "none":
        status = "❌ Не активна"
        tariff_text = "❌ Нет подписки"
        expire_text = "—"

    else:
        status = "✅ Активна"
        tariff_text = f"👑 {tariff}"
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
{link}
"""


    await message.answer(
        text,
        reply_markup=cabinet_keyboard()
    )



def cabinet_keyboard():

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    return InlineKeyboardMarkup(
        inline_keyboard=[
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