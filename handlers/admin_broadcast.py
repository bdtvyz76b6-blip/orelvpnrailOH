from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import BOT_TOKEN

from database import get_user_ids


router = Router()


bot = Bot(
    token=BOT_TOKEN
)


# =====================
# СОСТОЯНИЕ
# =====================

class Broadcast(StatesGroup):

    text = State()



# =====================
# НАЧАЛО РАССЫЛКИ
# =====================

@router.callback_query(
    F.data == "admin_broadcast"
)
async def start_broadcast(
    call: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        Broadcast.text
    )


    await call.message.answer(
        "📢 Отправь текст для рассылки:"
    )



# =====================
# ОТПРАВКА
# =====================

@router.message(
    Broadcast.text
)
async def send_broadcast(
    message: Message,
    state: FSMContext
):

    users = get_user_ids()


    sent = 0
    failed = 0


    for user_id in users:

        try:

            await bot.send_message(
                user_id,
                message.text
            )

            sent += 1


        except Exception:

            failed += 1



    await message.answer(
        "📢 Рассылка завершена\n\n"
        f"✅ Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}"
    )


    await state.clear()