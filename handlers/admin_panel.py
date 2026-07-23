from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from states import PromoStates, BroadcastStates

from keyboards import (
    promo_menu,
    broadcast_menu,
    admin_menu
)

from database import (
    create_promo,
    get_promos,
    get_user_ids
)


router = Router()



# =====================
# ПРОМОКОДЫ
# =====================

@router.message(F.text == "🎁 Промокоды")
async def promo_open(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🎁 Управление промокодами:",
        reply_markup=promo_menu()
    )



@router.callback_query(F.data == "create_promo")
async def create_promo_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id != ADMIN_ID:
        return


    await callback.message.answer(
        "Введите промокод и дни:\n\n"
        "Пример:\n"
        "OREL30 30"
    )


    await state.set_state(
        PromoStates.waiting_promo
    )


    await callback.answer()



@router.message(PromoStates.waiting_promo)
async def save_promo(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return


    data = message.text.split()


    if len(data) != 2:

        await message.answer(
            "Формат:\nКОД ДНИ"
        )
        return


    code = data[0]
    days = int(data[1])


    create_promo(
        code,
        days
    )


    await message.answer(
        f"✅ Промокод создан\n\n"
        f"🔑 {code}\n"
        f"📅 {days} дней"
    )


    await state.clear()




@router.callback_query(F.data == "list_promo")
async def list_promo(callback: CallbackQuery):

    promos = get_promos()


    if not promos:

        await callback.message.answer(
            "Промокодов нет"
        )

        return


    text = "🎁 Промокоды:\n\n"


    for p in promos:

        text += (
            f"🔑 {p[0]} — {p[1]} дней\n"
        )


    await callback.message.answer(text)

    await callback.answer()





# =====================
# РАССЫЛКА
# =====================


@router.message(F.text == "📢 Рассылка")
async def broadcast_open(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "📢 Рассылка:",
        reply_markup=broadcast_menu()
    )



@router.callback_query(F.data == "create_broadcast")
async def broadcast_start(
    callback: CallbackQuery,
    state: FSMContext
):

    await callback.message.answer(
        "Введите сообщение для рассылки:"
    )


    await state.set_state(
        BroadcastStates.waiting_text
    )


    await callback.answer()




@router.message(BroadcastStates.waiting_text)
async def send_broadcast(
    message: Message,
    state: FSMContext
):

    if message.from_user.id != ADMIN_ID:
        return


    users = get_user_ids()

    count = 0


    for user_id in users:

        try:

            await message.bot.send_message(
                user_id,
                message.text
            )

            count += 1

        except:

            pass



    await message.answer(
        f"📢 Рассылка завершена\n\n"
        f"Отправлено: {count}"
    )


    await state.clear()




# =====================
# НАЗАД
# =====================


@router.callback_query(F.data == "admin_back")
async def back(callback: CallbackQuery):

    await callback.message.answer(
        "🦅 Админ-панель",
        reply_markup=admin_menu()
    )

    await callback.answer()
