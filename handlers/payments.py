from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_OWNER,
    PRICE_BS,
    BS_LINK
)

from database import activate_bs
from keyboards import approve_keyboard

router = Router()


def payment_done_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Я оплатил",
                    callback_data="paid"
                )
            ]
        ]
    )


@router.callback_query(F.data == "buy_bs")
async def buy_bs(callback: CallbackQuery):
    await callback.message.answer(
        "👑 Обход Б/С\n\n"
        f"Стоимость: {PRICE_BS}\n\n"
        "Перевод:\n"
        f"💳 {CARD_NUMBER}\n\n"
        f"Получатель: {CARD_OWNER}\n\n"
        "После оплаты нажмите кнопку «✅ Я оплатил» и отправьте чек боту.",
        reply_markup=payment_done_keyboard()
    )

    await callback.answer()


@router.callback_query(F.data == "paid")
async def paid(callback: CallbackQuery):
    await callback.message.answer(
        "📎 Отправьте чек оплаты сюда."
    )

    await callback.answer()


@router.message(F.photo)
async def get_check(message: Message):
    await message.bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=(
            "🔔 Новая заявка на оплату через мини-приложение\n\n"
            f"👤 Пользователь:\n@{message.from_user.username}\n"
            f"ID: {message.from_user.id}\n\n"
            "Тариф:\n👑 Обход Б/С"
        ),
        reply_markup=approve_keyboard(message.from_user.id)
    )

    await message.answer(
        "✅ Чек отправлен. Ожидайте подтверждения."
    )


@router.callback_query(F.data.startswith("give_"))
async def give_access(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    activate_bs(user_id, BS_LINK)

    await callback.bot.send_message(
        user_id,
        "🎉 Вам активировали тариф!\n\n"
        "👑 Обход Б/С\n\n"
        "Ваша ссылка:\n"
        f"{BS_LINK}"
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ Оплата подтверждена"
    )

    await callback.answer("Доступ выдан")


@router.callback_query(F.data.startswith("deny_"))
async def deny_access(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])

    await callback.bot.send_message(
        user_id,
        "❌ Ваша оплата не была подтверждена."
    )

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ Оплата отклонена"
    )

    await callback.answer("Заявка отклонена")