from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Найти пользователя",
                    callback_data="admin_search"
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
                    text="🎟 Промокоды",
                    callback_data="admin_promos"
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
                    text="📊 Статистика",
                    callback_data="admin_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить серверы",
                    callback_data="admin_sync_servers"
                )
            ]
        ]
    )