from aiogram import Router, F
from aiogram.types import Message

from keyboards.admin_keyboard import admin_menu


router = Router()

ADMIN_ID = 6312016802


@router.message(F.text == "/admin")
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выбери раздел:",
        reply_markup=admin_menu()
    )