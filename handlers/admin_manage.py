from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_user,
    activate_subscription,
    remove_bs
)

from github_update import create_subscription

from config import ADMIN_ID


router = Router()



# =====================
# СОСТОЯНИЯ
# =====================

class ManageUser(StatesGroup):

    waiting_id = State()

    waiting_days = State()

    waiting_message = State()



# =====================
# ПРОВЕРКА
# =====================

def is_admin(user_id):

    return user_id == ADMIN_ID



# =====================
# НАЧАТЬ УПРАВЛЕНИЕ
# =====================

@router.callback_query(
    F.data == "admin_manage"
)
async def manage(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return


    await callback.message.answer(
"""
⚙️ Управление пользователем


Введите Telegram ID пользователя:
"""
    )


    await callback.answer()



# =====================
# ПОЛУЧИТЬ ID
# =====================

@router.message(ManageUser.waiting_id)
async def get_id(message: Message, state: FSMContext):

    user_id = int(message.text)


    user = get_user(user_id)


    if not user:

        await message.answer(
            "❌ Пользователь не найден"
        )

        await state.clear()

        return



    await state.update_data(
        user_id=user_id
    )


    await message.answer(
f"""
👤 Пользователь найден


🆔 ID:
{user['user_id']}


👑 Тариф:
{user['tariff']}


📅 До:
{user['subscription_until']}


Выберите действие:

➕ Выдать подписку
⏳ Продлить
❌ Отключить
"""
    )


    await state.clear()



# =====================
# ВЫДАТЬ ПОДПИСКУ
# =====================

@router.message(
    F.text == "➕ Выдать подписку"
)
async def give_sub(message: Message):

    if not is_admin(message.from_user.id):
        return


    await message.answer(
        "Введите количество дней:"
    )



# =====================
# ОТКЛЮЧИТЬ
# =====================

@router.message(
    F.text == "❌ Отключить"
)
async def disable(message: Message):

    if not is_admin(message.from_user.id):
        return


    await message.answer(
        "Введите ID пользователя:"
    )


    # дальше подключим обработчик удаления



# =====================
# СООБЩЕНИЕ
# =====================

@router.message(
    F.text == "📩 Написать"
)
async def write_user(message: Message):

    await message.answer(
        "Введите ID пользователя и текст:"
    )