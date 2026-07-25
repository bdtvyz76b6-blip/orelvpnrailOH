from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID

from database import (
    create_promo,
    get_promos,
    delete_promo
)


router = Router()



# =====================
# СОСТОЯНИЯ
# =====================

class PromoState(StatesGroup):

    create = State()

    delete = State()



# =====================
# ПРОВЕРКА АДМИНА
# =====================

def is_admin(user_id):

    return user_id == ADMIN_ID



# =====================
# СОЗДАТЬ
# =====================

@router.callback_query(
    F.data == "create_promo"
)
async def create(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(
        callback.from_user.id
    ):
        return


    await state.set_state(
        PromoState.create
    )


    await callback.message.answer(
"""
🎫 Создание промокода


Введите:

КОД ДНИ


Пример:

OREL30 30
"""
    )


    await callback.answer()



@router.message(
PromoState.create
)
async def create_process(
    message: Message,
    state: FSMContext
):

    if not is_admin(
        message.from_user.id
    ):
        return



    data = message.text.split()


    if len(data) != 2:

        await message.answer(
            "❌ Формат: КОД ДНИ"
        )

        return



    code = data[0].upper()

    days = int(data[1])



    create_promo(
        code,
        days
    )


    await message.answer(
f"""
✅ Промокод создан


🎫 Код:
{code}


⏳ Дней:
{days}
"""
    )


    await state.clear()



# =====================
# СПИСОК
# =====================

@router.callback_query(
F.data == "list_promo"
)
async def list_promos(
    callback: CallbackQuery
):

    promos = get_promos()



    if not promos:

        await callback.message.answer(
            "🎫 Промокодов нет"
        )

        return



    text = """
🎫 Промокоды:


"""


    for promo in promos:

        text += f"""
🔑 {promo[0]}

⏳ {promo[1]} дней

────────
"""



    await callback.message.answer(
        text
    )


    await callback.answer()



# =====================
# УДАЛИТЬ
# =====================

@router.callback_query(
F.data == "delete_promo"
)
async def delete(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(
        callback.from_user.id
    ):
        return


    await state.set_state(
        PromoState.delete
    )


    await callback.message.answer(
"""
🗑 Удаление промокода


Введите код:
"""
    )


    await callback.answer()



@router.message(
PromoState.delete
)
async def delete_process(
    message: Message,
    state: FSMContext
):

    code = message.text.upper()


    delete_promo(
        code
    )


    await message.answer(
f"""
🗑 Промокод удалён:

{code}
"""
    )


    await state.clear()