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
# CREATE
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
# CREATE — CODE
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

    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Операция отменена.",
            reply_markup=promo_menu(),
        )
        return

    data = await state.get_data()
    mode = data.get("mode")

    code = normalize_code(
        message.text
    )

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

    # --------------------------------------------------------
    # FIND
    # --------------------------------------------------------

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

            if (
                str(
                    promo.get("code")
                    or ""
                ).upper()
                == code
            ):
                found = promo
                break

        if not found:

            await message.answer(
                f"❌ Промокод "
                f"<code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )
            return

        active = (
            "🟢 Активен"
            if bool(found.get("active"))
            else "🔴 Неактивен"
        )

        days = found.get(
            "days"
        ) or 0

        uses = found.get(
            "uses"
        ) or 0

        max_uses = found.get(
            "max_uses"
        ) or 0

        limit = (
            "∞"
            if max_uses == 0
            else str(max_uses)
        )

        await message.answer(
            "🔎 <b>Промокод</b>\n\n"
            f"🎟 Код: "
            f"<code>{found.get('code')}</code>\n"
            f"⏳ Дней: <b>{days}</b>\n"
            f"🔢 Использований: "
            f"<b>{uses}/{limit}</b>\n"
            f"📌 Статус: <b>{active}</b>",
            parse_mode="HTML",
            reply_markup=promo_menu(),
        )

        return

    # --------------------------------------------------------
    # DISABLE
    # --------------------------------------------------------

    if mode == "disable":

        await state.clear()

        try:
            promo = get_promocode(code)
        except Exception as e:
            print(
                "Promo disable lookup error:",
                repr(e),
            )

            await message.answer(
                "❌ Ошибка базы данных.",
                reply_markup=promo_menu(),
            )
            return

        if not promo:

            await message.answer(
                f"❌ Активный промокод "
                f"<code>{code}</code> не найден.",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )
            return

        try:
            success = deactivate_promocode(
                code
            )
        except Exception as e:
            print(
                "Promo deactivate error:",
                repr(e),
            )
            success = False

        if success:

            await message.answer(
                "✅ <b>Промокод деактивирован</b>\n\n"
                f"🎟 <code>{code}</code>",
                parse_mode="HTML",
                reply_markup=promo_menu(),
            )

        else:

            await message.answer(
                "❌ Не удалось "
                "деактивировать промокод.",
                reply_markup=promo_menu(),
            )

        return

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    if mode != "create":

        await state.clear()

        await message.answer(
            "❌ Состояние операции потеряно.",
            reply_markup=promo_menu(),
        )
        return

    try:
        existing = get_promocode(code)
    except Exception as e:
        print(
            "Promo lookup error:",
            repr(e),
        )

        await message.answer(
            "❌ Ошибка при проверке промокода."
        )
        return

    if existing:

        await message.answer(
            "❌ Такой активный промокод "
            "уже существует.\n\n"
            f"🎟 Код: <code>{code}</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(
        code=code
    )

    await state.set_state(
        PromoStates.waiting_days
    )

    await message.answer(
        "⏳ Теперь отправь "
        "количество дней подписки.\n\n"
        "Например:\n"
        "<code>30</code>",
        parse_mode="HTML",
    )


# ============================================================
# CREATE — DAYS
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

    if message.text == "/cancel":

        await state.clear()

        await message.answer(
            "❌ Создание промокода отменено.",
            reply_markup=promo_menu(),
        )

        return

    try:

        days = int(
            (message.text or "").strip()
        )

    except (
        ValueError,
        TypeError,
    ):

        await message.answer(
            "❌ Введи число.\n\n"
            "Например: <code>30</code>",
            parse_mode="HTML",
        )

        return

    if days <= 0:

        await message.answer(
            "❌ Количество дней "
            "должно быть больше 0."
        )

        return

    if days > 999999999:

        await message.answer(
            "❌ Слишком большое "
            "количество дней."
        )

        return

    await state.update_data(
        days=days
    )

    await state.set_state(
        PromoStates.waiting_max_uses
    )

    await message.answer(
        "🔢 Теперь укажи максимальное "
        "количество использований.\n\n"
        "Например:\n"
        "<code>10</code>\n\n"
        "Или отправь <code>0</code>, "
        "если ограничений нет.\n\n"
        "Для отмены: /cancel",
        parse_mode="HTML",
    )


# ============================================================
# CREATE — MAX USES
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

    if message.text == "/cancel":

        await state.clear()

        await message.answer(
            "❌ Создание промокода отменено.",
            reply_markup=promo_menu(),
        )

        return

    try:

        max_uses = int(
            (message.text or "").strip()
        )

    except (
        ValueError,
        TypeError,
    ):

        await message.answer(
            "❌ Введи число.\n\n"
            "Например: <code>10</code>",
            parse_mode="HTML",
        )

        return

    if max_uses < 0:

        await message.answer(
            "❌ Количество использований "
            "не может быть отрицательным."
        )

        return

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    data = await state.get_data()

    code = data.get("code")
    days = data.get("days")

    if not code or not days:

        await state.clear()

        await message.answer(
            "❌ Данные промокода потеряны.",
            reply_markup=promo_menu(),
        )

        return

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    try:

        success = create_promocode(
            code=code,
            days=days,
            max_uses=max_uses,
        )

    except Exception as e:

        print(
            "Create promocode error:",
            repr(e),
        )

        success = False

    await state.clear()

    if not success:

        await message.answer(
            "❌ Не удалось создать промокод.\n\n"
            "Возможно, такой код уже существует.",
            reply_markup=promo_menu(),
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

    promos = [
        promo
        for promo in promos
        if isinstance(
            promo,
            dict,
        )
    ]

    if not promos:

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Назад",
                        callback_data=(
                            "admin_promo_back"
                        ),
                    )
                ]
            ]
        )

        if callback.message:

            await callback.message.edit_text(
                "📋 <b>Промокодов пока нет.</b>",
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        await callback.answer()

        return

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    try:

        promos.sort(
            key=lambda x: str(
                x.get("code") or ""
            ).upper()
        )

    except Exception:
        pass

    text = (
        "📋 <b>Промокоды ixxy VPN</b>\n\n"
    )

    for promo in promos:

        code = (
            promo.get("code")
            or "???"
        )

        days = (
            promo.get("days")
            or 0
        )

        uses = (
            promo.get("uses")
            or 0
        )

        max_uses = (
            promo.get("max_uses")
            or 0
        )

        active = bool(
            promo.get("active")
        )

        status = (
            "🟢"
            if active
            else "🔴"
        )

        usage = (
            f"{uses}/∞"
            if max_uses == 0
            else f"{uses}/{max_uses}"
        )

        text += (
            f"{status} <code>{code}</code>\n"
            f"   ⏳ {days} дней\n"
            f"   🔢 Использований: "
            f"{usage}\n\n"
        )

    # --------------------------------------------------------
    # TELEGRAM MESSAGE LIMIT
    # --------------------------------------------------------

    if len(text) > 3900:

        text = text[:3900]

        text += (
            "\n\n⚠️ Список слишком большой. "
            "Показана только часть."
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить",
                    callback_data=(
                        "admin_promo_list"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=(
                        "admin_promo_back"
                    ),
                )
            ],
        ]
    )

    if callback.message:

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
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
            "Отправь код, который нужно "
            "деактивировать.\n\n"
            "Для отмены: /cancel",
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# CANCEL
# ============================================================

@router.message(
    PromoStates.waiting_code,
    F.text == "/cancel",
)
@router.message(
    PromoStates.waiting_days,
    F.text == "/cancel",
)
@router.message(
    PromoStates.waiting_max_uses,
    F.text == "/cancel",
)
async def promo_cancel(
    message: Message,
    state: FSMContext,
):

    if message.from_user and is_admin(
        message.from_user.id
    ):

        await state.clear()

        await message.answer(
            "❌ Операция отменена.",
            reply_markup=promo_menu(),
        )


# ============================================================
# NOOP
# ============================================================

@router.callback_query(
    F.data == "admin_promo_noop"
)
async def promo_noop(
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

    await callback.answer()