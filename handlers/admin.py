from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_ID

from database import (
    get_all_users,
    get_user,
    activate_bs,
    remove_bs,
    get_stats
)

from keyboards import (
    admin_menu,
    users_keyboard,
    user_card_keyboard
)


router = Router()


# =====================
# АДМИН ПАНЕЛЬ
# =====================

@router.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выберите раздел:",
        reply_markup=admin_menu()
    )



# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

@router.message(F.text == "👥 Пользователи")
async def users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    users = get_all_users()


    if not users:
        await message.answer(
            "Пользователей нет."
        )
        return


    await message.answer(
        f"👥 Пользователи\n\n"
        f"Всего: {len(users)}",
        reply_markup=users_keyboard(users)
    )



# =====================
# КАРТОЧКА
# =====================

@router.callback_query(F.data.startswith("user_"))
async def user_card(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[1]
    )


    user = get_user(user_id)


    if not user:
        await callback.answer(
            "Нет пользователя"
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


    await callback.message.edit_text(

        f"""
👤 Карточка пользователя

🆔 ID:
{user[0]}

👤 Username:
@{user[1]}

🆓 Wi-Fi:
{wifi}

👑 Обход Б/С:
{bs}

📅 Создан:
{user[6]}
""",

        reply_markup=user_card_keyboard(user_id)
    )


    await callback.answer()



# =====================
# ВЫДАТЬ ОБХОД
# =====================

@router.callback_query(F.data.startswith("give_bs_"))
async def give_bs(callback: CallbackQuery):

    user_id = int(
        callback.data.split("_")[2]
    )


    activate_bs(
        user_id,
        BS_LINK
    )


    try:

        await callback.bot.send_message(
            user_id,
            "🎉 Вам активировали тариф:\n\n"
            "👑 Обход Б/С\n\n"
            f"{BS_LINK}"
        )

    except:
        pass


    await callback.answer(
        "Выдано ✅"
    )



# =====================
# ЗАБРАТЬ ОБХОД
# =====================

@router.callback_query(F.data.startswith("remove_bs_"))
async def remove_bs_handler(callback: CallbackQuery):

    user_id = int(
        callback.data.split("_")[2]
    )


    remove_bs(user_id)


    try:

        await callback.bot.send_message(
            user_id,
            "❌ Обход Б/С отключён."
        )

    except:
        pass


    await callback.answer(
        "Отключено"
    )



# =====================
# СТАТИСТИКА
# =====================

@router.message(F.text == "📊 Статистика")
async def stats(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    data = get_stats()


    await message.answer(

        f"""
📊 Статистика

👥 Пользователей:
{data["total"]}

🆓 Wi-Fi:
{data["wifi"]}

👑 Обход Б/С:
{data["bs"]}
"""
    )



# =====================
# ЗАЯВКИ
# =====================

@router.message(F.text == "💳 Заявки")
async def requests(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "💳 Заявки\n\n"
        "Новые оплаты будут приходить сюда."
    )



# =====================
# РАССЫЛКА
# =====================

@router.message(F.text == "📢 Рассылка")
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "📢 Раздел рассылки"
    )



# =====================
# ПРОМОКОДЫ
# =====================

@router.message(F.text == "🎁 Промокоды")
async def promo(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "🎁 Промокоды"
    )



# =====================
# НАСТРОЙКИ
# =====================

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "⚙️ Настройки"
    )