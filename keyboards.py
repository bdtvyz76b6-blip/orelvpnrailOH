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
                    text="🎫 Купить подписку"
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
# ВЫБОР ОПЛАТЫ
# =====================

def payment_method_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⭐ Telegram Stars",
                    callback_data="pay_stars"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 Перевод",
                    callback_data="pay_transfer"
                )
            ]

        ]
    )





# =====================
# STARS ТАРИФЫ
# =====================

def stars_buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⭐ 1 месяц — 70",
                    callback_data="stars_30"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 3 месяца — 190",
                    callback_data="stars_90"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 6 месяцев — 350",
                    callback_data="stars_180"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 12 месяцев — 700",
                    callback_data="stars_365"
                )
            ]

        ]
    )





# =====================
# ПЕРЕВОД ТАРИФЫ
# =====================

def transfer_buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 1 месяц — 70₽",
                    callback_data="transfer_30"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 3 месяца — 190₽",
                    callback_data="transfer_90"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 6 месяцев — 350₽",
                    callback_data="transfer_180"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 12 месяцев — 700₽",
                    callback_data="transfer_365"
                )
            ]

        ]
    )





# =====================
# ЛИЧНЫЙ КАБИНЕТ
# =====================

def cabinet_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="refresh_cabinet"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔗 Получить ссылку",
                    callback_data="get_link"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎫 Продлить",
                    callback_data="renew"
                )
            ]

        ]
    )





# =====================
# АДМИНКА
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
# ДЕЙСТВИЯ С ПОЛЬЗОВАТЕЛЕМ
# =====================

def user_actions(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🎫 Выдать подписку",
                    callback_data=f"give_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=f"extend_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=f"disable_{user_id}"
                )
            ]

        ]
    )