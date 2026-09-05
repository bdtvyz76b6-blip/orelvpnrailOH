from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_IDS

router = Router()


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# КЛАВИАТУРА НАСТРОЕК
# ============================================================

def settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💰 Цены",
                    callback_data="settings_prices"
                ),
                InlineKeyboardButton(
                    text="🏦 СБП",
                    callback_data="settings_sbp"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🤖 /start",
                    callback_data="settings_start"
                ),
                InlineKeyboardButton(
                    text="📢 Канал",
                    callback_data="settings_channel"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Поддержка",
                    callback_data="settings_support"
                ),
                InlineKeyboardButton(
                    text="🎁 Пробный период",
                    callback_data="settings_trial"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔔 Уведомления",
                    callback_data="settings_notify"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data="admin_settings"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back"
                ),
            ],
        ]
    )


# ============================================================
# ГЛАВНОЕ МЕНЮ НАСТРОЕК
# ============================================================

@router.callback_query(F.data == "admin_settings")
async def settings(call: CallbackQuery):

    if not call.from_user:
        return

    if not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

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

    try:
        await call.message.edit_text(
            text,
            reply_markup=settings_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        print("Admin settings error:", repr(e))

    await call.answer()


# ============================================================
# ЗАГОТОВКА: ЦЕНЫ
# ============================================================

@router.callback_query(F.data == "settings_prices")
async def settings_prices(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "💰 Раздел цен пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: СБП
# ============================================================

@router.callback_query(F.data == "settings_sbp")
async def settings_sbp(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "🏦 Раздел СБП пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: START
# ============================================================

@router.callback_query(F.data == "settings_start")
async def settings_start(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "🤖 Редактор /start пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: КАНАЛ
# ============================================================

@router.callback_query(F.data == "settings_channel")
async def settings_channel(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "📢 Настройка канала пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: ПОДДЕРЖКА
# ============================================================

@router.callback_query(F.data == "settings_support")
async def settings_support(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "👨‍💻 Настройка поддержки пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: ПРОБНЫЙ ПЕРИОД
# ============================================================

@router.callback_query(F.data == "settings_trial")
async def settings_trial(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "🎁 Настройка пробного периода пока подключается",
        show_alert=True
    )


# ============================================================
# ЗАГОТОВКА: УВЕДОМЛЕНИЯ
# ============================================================

@router.callback_query(F.data == "settings_notify")
async def settings_notify(call: CallbackQuery):

    if not call.from_user or not is_admin(call.from_user.id):
        await call.answer(
            "❌ Нет доступа",
            show_alert=True
        )
        return

    await call.answer(
        "🔔 Настройка уведомлений пока подключается",
        show_alert=True
    )