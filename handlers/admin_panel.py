from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID

from database import (
    get_stats,
    get_all_users,
    get_payments,
    get_user,
    remove_bs,
    activate_subscription
)

from github_update import create_subscription


router = Router()



# =====================
# ПРОВЕРКА АДМИНА
# =====================

def is_admin(user_id):

    return user_id == ADMIN_ID



# =====================
# АДМИНКА
# =====================

@router.message(Command("admin"))
async def admin_panel(message: Message):

    if not is_admin(message.from_user.id):

        await message.answer(
            "❌ Нет доступа"
        )

        return


    await message.answer(
"""
🛠 Орёл VPN — Админ панель


Выберите раздел:
""",
        reply_markup=admin_keyboard()
    )



# =====================
# КЛАВИАТУРА
# =====================

def admin_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data="admin_payments"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Рассылка",
                    callback_data="admin_broadcast"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎫 Промокоды",
                    callback_data="admin_promos"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⚙️ Управление",
                    callback_data="admin_manage"
                )
            ]

        ]
    )



# =====================
# СТАТИСТИКА
# =====================

@router.callback_query(
    F.data == "admin_stats"
)
async def stats(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return


    data = get_stats()


    await callback.message.answer(
f"""
📊 Статистика


👥 Пользователей:
{data['total']}


✅ Активных:
{data['active']}


🦅 Орёл VPN
"""
    )


    await callback.answer()



# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

@router.callback_query(
    F.data == "admin_users"
)
async def users(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return


    users = get_all_users()


    text = "👥 Последние пользователи:\n\n"


    for user in users[:20]:

        text += (
f"""
🆔 {user['user_id']}
👑 {user['tariff']}
📅 {user['subscription_until']}
📡 {user['status']}

"""
        )


    await callback.message.answer(
        text
    )


    await callback.answer()



# =====================
# ПЛАТЕЖИ
# =====================

@router.callback_query(
    F.data == "admin_payments"
)
async def payments(callback: CallbackQuery):

    if not is_admin(callback.from_user.id):
        return


    pays = get_payments()


    if not pays:

        await callback.message.answer(
            "💳 Платежей нет"
        )

        return



    text = "💳 Платежи:\n\n"


    for pay in pays:

        text += (
f"""
🧾 #{pay['id']}
👤 {pay['user_id']}
📅 {pay['days']} дней

"""
        )


    await callback.message.answer(
        text
    )


    await callback.answer()



# =====================
# ЗАГОТОВКИ
# =====================

@router.callback_query(
    F.data == "admin_broadcast"
)
async def broadcast(callback: CallbackQuery):

    await callback.message.answer(
        "📢 Рассылка: в разработке"
    )

    await callback.answer()



@router.callback_query(
    F.data == "admin_promos"
)
async def promos(callback: CallbackQuery):

    await callback.message.answer(
        "🎫 Промокоды: в разработке"
    )

    await callback.answer()



@router.callback_query(
    F.data == "admin_manage"
)
async def manage(callback: CallbackQuery):

    await callback.message.answer(
        """
⚙️ Управление


Скоро:

➕ Выдать подписку
➖ Отключить
⏳ Продлить
🔍 Найти пользователя
"""
    )

    await callback.answer()