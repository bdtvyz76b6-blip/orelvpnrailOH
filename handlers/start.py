from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from database import add_user
from keyboards import main_menu


router = Router()


# =========================
# /start
# =========================

@router.message(CommandStart())
async def start(message: Message):

    user_id = message.from_user.id
    username = message.from_user.username or "без_username"


    add_user(
        user_id,
        username
    )


    await message.answer(
        "🦅 Орёл VPN\n\n"
        "Добро пожаловать!\n\n"
        "Выберите нужный раздел:",
        reply_markup=main_menu()
    )