from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "admin_settings")
async def settings(call: CallbackQuery):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💰 Цены",
                    callback_data="settings_prices"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏦 СБП",
                    callback_data="settings_sbp"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🤖 Текст /start",
                    callback_data="settings_start"
                )
            ],

            [
                InlineKeyboardButton(
                    text="📢 Канал",
                    callback_data="settings_channel"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👨‍💻 Поддержка",
                    callback_data="settings_support"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🎁 Пробный период",
                    callback_data="settings_trial"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔔 Уведомления",
                    callback_data="settings_notify"
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

    await call.message.edit_text(
        "⚙️ Настройки",
        reply_markup=keyboard
    )