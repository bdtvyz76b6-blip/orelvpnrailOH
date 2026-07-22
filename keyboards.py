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




# =====================
# АДМИН МЕНЮ
# =====================

def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(text="👥 Пользователи")
            ],

            [
                KeyboardButton(text="📊 Статистика")
            ],

            [
                KeyboardButton(text="💳 Заявки")
            ],

            [
                KeyboardButton(text="📢 Рассылка")
            ],

            [
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




# =====================
# ПОЛЬЗОВАТЕЛИ
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
# КАРТОЧКА ЮЗЕРА
# =====================

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

            ]

        ]

    )





# =====================
# ПОКУПКА
# =====================

def buy_keyboard():

    return InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(
                    text="💳 Купить Обход Б/С",
                    callback_data="buy_bs"
                )

            ]

        ]

    )





# =====================
# МЕНЮ ПРОМОКОДОВ
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





# =====================
# ЗАЯВКА ОПЛАТЫ
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