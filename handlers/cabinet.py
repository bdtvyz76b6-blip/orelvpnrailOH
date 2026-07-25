from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from datetime import datetime

from database import get_user


router = Router()



# =====================
# ДНИ ДО ОКОНЧАНИЯ
# =====================

def get_days_left(date):

    if not date:
        return 0

    try:

        end = datetime.strptime(
            date,
            "%Y-%m-%d"
        )

        days = (
            end - datetime.now()
        ).days


        if days < 0:
            return 0


        return days


    except:

        return 0



# =====================
# ПОКАЗ КАБИНЕТА
# =====================

async def show_cabinet(message: Message):

    user = get_user(
        message.from_user.id
    )


    if not user:

        await message.answer(
            "❌ Профиль не найден.\nНажмите /start"
        )

        return



    user_id = user["user_id"]

    tariff = user["tariff"]

    expire = user["subscription_until"]

    status = user["status"]

    servers = user["servers_count"]

    devices = user["devices_count"]

    limit = user["devices_limit"]


    days = get_days_left(
        expire
    )


    if days > 0:

        status_text = "✅ Активен"

    else:

        status_text = "❌ Закончился"



    await message.answer(
f"""
🦅 Орёл VPN


👤 Личный кабинет


🆔 ID:
{user_id}


👑 Тариф:
{tariff}


📅 До:
{expire if expire else "—"}


📡 Статус:
{status_text}


🌍 Серверов:
{servers}


📱 Устройства:
{devices}/{limit}


⏳ Осталось:
{days} дней
""",
        reply_markup=cabinet_keyboard()
    )



# =====================
# КОМАНДА
# =====================

@router.message(
    Command("cabinet")
)
async def cabinet_command(message: Message):

    await show_cabinet(
        message
    )



# =====================
# КНОПКА МЕНЮ
# =====================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet_button(message: Message):

    await show_cabinet(
        message
    )



# =====================
# КЛАВИАТУРА
# =====================

def cabinet_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[


            [
                InlineKeyboardButton(
                    text="📋 Получить ссылку",
                    callback_data="copy_link"
                )
            ],


            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="refresh_cabinet"
                )
            ],


            [
                InlineKeyboardButton(
                    text="💎 Продлить",
                    callback_data="buy"
                )
            ],


            [
                InlineKeyboardButton(
                    text="⚙️ Настройки",
                    callback_data="settings"
                )
            ],


            [
                InlineKeyboardButton(
                    text="🆘 Поддержка",
                    url="https://t.me/rusrodyyya"
                )
            ]

        ]
    )



# =====================
# ССЫЛКА
# =====================

@router.callback_query(
    F.data == "copy_link"
)
async def copy_link(callback: CallbackQuery):

    user = get_user(
        callback.from_user.id
    )


    if not user:

        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )

        return



    link = user["link"]


    if not link:

        await callback.message.answer(
            "❌ У вас пока нет активной подписки"
        )

    else:

        await callback.message.answer(
f"""
📋 Ваша ссылка:

{link}
"""
        )


    await callback.answer()



# =====================
# ОБНОВЛЕНИЕ
# =====================

@router.callback_query(
    F.data == "refresh_cabinet"
)
async def refresh_cabinet(callback: CallbackQuery):

    await callback.message.delete()


    await show_cabinet(
        callback.message
    )


    await callback.answer(
        "Обновлено ✅"
    )