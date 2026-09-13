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
    return user_id in ADMIN_IDS


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
        ]
    )


# ============================================================
# /promos
# ============================================================

@router.message(Command("promos"))
async def promos_command(message: Message):
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
async def promo_back(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await callback.message.edit_text(
        "🎟 <b>Промокоды ixxy VPN</b>\n\n"
        "Выбери действие:",
        reply_markup=promo_menu(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# CREATE
# ============================================================

@router.callback_query(F.data == "admin_promo_create")
async def promo_create_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(PromoStates.waiting_code)

    await callback.message.edit_text(
        "➕ <b>Создание промокода</b>\n\n"
        "Отправь код промокода.\n\n"
        "Например:\n"
        "<code>IXXY2026</code>",
        parse_mode="HTML",
    )

    await callback.answer()


@router.message(PromoStates.waiting_code)
async def promo_code_received(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    code = message.text.strip().upper()

    if not code:
        await message.answer("❌ Код не может быть пустым.")
        return

    if len(code) > 50:
        await message.answer("❌ Код слишком длинный. Максимум 50 символов.")
        return

    existing = get_promocode(code)

    if existing:
        await message.answer(
            "❌ Такой активный промокод уже существует.\n\n"
            f"Код: <code>{code}</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(code=code)
    await state.set_state(PromoStates.waiting_days)

    await message.answer(
        "⏳ Теперь отправь количество дней подписки.\n\n"
        "Например:\n"
        "<code>30</code>",
        parse_mode="HTML",
    )


@router.message(PromoStates.waiting_days)
async def promo_days_received(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи число. Например: <code>30</code>", parse_mode="HTML")
        return

    if days <= 0:
        await message.answer("❌ Количество дней должно быть больше 0.")
        return

    if days > 999999999:
        await message.answer("❌ Слишком большое количество дней.")
        return

    await state.update_data(days=days)
    await state.set_state(PromoStates.waiting_max_uses)

    await message.answer(
        "🔢 Теперь укажи максимальное количество использований.\n\n"
        "Например:\n"
        "<code>10</code>\n\n"
        "Или отправь <code>0</code>, если количество использований не ограничено.",
        parse_mode="HTML",
    )


@router.message(PromoStates.waiting_max_uses)
async def promo_max_uses_received(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    try:
        max_uses = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Введи число. Например: <code>10</code>",
            parse_mode="HTML",
        )
        return

    if max_uses < 0:
        await message.answer("❌ Количество использований не может быть отрицательным.")
        return

    data = await state.get_data()

    code = data["code"]
    days = data["days"]

    success = create_promocode(
        code=code,
        days=days,
        max_uses=max_uses,
    )

    await state.clear()

    if not success:
        await message.answer(
            "❌ Не удалось создать промокод.\n"
            "Возможно, такой код уже существует."
        )
        return

    limit_text = (
        "♾ Без ограничений"
        if max_uses == 0
        else str(max_uses)
    )

    await message.answer(
        "✅ <b>Промокод создан!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n"
        f"⏳ Дней: <b>{days}</b>\n"
        f"🔢 Лимит: <b>{limit_text}</b>",
        parse_mode="HTML",
        reply_markup=promo_menu(),
    )


# ============================================================
# LIST
# ============================================================

@router.callback_query(F.data == "admin_promo_list")
async def promo_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    promos = get_all_promocodes()

    if not promos:
        await callback.message.edit_text(
            "📋 <b>Промокодов пока нет.</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="admin_promo_back",
                        )
                    ]
                ]
            ),
        )
        await callback.answer()
        return

    text = "📋 <b>Промокоды ixxy VPN</b>\n\n"

    for promo in promos:
        code = promo.get("code", "")
        days = promo.get("days", 0)
        uses = promo.get("uses", 0)
        max_uses = promo.get("max_uses", 0)
        active = promo.get("active", False)

        status = "🟢" if active else "🔴"

        if max_uses == 0:
            usage = f"{uses}/∞"
        else:
            usage = f"{uses}/{max_uses}"

        text += (
            f"{status} <code>{code}</code>\n"
            f"   ⏳ {days} дней\n"
            f"   🔢 Использований: {usage}\n\n"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_promo_back",
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    await callback.answer()


# ============================================================
# FIND
# ============================================================

@router.callback_query(F.data == "admin_promo_find")
async def promo_find_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(PromoStates.waiting_code)

    await callback.message.edit_text(
        "🔎 Отправь код промокода:",
        parse_mode="HTML",
    )

    await state.update_data(find_mode=True)

    await callback.answer()


# ============================================================
# DISABLE
# ============================================================

@router.callback_query(F.data == "admin_promo_disable")
async def promo_disable_start(
    callback: CallbackQuery,
    state: FSMContext,
):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(PromoStates.waiting_code)

    await state.update_data(disable_mode=True)

    await callback.message.edit_text(
        "❌ <b>Деактивация промокода</b>\n\n"
        "Отправь код, который нужно деактивировать.",
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# SPECIAL CODE HANDLER
# ============================================================

@router.message(PromoStates.waiting_code)
async def promo_special_code_handler(
    message: Message,
    state: FSMContext,
):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()

    # Если это создание — обработчик ниже не должен сюда попадать.
    if not data.get("find_mode") and not data.get("disable_mode"):
        code = message.text.strip().upper()

        if not code:
            await message.answer("❌ Код не может быть пустым.")
            return

        if len(code) > 50:
            await message.answer(
                "❌ Код слишком длинный. Максимум 50 символов."
            )
            return

        existing = get_promocode(code)

        if existing:
            await message.answer(
                "❌ Такой активный промокод уже существует.",
            )
            return

        await state.update_data(code=code)
        await state.set_state(PromoStates.waiting_days)

        await message.answer(
            "⏳ Отправь количество дней:",
        )
        return

    code = message.text.strip().upper()

    # ---------------- FIND ----------------

    if data.get("find_mode"):
        await state.clear()

        promos = get_all_promocodes()

        found = None

        for promo in promos:
            if str(promo.get("code", "")).upper() == code:
                found = promo
                break

        if not found:
            await message.answer(
                f"❌ Промокод <code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )
            return

        active = "🟢 Активен" if found.get("active") else "🔴 Неактивен"
        max_uses = found.get("max_uses", 0)
        uses = found.get("uses", 0)

        limit = "∞" if max_uses == 0 else str(max_uses)

        await message.answer(
            "🔎 <b>Промокод</b>\n\n"
            f"🎟 Код: <code>{found.get('code')}</code>\n"
            f"⏳ Дней: <b>{found.get('days')}</b>\n"
            f"🔢 Использований: <b>{uses}/{limit}</b>\n"
            f"📌 Статус: <b>{active}</b>",
            parse_mode="HTML",
            reply_markup=promo_menu(),
        )
        return

    # ---------------- DISABLE ----------------

    if data.get("disable_mode"):
        await state.clear()

        promo = get_promocode(code)

        if not promo:
            await message.answer(
                f"❌ Активный промокод <code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )
            return

        success = deactivate_promocode(code)

        if success:
            await message.answer(
                "✅ <b>Промокод деактивирован</b>\n\n"
                f"🎟 <code>{code}</code>",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )
        else:
            await message.answer(
                "❌ Не удалось деактивировать промокод.",
                reply_markup=promo_menu(),
            )


# ============================================================
# CALLBACK NOOP
# ============================================================

@router.callback_query(F.data == "admin_promo_noop")
async def promo_noop(callback: CallbackQuery):
    await callback.answer()