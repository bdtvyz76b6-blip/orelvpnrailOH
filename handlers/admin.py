from aiogram import Router, F
from aiogram.types import Message

from keyboards.admin_keyboard import admin_menu
from config import ADMIN_IDS


router = Router()


@router.message(F.text == "/admin")
async def admin(message: Message):
    # Проверяем, является ли пользователь админом
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выбери раздел:",
        reply_markup=admin_menu()
    )