from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import get_user_ids
from loader import bot

router = Router()


class Broadcast(StatesGroup):
    text = State()


@router.callback_query(F.data == "admin_broadcast")
async def broadcast(call: CallbackQuery, state: FSMContext):

    await state.set_state(Broadcast.text)

    await call.message.answer(
        "📢 Отправь сообщение для рассылки."
    )


@router.message(Broadcast.text)
async def send_broadcast(message: Message, state: FSMContext):

    users = get_user_ids()

    ok = 0
    bad = 0

    for user_id in users:

        try:
            await bot.send_message(
                user_id,
                message.text
            )
            ok += 1

        except:
            bad += 1

    await message.answer(
        f"✅ Рассылка завершена\n\n"
        f"📨 Отправлено: {ok}\n"
        f"❌ Ошибок: {bad}"
    )

    await state.clear()