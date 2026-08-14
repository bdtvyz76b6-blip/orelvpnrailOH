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
                    text="📄 Документы"
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
# СПОСОБ ОПЛАТЫ
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
                    text="💳 СБП",
                    callback_data="pay_sbp"
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
                    text="⭐ 1 месяц — 70 Stars",
                    callback_data="stars_30"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 3 месяца — 190 Stars",
                    callback_data="stars_90"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 6 месяцев — 350 Stars",
                    callback_data="stars_180"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 12 месяцев — 700 Stars",
                    callback_data="stars_365"
                )
            ]

        ]
    )



# =====================
# СБП ТАРИФЫ
# =====================

def sbp_buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💳 1 месяц — 99₽",
                    callback_data="sbp_30"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 3 месяца — 249₽",
                    callback_data="sbp_90"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 6 месяцев — 599₽",
                    callback_data="sbp_180"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💳 12 месяцев — 999₽",
                    callback_data="sbp_365"
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
                    text="🔗 Получить ссылку",
                    callback_data="get_link"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔄 Обновить серверы",
                    callback_data="refresh_subscription"
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
# АДМИН ПАНЕЛЬ
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
# ПРИНЯТИЕ УСЛОВИЙ
# =====================

def accept_terms_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📄 Документы",
                    url="https://bdtvyz76b6-blip.github.io/managerorlvpnsite/"
                )
            ],

            [
                InlineKeyboardButton(
                    text="✅ Принимаю",
                    callback_data="accept_terms"
                )
            ]

        ]
    )