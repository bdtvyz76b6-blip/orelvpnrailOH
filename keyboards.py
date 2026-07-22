from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# =========================
# ГЛАВНОЕ МЕНЮ ПОЛЬЗОВАТЕЛЯ
# =========================

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


# =========================
# БОЛЬШАЯ АДМИНКА
# =========================

def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(text="👥 Пользователи"),
                KeyboardButton(text="💳 Заявки")
            ],

            [
                KeyboardButton(text="📊 Статистика"),
                KeyboardButton(text="📢 Рассылка")
            ],

            [
                KeyboardButton(text="🔗 Подписки"),
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


# =========================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =========================

def users_keyboard(users):

    buttons = []


    for user in users:

        username = user[1] or "без username"


        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"👤 @{username}",
                    callback_data=f"user_{user[0]}"
                )
            ]
        )


    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )



# =========================
# КАРТОЧКА ПОЛЬЗОВАТЕЛЯ
# =========================

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
            ],

            [
                InlineKeyboardButton(
                    text="📩 Написать",
                    callback_data=f"message_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=f"delete_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_users"
                )
            ]

        ]
    )



# =========================
# ПОКУПКА ОБХОД Б/С
# =========================

def buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👑 Купить Обход Б/С",
                    callback_data="buy_bs"
                )
            ]

        ]
    )



# =========================
# ПОДТВЕРЖДЕНИЕ ОПЛАТЫ
# =========================

def approve_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"give_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"deny_{user_id}"
                )
            ]

        ]
    ) 