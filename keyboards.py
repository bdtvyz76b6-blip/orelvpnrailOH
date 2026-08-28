from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def main_menu(user_id=None):

    keyboard = [
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
        ]
    ]

    # ========================================================
    # МОЯ ПОДПИСКА — TELEGRAM MINI APP
    # ========================================================

    if user_id:

        subscription_url = (
            "https://orelvpnrailoh-1.onrender.com"
            f"/s/2ix847xy{user_id}"
        )

        keyboard.append(
            [
                KeyboardButton(
                    text="🌐 Моя подписка",
                    web_app=WebAppInfo(
                        url=subscription_url
                    )
                )
            ]
        )

    else:

        keyboard.append(
            [
                KeyboardButton(
                    text="🌐 Моя подписка"
                )
            ]
        )

    # ========================================================
    # ОСТАЛЬНЫЕ КНОПКИ
    # ========================================================

    keyboard.extend([
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
    ])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


# ============================================================
# СПОСОБ ОПЛАТЫ
# ============================================================

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


# ============================================================
# TELEGRAM STARS
# ============================================================

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


# ============================================================
# СБП
# ============================================================

def sbp_buy_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 1 месяц — 129₽",
                    callback_data="sbp_30"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 3 месяца — 379₽",
                    callback_data="sbp_90"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 6 месяцев — 659₽",
                    callback_data="sbp_180"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 12 месяцев — 1089₽",
                    callback_data="sbp_365"
                )
            ]
        ]
    )


# ============================================================
# ЛИЧНЫЙ КАБИНЕТ
# ============================================================

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
                    text="🎟 Промокод",
                    callback_data="enter_promo"
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


# ============================================================
# СОГЛАШЕНИЕ
# ============================================================

def accept_terms_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Документы",
                    url=(
                        "https://bdt2010.github.io/"
                        "managerorlvpnsite/"
                    )
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