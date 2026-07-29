from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import (
    add_promocode,
    get_promocodes,
    delete_promocode
)

router = Router()


class PromoCreate(StatesGroup):
    code = State()
    days = State()



@router.callback_query(F.data == "admin_promos")
async def promos(call: CallbackQuery):

    await call.message.edit_text(
        "🎟 Промокоды\n\n"
        "Выбери действие:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="➕ Создать",
                        callback_data="promo_create"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📋 Список",
                        callback_data="promo_list"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🗑 Удалить",
                        callback_data="promo_delete"
                    )
                ]
            ]
        )
    )



@router.callback_query(F.data == "promo_create")
async def create_start(
    call: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        PromoCreate.code
    )

    await call.message.answer(
        "🎟 Введи код:"
    )



@router.message(PromoCreate.code)
async def get_code(
    message,
    state: FSMContext
):

    await state.update_data(
        code=message.text.upper()
    )

    await state.set_state(
        PromoCreate.days
    )

    await message.answer(
        "📅 Сколько дней выдать?"
    )



@router.message(PromoCreate.days)
async def get_days(
    message,
    state: FSMContext
):

    data = await state.get_data()

    code = data["code"]
    days = int(message.text)


    add_promocode(
        code,
        days
    )


    await message.answer(
        f"✅ Промокод создан\n\n"
        f"🎟 {code}\n"
        f"📅 {days} дней"
    )


    await state.clear()



@router.callback_query(F.data == "promo_list")
async def promo_list(call: CallbackQuery):

    promos = get_promocodes()

    if not promos:
        await call.message.edit_text(
            "🎟 Промокодов нет"
        )
        return


    text = "🎟 Активные промокоды:\n\n"

    for promo in promos:
        text += (
            f"🔹 {promo[0]} — "
            f"{promo[1]} дней\n"
        )


    await call.message.edit_text(
        text
    )