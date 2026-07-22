from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_ID, BS_LINK

from database import (
    get_all_users,
    get_user,
    activate_bs,
    remove_bs
)

from keyboards import (
    admin_menu,
    users_keyboard,
    user_card_keyboard
)


router = Router()


# =========================
# Вход в админку
# =========================

@router.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выберите раздел:",
        reply_markup=admin_menu()
    )


# =========================
# Пользователи
# =========================

@router.message(F.text == "👥 Пользователи")
async def users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    await message.answer(
        f"👥 Пользователи\n\n"
        f"Всего: {len(users)}",
        reply_markup=users_keyboard(users)
    )


# =========================
# Карточка пользователя
# =========================

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
            "Пользователь не найден"
        )
        return


    wifi = "✅ Активен" if user[2] else "❌ Нет"

    bs = "✅ Активен" if user[3] else "❌ Нет"


    await callback.message.edit_text(

        f"""
👤 Карточка пользователя


🆔 ID:
{user[0]}


👤 Username:
@{user[1]}


🟢 Wi-Fi:
{wifi}


👑 Обход Б/С:
{bs}

        """,

        reply_markup=user_card_keyboard(user_id)
    )


    await callback.answer()



# =========================
# Выдать Б/С
# =========================

@router.callback_query(F.data.startswith("give_bs_"))
async def give_bs(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[2]
    )


    activate_bs(
        user_id,
        BS_LINK
    )


    await callback.answer(
        "👑 Обход Б/С выдан"
    )


# =========================
# Забрать Б/С
# =========================

@router.callback_query(F.data.startswith("remove_bs_"))
async def remove_bs_handler(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[2]
    )


    remove_bs(user_id)


    await callback.answer(
        "❌ Обход Б/С отключён"
    )
