from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user


router = Router()


# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

async def show_cabinet(message: Message):

    user_id = message.from_user.id

    user = get_user(user_id)

    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы.\nНажмите /start"
        )
        return


    username = message.from_user.username

    if username:
        user_name = f"@{username}"
    else:
        user_name = "Без username"


    tariff = user["tariff"]
    expire = user["subscription_until"]
    link = user["link"]


    if tariff in ["none", "", None]:
        tariff_text = "❌ Нет подписки"
        status = "❌ Не активна"
        expire_text = "—"

    else:
        tariff_text = tariff
        status = "✅ Активна"
        expire_text = expire or "—"


    await message.answer(
        f"""
🦅 Личный кабинет Orel VPN


👤 Пользователь:
{user_name}


🆔 ID:
{user_id}


👑 Тариф:
{tariff_text}


📅 Действует до:
{expire_text}


📡 Статус:
{status}


🔗 Ссылка:
{link or "Нет ссылки"}
""",
        reply_markup=cabinet_keyboard()
    )



# Команда /cabinet

@router.message(Command("cabinet"))
async def cabinet(message: Message):
    await show_cabinet(message)



# Кнопка 👤 Личный кабинет

@router.message(F.text == "👤 Личный кабинет")
async def cabinet_button(message: Message):
    await show_cabinet(message)



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
# ССЫЛКА
# =====================

@router.callback_query(F.data == "copy_link")
async def copy_link(callback: CallbackQuery):

    user = get_user(callback.from_user.id)

    if not user:
        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )
        return


    link = user["link"]


    await callback.message.answer(
        f"📋 Ваша ссылка:\n\n{link}"
    )


    await callback.answer()



# =====================
# ОБНОВЛЕНИЕ
# =====================

@router.callback_query(F.data == "cabinet")
async def cabinet_refresh(callback: CallbackQuery):

    await callback.message.delete()

    await show_cabinet(callback.message)

    await callback.answer("Обновлено ✅")