from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# ============================================================
# НАСТРОЙКИ
# ============================================================

PUBLIC_SITE_URL = (
    "https://orelvpnrailoh-1.onrender.com"
)

SUBSCRIPTION_PREFIX = "2ix847xy"


# ============================================================
# ССЫЛКА НА СТРАНИЦУ ПОДПИСКИ
# ============================================================

def get_subscription_site_url(user_id: int):

    return (
        f"{PUBLIC_SITE_URL}"
        f"/s/"
        f"{SUBSCRIPTION_PREFIX}"
        f"{user_id}"
    )


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def main_menu(user_id: int):

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
                    text="🔌 Подключиться"
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

def cabinet_keyboard(user_id: int):

    subscription_url = get_subscription_site_url(
        user_id
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔌 Подключиться",
                    url=subscription_url
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
# ДОКУМЕНТЫ / СОГЛАСИЕ
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