from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import ADMIN_IDS


router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    try:
        return int(user_id) in ADMIN_IDS
    except (TypeError, ValueError):
        return False


# ============================================================
# КЛАВИАТУРА НАСТРОЕК
# ============================================================

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Цены",
                    callback_data="settings_prices",
                ),
                InlineKeyboardButton(
                    text="🏦 СБП",
                    callback_data="settings_sbp",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 /start",
                    callback_data="settings_start",
                ),
                InlineKeyboardButton(
                    text="📢 Канал",
                    callback_data="settings_channel",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Поддержка",
                    callback_data="settings_support",
                ),
                InlineKeyboardButton(
                    text="🎁 Пробный период",
                    callback_data="settings_trial",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔔 Уведомления",
                    callback_data="settings_notify",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="admin_settings",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                ),
            ],
        ]
    )


# ============================================================
# ВСПОМОГАТЕЛЬНОЕ
# ============================================================

async def check_admin(call: CallbackQuery) -> bool:
    if not call.from_user:
        return False

    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True,
        )
        return False

    return True


async def show_settings(call: CallbackQuery):
    text = (
        "⚙️ <b>Настройки ixxy VPN</b>\n\n"
        "Здесь можно управлять основными параметрами бота.\n\n"
        "💰 <b>Цены</b> — тарифы и стоимость подписок\n"
        "🏦 <b>СБП</b> — настройки оплаты\n"
        "🤖 <b>/start</b> — приветственный текст\n"
        "📢 <b>Канал</b> — Telegram-канал проекта\n"
        "👨‍💻 <b>Поддержка</b> — контакт поддержки\n"
        "🎁 <b>Пробный период</b> — параметры trial\n"
        "🔔 <b>Уведомления</b> — уведомления пользователей\n\n"
        "👇 <b>Выберите раздел:</b>"
    )

    if call.message:
        try:
            await call.message.edit_text(
                text,
                reply_markup=settings_keyboard(),
                parse_mode="HTML",
            )
        except Exception as e:
            error = str(e).lower()

            # Если сообщение уже содержит такой же текст
            if "message is not modified" not in error:
                print(
                    "Admin settings error:",
                    repr(e),
                )


# ============================================================
# ГЛАВНОЕ МЕНЮ НАСТРОЕК
# ============================================================

@router.callback_query(F.data == "admin_settings")
async def settings(call: CallbackQuery):

    if not await check_admin(call):
        return

    await show_settings(call)
    await call.answer()


# ============================================================
# ЦЕНЫ
# ============================================================

@router.callback_query(F.data == "settings_prices")
async def settings_prices(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "💰 <b>Цены ixxy VPN</b>\n\n"
        "⭐ <b>Telegram Stars:</b>\n"
        "• 1 месяц — 70 Stars\n"
        "• 3 месяца — 190 Stars\n"
        "• 6 месяцев — 350 Stars\n"
        "• 12 месяцев — 700 Stars\n\n"
        "💳 <b>СБП:</b>\n"
        "• 1 месяц — 129₽\n"
        "• 3 месяца — 379₽\n"
        "• 6 месяцев — 659₽\n"
        "• 12 месяцев — 1089₽\n\n"
        "⚙️ Редактор цен пока не подключён."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# СБП
# ============================================================

@router.callback_query(F.data == "settings_sbp")
async def settings_sbp(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "🏦 <b>Настройки СБП</b>\n\n"
        "Платёжная система: <b>CashEra</b>\n\n"
        "💳 Доступные тарифы:\n"
        "• 1 месяц — 129₽\n"
        "• 3 месяца — 379₽\n"
        "• 6 месяцев — 659₽\n"
        "• 12 месяцев — 1089₽\n\n"
        "⚙️ Изменение настроек СБП пока не подключено."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# START
# ============================================================

@router.callback_query(F.data == "settings_start")
async def settings_start(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "🤖 <b>Настройки /start</b>\n\n"
        "Здесь можно будет изменить приветственное сообщение "
        "при запуске бота.\n\n"
        "⚙️ Редактор /start пока не подключён."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# КАНАЛ
# ============================================================

@router.callback_query(F.data == "settings_channel")
async def settings_channel(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "📢 <b>Telegram-канал</b>\n\n"
        "Раздел предназначен для настройки канала ixxy VPN.\n\n"
        "⚙️ Настройка канала пока не подключена."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# ПОДДЕРЖКА
# ============================================================

@router.callback_query(F.data == "settings_support")
async def settings_support(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "👨‍💻 <b>Поддержка ixxy VPN</b>\n\n"
        "Текущий контакт поддержки:\n"
        "👉 @orelvpntopbot\n\n"
        "⚙️ Редактор контакта пока не подключён."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# ПРОБНЫЙ ПЕРИОД
# ============================================================

@router.callback_query(F.data == "settings_trial")
async def settings_trial(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "🎁 <b>Пробный период</b>\n\n"
        "Здесь будут настраиваться параметры бесплатного "
        "пробного периода для новых пользователей.\n\n"
        "⚙️ Редактор trial пока не подключён."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()


# ============================================================
# УВЕДОМЛЕНИЯ
# ============================================================

@router.callback_query(F.data == "settings_notify")
async def settings_notify(call: CallbackQuery):

    if not await check_admin(call):
        return

    text = (
        "🔔 <b>Уведомления</b>\n\n"
        "Здесь будут настраиваться уведомления пользователей:\n\n"
        "• ⏳ Скоро закончится подписка\n"
        "• 🔴 Подписка истекла\n"
        "• 💳 Успешная оплата\n"
        "• 🎁 Получен пробный период\n\n"
        "⚙️ Редактор уведомлений пока не подключён."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_settings",
                )
            ]
        ]
    )

    if call.message:
        await call.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    await call.answer()