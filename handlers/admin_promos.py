# handlers/admin_promos.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from config import ADMIN_IDS

from database import (
    create_promocode,
    get_promocode,
    get_all_promocodes,
    deactivate_promocode,
)


router = Router()


# ============================================================
# FSM
# ============================================================

class PromoStates(StatesGroup):
    waiting_code = State()
    waiting_days = State()
    waiting_max_uses = State()


# ============================================================
# ADMIN CHECK
# ============================================================

def is_admin(user_id: int) -> bool:
    return int(user_id) in ADMIN_IDS


# ============================================================
# MENU
# ============================================================

def promo_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать промокод",
                    callback_data="admin_promo_create",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Все промокоды",
                    callback_data="admin_promo_list",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Найти промокод",
                    callback_data="admin_promo_find",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Деактивировать",
                    callback_data="admin_promo_disable",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Админ-панель",
                    callback_data="admin_back",
                )
            ],
        ]
    )


# ============================================================
# HELPERS
# ============================================================

def normalize_code(text: str | None) -> str:
    if not text:
        return ""

    return text.strip().upper()


def is_cancel(text: str | None) -> bool:
    return (text or "").strip().lower() == "/cancel"


def promo_text(promo: dict) -> str:
    code = str(
        promo.get("code") or "—"
    )

    days = promo.get("days")

    max_uses = promo.get("max_uses")

    uses = promo.get("uses")

    active_value = promo.get("active")

    if active_value is True:
        status = "🟢 Активен"
    elif active_value is False:
        status = "🔴 Неактивен"
    else:
        status = "⚪ Статус неизвестен"

    if days is None:
        days_text = "—"
    else:
        days_text = str(days)

    if max_uses is None:
        max_uses_text = "∞"
    else:
        max_uses_text = str(max_uses)

    if uses is None:
        uses_text = "0"
    else:
        uses_text = str(uses)

    return (
        f"🎟 <b>{code}</b>\n\n"
        f"⏳ Дней: <b>{days_text}</b>\n"
        f"👥 Использований: <b>{uses_text}</b> / "
        f"<b>{max_uses_text}</b>\n"
        f"📌 {status}"
    )


# ============================================================
# /promos
# ============================================================

@router.message(Command("promos"))
async def promos_command(message: Message):

    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🎟 <b>Промокоды ixxy VPN</b>\n\n"
        "Выбери действие:",
        reply_markup=promo_menu(),
        parse_mode="HTML",
    )


# ============================================================
# BACK
# ============================================================

