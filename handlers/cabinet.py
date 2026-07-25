from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database import (
    add_user,
    get_user
)

from config import SUPPORT

from datetime import datetime


router = Router()



# =====================
# КАБИНЕТ
# =====================

@router.message(
    F.text == "👤 Личный кабинет"
)
async def cabinet(message: Message):

    user_id = message.from_user.id


    # создаём пользователя если его нет
    add_user(
        user_id,
        message.from_user.username
    )


    user = get_user(
        user_id
    )


    if not user:

        await message.answer(
            "❌ Ошибка профиля"
        )

        return



    tariff = user[2]

    link = user[3]

    expire = user[4]



    # статус

    status = "❌ Не активен"

    days_left = "—"



    if expire:


        try:

            date = datetime.strptime(
                expire,
                "%Y-%m-%d"
            )


            left = (
                date.date()
                -
                datetime.now().date()
            ).days



            if left > 0:

                status = "✅ Активен"

                days_left = left



            else:

                status = "❌ Завершён"

                days_left = 0



        except:

            pass



    # тариф

    if tariff == "Wi-Fi":

        tariff_text = "🆓 Wi-Fi"



    else:

        tariff_text = f"👑 {tariff}"



    text = f"""
👤 Личный кабинет


🆔 ID:
{user_id}


👑 Тариф:
{tariff_text}


📅 До:
{expire if expire else "—"}


📡 Статус:
{status}


🌍 Серверов:
5


📱 Устройства:
—


⏳ Осталось:
{days_left} дней


🔗 Подписка:
Нажмите кнопку ниже
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
                    text="📋 Моя ссылка",
                    callback_data="my_link"
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
                    url=f"https://t.me/{SUPPORT.replace('@','')}"
                )
            ]

        ]
    )





# =====================
# ССЫЛКА
# =====================

@router.callback_query(
    F.data == "my_link"
)
async def my_link(
    callback: CallbackQuery
):

    user = get_user(
        callback.from_user.id
    )


    if not user:

        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )

        return



    link = user[3]



    if not link:

        link = "❌ Подписка не активна"



    await callback.message.answer(
f"""
🔗 Ваша ссылка:

{link}
"""
    )


    await callback.answer()





# =====================
# ОБНОВИТЬ
# =====================

@router.callback_query(
    F.data == "refresh_cabinet"
)
async def refresh(
    callback: CallbackQuery
):

    await callback.message.delete()


    await cabinet(
        callback.message
    )


    await callback.answer(
        "Обновлено ✅"
    )