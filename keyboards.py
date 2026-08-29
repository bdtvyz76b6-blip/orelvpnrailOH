from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


# ============================================================
# НАЗАД
# ============================================================

def back_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Назад",
                    callback_data="back"
                )
            ]
        ]
    )


# ============================================================
# ОТМЕНА
# ============================================================

def cancel_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel"
                )
            ]
        ]
    )


# ============================================================
# НАЗАД В МЕНЮ
# ============================================================

def menu_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏠 Главное меню",
                    callback_data="main_menu"
                )
            ]
        ]
    )