@router.callback_query(F.data == "admin_promo_back")
async def promo_back(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not callback.from_user or not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    if callback.message:
        await callback.message.edit_text(
            "🎟 <b>Промокоды ixxy VPN</b>\n\n"
            "Выбери действие:",
            reply_markup=promo_menu(),
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# CREATE START
# ============================================================

@router.callback_query(
    F.data == "admin_promo_create"
)
async def promo_create_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not callback.from_user or not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        PromoStates.waiting_code
    )

    await state.update_data(
        mode="create"
    )

    if callback.message:
        await callback.message.edit_text(
            "➕ <b>Создание промокода</b>\n\n"
            "Отправь код промокода.\n\n"
            "Например:\n"
            "<code>IXXY2026</code>\n\n"
            "Для отмены: /cancel",
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# FIND START
# ============================================================

@router.callback_query(
    F.data == "admin_promo_find"
)
async def promo_find_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not callback.from_user or not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        PromoStates.waiting_code
    )

    await state.update_data(
        mode="find"
    )

    if callback.message:
        await callback.message.edit_text(
            "🔎 <b>Поиск промокода</b>\n\n"
            "Отправь код промокода.\n\n"
            "Для отмены: /cancel",
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# DISABLE START
# ============================================================

@router.callback_query(
    F.data == "admin_promo_disable"
)
async def promo_disable_start(
    callback: CallbackQuery,
    state: FSMContext,
):

    if not callback.from_user or not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        PromoStates.waiting_code
    )

    await state.update_data(
        mode="disable"
    )

    if callback.message:
        await callback.message.edit_text(
            "❌ <b>Деактивация промокода</b>\n\n"
            "Отправь код промокода.\n\n"
            "Для отмены: /cancel",
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# CODE RECEIVED
# ============================================================

@router.message(
    PromoStates.waiting_code
)
async def promo_code_received(
    message: Message,
    state: FSMContext,
):

    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        await state.clear()
        return

    text = message.text or ""

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    if is_cancel(text):

        await state.clear()

        await message.answer(
            "❌ Операция отменена.",
            reply_markup=promo_menu(),
        )

        return

    code = normalize_code(text)

    if not code:

        await message.answer(
            "❌ Код не может быть пустым."
        )

        return

    if len(code) > 50:

        await message.answer(
            "❌ Код слишком длинный.\n"
            "Максимум 50 символов."
        )

        return

    data = await state.get_data()

    mode = data.get("mode")

    # ========================================================
    # FIND
    # ========================================================

    if mode == "find":

        await state.clear()

        try:

            promo = get_promocode(code)

        except Exception as e:

            print(
                "Promo find error:",
                repr(e),
            )

            await message.answer(
                "❌ Ошибка базы данных.",
                reply_markup=promo_menu(),
            )

            return

        if not promo:

            await message.answer(
                "❌ Промокод "
                f"<code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )

            return

        await message.answer(
            promo_text(promo),
            parse_mode="HTML",
            reply_markup=promo_menu(),
        )

        return

    # ========================================================
    # DISABLE
    # ========================================================

    if mode == "disable":

        await state.clear()

        try:

            promo = get_promocode(code)

            if not promo:

                await message.answer(
                    "❌ Промокод "
                    f"<code>{code}</code> не найден.",
                    parse_mode="HTML",
                    reply_markup=promo_menu(),
                )

                return

            result = deactivate_promocode(
                code
            )

            if result is False:

                await message.answer(
                    "❌ Не удалось деактивировать "
                    "промокод.",
                    reply_markup=promo_menu(),
                )

                return

        except Exception as e:

            print(
                "Promo disable error:",
                repr(e),
            )

            await message.answer(
                "❌ Ошибка базы данных.",
                reply_markup=promo_menu(),
            )

            return

        await message.answer(
            "✅ Промокод "
            f"<code>{code}</code> деактивирован.",
            parse_mode="HTML",
            reply_markup=promo_menu(),
        )

        return

    # ========================================================
    # CREATE
    # ========================================================

    if mode == "create":

        try:

            existing = get_promocode(
                code
            )

        except Exception as e:

            print(
                "Promo check error:",
                repr(e),
            )

            await message.answer(
                "❌ Ошибка базы данных."
            )

            return

        if existing:

            await message.answer(
                "❌ Такой промокод уже существует.\n"
                "Отправь другой код.",
            )

            return

        await state.update_data(
            code=code
        )

        await state.set_state(
            PromoStates.waiting_days
        )

        await message.answer(
            "⏳ <b>Срок действия</b>\n\n"
            "Сколько дней будет добавлять "
            "промокод?\n\n"
            "Например: <code>30</code>\n\n"
            "Для отмены: /cancel",
            parse_mode="HTML",
        )

        return


# ============================================================
# DAYS RECEIVED
# ============================================================

@router.message(
    PromoStates.waiting_days
)
async def promo_days_received(
    message: Message,
    state: FSMContext,
):

    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        await state.clear()
        return

    text = message.text or ""

    if is_cancel(text):

        await state.clear()

        await message.answer(
            "❌ Операция отменена.",
            reply_markup=promo_menu(),
        )

        return

    try:

        days = int(
            text.strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введи целое число дней.\n\n"
            "Например: <code>30</code>",
            parse_mode="HTML",
        )

        return

    if days <= 0:

        await message.answer(
            "❌ Количество дней должно быть "
            "больше 0."
        )

        return

    if days > 999999999999:

        await message.answer(
            "❌ Слишком большое количество дней."
        )

        return

    await state.update_data(
        days=days
    )

    await state.set_state(
        PromoStates.waiting_max_uses
    )

    await message.answer(
        "👥 <b>Лимит использований</b>\n\n"
        "Сколько раз можно использовать "
        "промокод?\n\n"
        "Напиши число.\n"
        "Например: <code>10</code>\n\n"
        "Или отправь <code>0</code> "
        "для неограниченного количества.\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML",
    )


# ============================================================
# MAX USES RECEIVED
# ============================================================

@router.message(
    PromoStates.waiting_max_uses
)
async def promo_max_uses_received(
    message: Message,
    state: FSMContext,
):

    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        await state.clear()
        return

    text = message.text or ""

    if is_cancel(text):

        await state.clear()

        await message.answer(
            "❌ Операция отменена.",
            reply_markup=promo_menu(),
        )

        return

    try:

        max_uses = int(
            text.strip()
        )

    except ValueError:

        await message.answer(
            "❌ Введи целое число.\n\n"
            "Например: <code>10</code>\n"
            "Или <code>0</code> для безлимита.",
            parse_mode="HTML",
        )

        return

    if max_uses < 0:

        await message.answer(
            "❌ Количество использований "
            "не может быть отрицательным."
        )

        return

    data = await state.get_data()

    code = data.get("code")
    days = data.get("days")

    if not code or not days:

        await state.clear()

        await message.answer(
            "❌ Данные создания промокода "
            "потеряны.",
            reply_markup=promo_menu(),
        )

        return

    # 0 = unlimited
    if max_uses == 0:
        db_max_uses = None
    else:
        db_max_uses = max_uses

    try:

        result = create_promocode(
            code=code,
            days=days,
            max_uses=db_max_uses,
        )

    except TypeError:

        # Совместимость с версиями database.py,
        # где max_uses может быть обязательным
        try:

            result = create_promocode(
                code,
                days,
                db_max_uses,
            )

        except Exception as e:

            print(
                "Promo create error:",
                repr(e),
            )

            await state.clear()

            await message.answer(
                "❌ Ошибка создания промокода.",
                reply_markup=promo_menu(),
            )

            return

    except Exception as e:

        print(
            "Promo create error:",
            repr(e),
        )

        await state.clear()

        await message.answer(
            "❌ Ошибка создания промокода.",
            reply_markup=promo_menu(),
        )

        return

    await state.clear()

    await message.answer(
        "✅ <b>Промокод создан!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n"
        f"⏳ Дней: <b>{days}</b>\n"
        f"👥 Лимит: "
        f"<b>{'∞' if db_max_uses is None else db_max_uses}</b>",
        parse_mode="HTML",
        reply_markup=promo_menu(),
    )


# ============================================================
# LIST
# ============================================================

@router.callback_query(
    F.data == "admin_promo_list"
)
async def promo_list(
    callback: CallbackQuery,
):

    if not callback.from_user or not is_admin(
        callback.from_user.id
    ):
        await callback.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    try:

        promos = (
            get_all_promocodes()
            or []
        )

    except Exception as e:

        print(
            "Promo list error:",
            repr(e),
        )

        await callback.answer(
            "❌ Ошибка базы данных.",
            show_alert=True,
        )

        return

    if not promos:

        text = (
            "📋 <b>Промокоды</b>\n\n"
            "Промокодов пока нет."
        )

    else:

        lines = [
            "📋 <b>Все промокоды</b>",
            "",
        ]

        for promo in promos:

            if not isinstance(
                promo,
                dict,
            ):
                continue

            code = str(
                promo.get("code") or "—"
            )

            days = promo.get("days")
            uses = promo.get("uses", 0)
            max_uses = promo.get("max_uses")
            active = promo.get("active")

            if active is True:
                status = "🟢"
            elif active is False:
                status = "🔴"
            else:
                status = "⚪"

            max_text = (
                "∞"
                if max_uses is None
                else str(max_uses)
            )

            lines.append(
                f"{status} <code>{code}</code> — "
                f"{days} дн. — "
                f"{uses}/{max_text}"
            )

        text = "\n".join(
            lines
        )

    if callback.message:

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=promo_menu(),
        )

    await callback.answer()