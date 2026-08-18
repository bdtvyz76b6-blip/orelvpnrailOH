from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_IDS
from keyboards.admin_keyboard import admin_menu


router = Router()


# =====================
# АДМИН ПАНЕЛЬ
# =====================

@router.message(Command("admin"))
async def admin_start(message: Message):

    # =====================
    # ПРОВЕРКА АДМИНА
    # =====================

    if message.from_user.id not in ADMIN_IDS:

        await message.answer(
            "❌ Нет доступа."
        )

        return

    # =====================
    # АДМИН МЕНЮ
    # =====================

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выбери раздел:",
        reply_markup=admin_menu()
    )