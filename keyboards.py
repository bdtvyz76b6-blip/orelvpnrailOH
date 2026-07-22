from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# =====================
# ГЛАВНОЕ МЕНЮ
# =====================

def main_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🆓 Wi-Fi"),
                KeyboardButton(text="👑 Обход Б/С")
            ],
            [
                KeyboardButton(text="👤 Личный кабинет")
            ],
            [
                KeyboardButton(text="💬 Поддержка")
            ]
        ],
        resize_keyboard=True
    )



# =====================
# АДМИН МЕНЮ
# =====================

def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(text="👥 Пользователи")
            ],

            [
                KeyboardButton(text="📊 Статистика")
            ],

            [
                KeyboardButton(text="💳 Заявки")
            ],

            [
                KeyboardButton(text="📢 Рассылка")
            ],

            [
                KeyboardButton(text="🎁 Промокоды")
            ],

            [
                KeyboardButton(text="⚙️ Настройки")
            ],

            [
                KeyboardButton(text="⬅️ Назад")
            ]

        ],
        resize_keyboard=True
    )



# =====================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =====================

def users_keyboard(users):

    buttons = []


    for user in users:

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"👤 {user[1]} | {user[0]}",
                    callback_data=f"user_{user[0]}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )



# =====================
# КАРТОЧКА ЮЗЕРА
# =====================

def user_card_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👑 Выдать Обход Б/С",
                    callback_data=f"give_bs_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Забрать Обход Б/С",
                    callback_data=f"remove_bs_{user_id}"
                )
            ]

        ]
    )



# =====================
# ПОКУПКА
# =====================

def buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 Купить Обход Б/С",
                    callback_data="buy_bs"
                )
            ]

        ]
    )