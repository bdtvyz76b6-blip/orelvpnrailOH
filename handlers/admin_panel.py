from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import ADMIN_ID
from keyboards import admin_menu


router = Router()


# =====================
# АДМИН ПАНЕЛЬ
# =====================

@router.message(Command("admin"))
async def admin_start(message: Message):

    if message.from_user.id != ADMIN_ID:

        await message.answer(
            "❌ Нет доступа."
        )

        return


    await message.answer(
        """
☂️ Админ панель

Выберите действие:
""",
        reply_markup=admin_menu()
    )