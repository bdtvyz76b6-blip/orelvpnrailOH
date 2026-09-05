from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            # ==================================================
            # СТАТИСТИКА
            # ==================================================

            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats",
                )
            ],

            # ==================================================
            # ПОЛЬЗОВАТЕЛИ
            # ==================================================

            [
                InlineKeyboardButton(
                    text="👥 Пользователи",
                    callback_data="admin_users",
                )
            ],

            # ==================================================
            # ПОИСК
            # ==================================================

            [
                InlineKeyboardButton(
                    text="🔎 Найти пользователя",
                    callback_data="admin_search",
                )
            ],

            # ==================================================
            # ПЛАТЕЖИ
            # ==================================================

            [
                InlineKeyboardButton(
                    text="💳 Платежи",
                    callback_data="admin_payments",
                )
            ],

            # ==================================================
            # ПРОМОКОДЫ
            # ==================================================

            [
                InlineKeyboardButton(
                    text="🎟 Промокоды",
                    callback_data="admin_promos",
                )
            ],

            # ==================================================
            # РАССЫЛКА
            # ==================================================

            [
                InlineKeyboardButton(
                    text="📢 Рассылка",
                    callback_data="admin_broadcast",
                )
            ],

            # ==================================================
            # СЕРВЕРЫ
            # ==================================================

            [
                InlineKeyboardButton(
                    text="🔄 Обновить серверы",
                    callback_data="admin_sync_servers",
                )
            ],

        ]
    )