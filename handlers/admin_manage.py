from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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

class Manage(StatesGroup):

    user_id = State()

    days = State()

    message = State()



# =====================
# ПРОВЕРКА АДМИНА
# =====================

def admin(user_id):

    return user_id == ADMIN_ID



# =====================
# НАЧАЛО
# =====================

@router.callback_query(
    F.data == "admin_manage"
)
async def start_manage(callback: CallbackQuery, state: FSMContext):

    if not admin(callback.from_user.id):
        return


    await state.set_state(
        Manage.user_id
    )


    await callback.message.answer(
        """
⚙️ Управление пользователем


Введите Telegram ID:
"""
    )


    await callback.answer()



# =====================
# ПОИСК
# =====================

@router.message(
    Manage.user_id
)
async def find_user(message: Message, state: FSMContext):

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
        target=user_id
    )


    await message.answer(
f"""
👤 Пользователь


🆔 ID:
{user['user_id']}


👑 Тариф:
{user['tariff']}


📅 До:
{user['subscription_until']}


📡 Статус:
{user['status']}
""",
        reply_markup=user_actions()
    )


    await state.clear()



# =====================
# КНОПКИ
# =====================

def user_actions():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Выдать VIP",
                    callback_data="give_vip"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data="extend_sub"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data="disable_sub"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📩 Написать",
                    callback_data="write_user"
                )
            ]

        ]
    )



# =====================
# ВЫДАТЬ VIP
# =====================

@router.callback_query(
    F.data == "give_vip"
)
async def give_vip(callback: CallbackQuery):

    await callback.message.answer(
        """
Введите:

ID пользователя + количество дней

Пример:

6312016802 30
"""
    )


    await callback.answer()



@router.message(
    F.text.regexp(r"^\d+\s\d+$")
)
async def give_process(message: Message):

    if not admin(message.from_user.id):
        return


    data = message.text.split()


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
🎉 Вам выдана подписка Орёл VPN


⏳ Срок:
{days} дней


🔗 Ссылка:

{link}
"""
    )



# =====================
# ОТКЛЮЧИТЬ
# =====================

@router.callback_query(
    F.data == "disable_sub"
)
async def disable_sub(callback: CallbackQuery):

    await callback.message.answer(
        """
Введите ID пользователя для отключения:
"""
    )


    await callback.answer()



@router.message(
    F.text.regexp(r"^\d+$")
)
async def disable_process(message: Message):

    if not admin(message.from_user.id):
        return


    user_id = int(
        message.text
    )


    user = get_user(
        user_id
    )


    if not user:

        await message.answer(
            "❌ Пользователь не найден"
        )

        return



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