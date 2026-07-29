from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import get_user

router = Router()


class SearchUser(StatesGroup):
    waiting_id = State()


@router.callback_query(F.data == "admin_search")
async def start_search(
    call: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        SearchUser.waiting_id
    )

    await call.message.answer(
        "🔎 Введи ID пользователя:"
    )


@router.message(SearchUser.waiting_id)
async def find_user(
    message: Message,
    state: FSMContext
):

    try:
        user_id = int(message.text)

    except:
        await message.answer(
            "❌ Введи только цифры"
        )
        return


    user = get_user(user_id)


    if not user:
        await message.answer(
            "❌ Пользователь не найден"
        )
        await state.clear()
        return


    await message.answer(
        f"👤 Пользователь\n\n"
        f"🆔 ID: {user[0]}\n"
        f"👤 Username: @{user[1] or 'нет'}\n\n"
        f"📌 Тариф: {user[2]}\n"
        f"📅 До: {user[4] or 'нет'}\n\n"
        f"🔗 Подписка:\n{user[3] or 'нет'}"
    )


    await state.clear()