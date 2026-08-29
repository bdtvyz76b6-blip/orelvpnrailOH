from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
                    text="💬 Поддержка"
                )
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
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
            ],
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
            ],
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
            ],
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
                    text="⚡ Подключиться",
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
            ],
        ]
    )


# ============================================================
# ПРИНЯТИЕ УСЛОВИЙ
# ============================================================

def accept_terms_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принимаю",
                    callback_data="accept_terms"
                )
            ],
        ]
    )