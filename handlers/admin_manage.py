from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID

from database import (
    get_user,
    activate_subscription,
    remove_bs
)

from github_update import create_subscription


router = Router()



# =====================
# СОСТОЯНИЯ
# =====================

class ManageUser(StatesGroup):

    waiting_id = State()

    waiting_give = State()

    waiting_extend = State()

    waiting_message = State()



# =====================
# ПРОВЕРКА АДМИНА
# =====================

def is_admin(user_id):

    return user_id == ADMIN_ID



# =====================
# НАЙТИ ПОЛЬЗОВАТЕЛЯ
# =====================

@router.callback_query(
    F.data == "find_user"
)
async def find_user(
    callback: CallbackQuery,
    state: FSMContext
):

    if not is_admin(
        callback.from_user.id
    ):
        return


    await state.set_state(
        ManageUser.waiting_id
    )


    await callback.message.answer(
"""
👤 Поиск пользователя


Введите Telegram ID:
"""
    )


    await callback.answer()



@router.message(
    ManageUser.waiting_id
)
async def show_user(
    message: Message,
    state: FSMContext
):

    try:

        user_id = int(
            message.text
        )

    except:

        await message.answer(
            "❌ ID должен быть числом"
        )

        return



    user = get_user(
        user_id
    )


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
👤 Пользователь


🆔 ID:
{user[0]}


👤 Username:
{user[1]}


👑 Тариф:
{user[2]}


📅 До:
{user[4]}


🔗 Ссылка:
{user[3]}
""",
        reply_markup=user_menu()
    )


    await state.clear()



# =====================
# МЕНЮ ПОЛЬЗОВАТЕЛЯ
# =====================

def user_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Выдать VIP",
                    callback_data="give_user"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data="extend_user"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data="disable_user"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📩 Написать",
                    callback_data="message_user"
                )
            ]

        ]
    )



# =====================
# ВЫДАТЬ ПОДПИСКУ
# =====================

@router.callback_query(
    F.data == "give_user"
)
async def give_user(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        ManageUser.waiting_give
    )


    await callback.message.answer(
"""
➕ Выдать подписку


Введите:

ID дни


Пример:

6312016802 30
"""
    )


    await callback.answer()



@router.message(
    ManageUser.waiting_give
)
async def give_process(
    message: Message,
    state: FSMContext
):

    data = message.text.split()


    if len(data) != 2:

        await message.answer(
            "❌ Формат: ID дни"
        )

        return



    user_id = int(data[0])

    days = int(data[1])



    link = create_subscription(
        user_id,
        days=days
    )


    activate_subscription(
        user_id,
        link,
        days
    )



    await message.answer(
        "✅ Подписка выдана"
    )



    await message.bot.send_message(
        user_id,
f"""
🎉 Вам активировали Орёл VPN


⏳ Срок:
{days} дней


🔗 Ссылка:

{link}
"""
    )


    await state.clear()



# =====================
# ПРОДЛИТЬ
# =====================

@router.callback_query(
    F.data == "extend_user"
)
async def extend_user(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        ManageUser.waiting_extend
    )


    await callback.message.answer(
"""
⏳ Продлить подписку


Введите:

ID дни


Пример:

6312016802 30
"""
    )


    await callback.answer()



@router.message(
    ManageUser.waiting_extend
)
async def extend_process(
    message: Message,
    state: FSMContext
):

    data = message.text.split()


    user_id = int(
        data[0]
    )

    days = int(
        data[1]
    )


    link = create_subscription(
        user_id,
        days=days
    )


    activate_subscription(
        user_id,
        link,
        days
    )


    await message.answer(
        "⏳ Подписка продлена"
    )


    await state.clear()



# =====================
# ОТКЛЮЧИТЬ
# =====================

@router.callback_query(
    F.data == "disable_user"
)
async def disable_user(
    callback: CallbackQuery
):

    await callback.message.answer(
"""
❌ Отключение


Введите ID пользователя:
"""
    )


    await callback.answer()



@router.message(
F.text.regexp(r"^\d+$")
)
async def disable_process(
    message: Message
):

    if not is_admin(
        message.from_user.id
    ):
        return


    user_id = int(
        message.text
    )


    remove_bs(
        user_id
    )


    await message.answer(
        "❌ Подписка отключена"
    )



    await message.bot.send_message(
        user_id,
"""
⚠️ Ваша подписка Орёл VPN отключена.
"""
    )



# =====================
# НАПИСАТЬ
# =====================

@router.callback_query(
    F.data == "message_user"
)
async def message_user(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.set_state(
        ManageUser.waiting_message
    )


    await callback.message.answer(
"""
📩 Сообщение пользователю


Введите:

ID текст


Пример:

6312016802 Ваша подписка продлена
"""
    )


    await callback.answer()



@router.message(
ManageUser.waiting_message
)
async def send_message_user(
    message: Message,
    state: FSMContext
):

    data = message.text.split(
        " ",
        1
    )


    user_id = int(
        data[0]
    )

    text = data[1]



    await message.bot.send_message(
        user_id,
        text
    )


    await message.answer(
        "✅ Сообщение отправлено"
    )


    await state.clear()