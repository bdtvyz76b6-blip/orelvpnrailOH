from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID

from database import (
    get_all_users
)


router = Router()



# =====================
# СОСТОЯНИЯ
# =====================

class BroadcastState(StatesGroup):

    waiting_text = State()

    waiting_type = State()



# =====================
# ПРОВЕРКА АДМИНА
# =====================

def is_admin(user_id):

    return user_id == ADMIN_ID



# =====================
# ВЫБОР ГРУППЫ
# =====================

@router.callback_query(
    F.data.startswith("broadcast_")
)
async def start_broadcast(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(
        callback.from_user.id
    ):
        return


    group = callback.data.replace(
        "broadcast_",
        ""
    )


    await state.update_data(
        group=group
    )


    await state.set_state(
        BroadcastState.waiting_text
    )


    await callback.message.answer(
"""
📢 Рассылка


Отправьте текст сообщения:

Можно использовать:
- эмодзи
- ссылки
- переносы строк
"""
    )


    await callback.answer()



# =====================
# ОТПРАВКА
# =====================

@router.message(
BroadcastState.waiting_text
)
async def send_broadcast(
    message: Message,
    state: FSMContext
):

    if not is_admin(
        message.from_user.id
    ):
        return



    data = await state.get_data()


    group = data.get(
        "group"
    )


    users = get_all_users()


    sent = 0

    failed = 0



    for user in users:

        user_id = user[0]

        tariff = user[2]

        expire = user[4]



        # ВСЕ

        if group == "all":

            pass



        # VIP

        elif group == "vip":

            if "Орёл VPN" not in tariff:

                continue



        # ПРОБНИКИ

        elif group == "trial":

            if "Пробный" not in tariff:

                continue



        # СКОРО ЗАКОНЧИТСЯ

        elif group == "soon":

            if not expire:

                continue



        try:

            await message.bot.send_message(

                user_id,

                message.text

            )


            sent += 1


        except:

            failed += 1



    await message.answer(
f"""
📢 Рассылка завершена


✅ Отправлено:
{sent}


❌ Ошибок:
{failed}
"""
    )


    await state.clear()