from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def main_menu(user_id=None):

    webapp_button = KeyboardButton(
        text="🌐 Моя подписка",
        web_app=WebAppInfo(
            url=(
                "https://orelvpnrailoh-1.onrender.com"
                f"/s/2ix847xy{user_id}"
            )
        ) if user_id else None
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👤 Личный кабинет"
                ),
                KeyboardButton(
                    text="🎫 Купить подписку"
                ),
            ],
            [
                KeyboardButton(
                    text="🎁 Пробный период"
                ),
                webapp_button,
            ],
            [
                KeyboardButton(
                    text="💬 Поддержка"
                ),
                KeyboardButton(
                    text="📄 Документы"
                ),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


# ============================================================
# КАБИНЕТ
# ============================================================

def cabinet_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 Моя подписка",
                    url="https://orelvpnrailoh-1.onrender.com"
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
                    text="🔗 Получить ссылку",
                    callback_data="get_link"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎟 Ввести промокод",
                    callback_data="enter_promo"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💳 Продлить подписку",
                    callback_data="renew"
                )
            ],
        ]
    )


# ============================================================
# ОПЛАТА
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
                    text="1 месяц — ⭐ 70",
                    callback_data="stars_30"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца — ⭐ 190",
                    callback_data="stars_90"
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев — ⭐ 350",
                    callback_data="stars_180"
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев — ⭐ 700",
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
                    text="1 месяц",
                    callback_data="sbp_30"
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца",
                    callback_data="sbp_90"
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев",
                    callback_data="sbp_180"
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев",
                    callback_data="sbp_365"
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
                    text="📄 Условия",
                    url="https://bdtvyz76b6-blip.github.io/managerorlvpnsite/"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Принимаю",
                    callback_data="accept_terms"
                )
            ],
        ]
    )