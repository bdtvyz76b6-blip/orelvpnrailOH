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
                KeyboardButton(
                    text="👑 Купить подписку"
                )
            ],

            [
                KeyboardButton(
                    text="🎁 Пробный период"
                )
            ],

            [
                KeyboardButton(
                    text="👤 Личный кабинет"
                )
            ],

            [
                KeyboardButton(
                    text="💬 Поддержка"
                )
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
                KeyboardButton(
                    text="👥 Пользователи"
                )
            ],

            [
                KeyboardButton(
                    text="📊 Статистика"
                )
            ],

            [
                KeyboardButton(
                    text="💳 Заявки"
                )
            ],

            [
                KeyboardButton(
                    text="📢 Рассылка"
                )
            ],

            [
                KeyboardButton(
                    text="🎁 Промокоды"
                )
            ],

            [
                KeyboardButton(
                    text="⚙️ Настройки"
                )
            ],

            [
                KeyboardButton(
                    text="⬅️ Назад"
                )
            ]

        ],
        resize_keyboard=True
    )

# =====================
# ТАРИФЫ
# =====================

def buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📅 7 дней — 35₽",
                    callback_data="buy_7"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 30 дней — 85₽",
                    callback_data="buy_30"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 90 дней — 245₽",
                    callback_data="buy_90"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📅 365 дней — 605₽",
                    callback_data="buy_365"
                )
            ]

        ]
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
# КАРТОЧКА ПОЛЬЗОВАТЕЛЯ
# =====================

def user_card_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="👑 Выдать подписку",
                    callback_data=f"give_sub_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Забрать подписку",
                    callback_data=f"remove_sub_{user_id}"
                )
            ]

        ]
    )

# =====================
# ОПЛАТА
# =====================

def payment_menu(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ Выдать подписку",
                    callback_data=f"approve_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_{user_id}"
                )
            ]

        ]
    )

# =====================
# ПРОМОКОДЫ
# =====================

def promo_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="➕ Создать промокод",
                    callback_data="create_promo"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📋 Список промокодов",
                    callback_data="list_promo"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Удалить промокод",
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
# РАССЫЛКА
# =====================

def broadcast_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✏️ Создать сообщение",
                    callback_data="create_broadcast"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Отправить всем",
                    callback_data="send_broadcast"
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