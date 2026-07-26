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
# ДОКУМЕНТЫ
# =====================

def documents_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📄 Пользовательское соглашение",
                    url="https://ТВОЙ_САЙТ.github.io/terms.html"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔒 Политика конфиденциальности",
                    url="https://ТВОЙ_САЙТ.github.io/privacy.html"
                )
            ]

        ]
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
# ПЕРЕВОД
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