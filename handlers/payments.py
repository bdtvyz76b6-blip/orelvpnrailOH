from aiogram import Router, F
from aiogram.types import Message

from config import ADMIN_ID

from keyboards import approve_keyboard


router = Router()


@router.message(F.photo)
async def payment_photo(message: Message):

    await message.answer(
        "✅ Скриншот отправлен администратору.\n"
        "Ожидайте проверки."
    )


    await message.bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=
        f"💳 Новый чек\n\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"👤 @{message.from_user.username}",
        reply_markup=approve_keyboard(
            message.from_user.id
        )
    )