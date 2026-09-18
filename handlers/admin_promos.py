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
# SAFE TEXT
# ============================================================

def normalize_code(text: str | None) -> str:
    if not text:
        return ""

    return text.strip().upper()


def is_cancel(text: str | None) -> bool:
    return (text or "").strip().lower() == "/cancel"


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
# CREATE / FIND / DISABLE — CODE
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

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

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

            promos = (
                get_all_promocodes()
                or []
            )

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

        found = None

        for promo in promos:

            if not isinstance(
                promo,
                dict,
            ):
                continue

            promo_code = str(
                promo.get("code")
                or ""
            ).strip().upper()

            if promo_code == code:

                found = promo
                break

        if not found:

            await message.answer(
                "❌ Промокод "
                f"<code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )

            return

        active = (
            "🟢