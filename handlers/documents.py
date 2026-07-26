from aiogram import Router, F
from aiogram.types import Message

from keyboards import documents_keyboard


router = Router()


@router.message(
    F.text == "📄 Документы"
)
async def documents(message: Message):

    await message.answer(
        """
📄 Документы сервиса «Орёл VPN»

Перед использованием сервиса ознакомьтесь:

• Пользовательское соглашение
• Политика конфиденциальности
        """,
        reply_markup=documents_keyboard()
    )