from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command

from config import ADMIN_ID

from database import (
    get_stats,
    get_all_users,
    get_payments
)

router = Router()

# =====================
# ПРОВЕРКА АДМИНА
# =====================

def check_admin(user_id):

    return user_id == ADMIN_ID

# =====================
# КОМАНДА /ADMIN
# =====================

@router.message(
    Command("admin")
)
async def admin(message: Message):

    if not check_admin(
        message.from_user.id
    ):

        await message.answer(
            "❌ Нет доступа"
        )

        return

    await message.answer(
"""
🦅 Orel VPN

🛠 Админ-панель

Выберите раздел:
""",
        reply_markup=admin_menu()
    )

# =====================
# ГЛАВНОЕ МЕНЮ
# =====================

def admin_menu():

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
                    text="⚙️ Управление",
                    callback_data="admin_manage"
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
            ]

        ]
    )

# =====================
# СТАТИСТИКА
# =====================

@router.callback_query(
    F.data == "admin_stats"
)
async def stats(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    data = get_stats()

    await callback.message.answer(
f"""
📊 Статистика Orel VPN

👥 Всего пользователей:
{data['total']}

✅ Активных:
{data['active']}

🦅 Сервис работает
"""
    )

    await callback.answer()

# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

@router.callback_query(
    F.data == "admin_users"
)
async def users(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    users = get_all_users()

    if not users:

        await callback.message.answer(
            "👥 Пользователей нет"
        )

        return

    text = """
👥 Последние пользователи:

"""

    for user in users[:15]:

        text += f"""
🆔 ID:
{user[0]}

👤 Username:
{user[1]}

👑 Тариф:
{user[2]}

📅 До:
{user[4]}

----------------
"""

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
async def payments(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    payments = get_payments()

    if not payments:

        await callback.message.answer(
            "💳 Платежей нет"
        )

        await callback.answer()

        return

    text = """
💳 Ожидающие платежи:

"""

    for pay in payments:

        text += f"""
🧾 Платёж #{pay[0]}

👤 ID:
{pay[1]}

📅 Дней:
{pay[3]}

----------------
"""

    await callback.message.answer(
        text
    )

    await callback.answer()

# =====================
# УПРАВЛЕНИЕ
# =====================

@router.callback_query(
    F.data == "admin_manage"
)
async def manage(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    await callback.message.answer(
"""
⚙️ Управление пользователями

Выберите действие:

👤 Поиск пользователя
➕ Выдать подписку
⏳ Продлить подписку
❌ Отключить подписку
📩 Написать пользователю
""",
        reply_markup=manage_menu()
    )

    await callback.answer()

def manage_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👤 Найти пользователя",
                    callback_data="find_user"
                )
            ],

            [
                InlineKeyboardButton(
                    text="➕ Выдать подписку",
                    callback_data="give_subscription"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data="extend_subscription"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data="disable_subscription"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back"
                )
            ]

        ]
    )

# =====================
# РАССЫЛКА
# =====================

@router.callback_query(
    F.data == "admin_broadcast"
)
async def broadcast(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    await callback.message.answer(
"""
📢 Рассылка

Выберите группу:

👥 Всем пользователям
👑 Только VIP
🎁 Только пробники
⚠️ Скоро закончится
""",
        reply_markup=broadcast_menu()
    )

    await callback.answer()

def broadcast_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👥 Всем",
                    callback_data="broadcast_all"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👑 VIP",
                    callback_data="broadcast_vip"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎁 Пробники",
                    callback_data="broadcast_trial"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back"
                )
            ]

        ]
    )

# =====================
# ПРОМОКОДЫ
# =====================

@router.callback_query(
    F.data == "admin_promos"
)
async def promos(
    callback: CallbackQuery
):

    if not check_admin(
        callback.from_user.id
    ):
        return

    await callback.message.answer(
"""
🎫 Промокоды

Действия:

➕ Создать промокод
📋 Список промокодов
🗑 Удалить промокод
""",
        reply_markup=promo_menu()
    )

    await callback.answer()

def promo_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Создать",
                    callback_data="create_promo"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📋 Список",
                    callback_data="list_promo"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data="delete_promo"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back"
                )
            ]

        ]
    )

# =====================
# НАЗАД В МЕНЮ
# =====================

@router.callback_query(
    F.data == "admin_back"
)
async def admin_back(
    callback: CallbackQuery
):

    await callback.message.edit_text(
"""
🦅 Orel VPN

🛠 Админ-панель

Выберите раздел:
""",
        reply_markup=admin_menu()
    )

    await callback.answer()