from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS

from database import (
    add_promocode,
    get_promocodes,
    delete_promocode,
)


router = Router()


# ============================================================
# НАСТРОЙКИ
# ============================================================

PROMOS_PER_PAGE = 10

MIN_PROMO_DAYS = 1
MAX_PROMO_DAYS = 3650


# ============================================================
# ПРОВЕРКА АДМИНА
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# FSM
# ============================================================

class PromoCreate(StatesGroup):
    code = State()
    days = State()


class PromoDelete(StatesGroup):
    code = State()


# ============================================================
# БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ПОЛЯ
# ============================================================

def promo_field(promo, index, default=None):
    try:
        if isinstance(promo, dict):
            keys = [
                "code",
                "days",
            ]

            if index < len(keys):
                return promo.get(
                    keys[index],
                    default,
                )

            return default

        return promo[index]

    except (IndexError, KeyError, TypeError):
        return default


# ============================================================
# КЛАВИАТУРА МЕНЮ
# ============================================================

def promo_menu_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать",
                    callback_data="promo_create",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список",
                    callback_data="promo_list",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data="promo_delete",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_back",
                )
            ],
        ]
    )


# ============================================================
# ОТКРЫТИЕ РАЗДЕЛА
# ============================================================

@router.callback_query(
    F.data == "admin_promos"
)
async def promos(
    call: CallbackQuery,
    state: FSMContext,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    try:
        promo_codes = get_promocodes() or []
        total = len(promo_codes)
    except Exception as e:
        print(
            "Admin promos load error:",
            repr(e),
        )
        total = 0

    text = (
        "🎟 <b>Промокоды</b>\n\n"
        f"📦 Всего активных: <b>{total}</b>\n\n"
        "Выберите действие:"
    )

    try:
        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=promo_menu_keyboard(),
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise

    await call.answer()


# ============================================================
# СОЗДАНИЕ ПРОМОКОДА
# ============================================================

@router.callback_query(
    F.data == "promo_create"
)
async def create_start(
    call: CallbackQuery,
    state: FSMContext,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        PromoCreate.code
    )

    await call.message.answer(
        "🎟 <b>Создание промокода</b>\n\n"
        "Введите код промокода.\n\n"
        "Пример:\n"
        "<code>IXXY2026</code>",
        parse_mode="HTML",
    )

    await call.answer()


# ============================================================
# ПОЛУЧЕНИЕ КОДА
# ============================================================

@router.message(
    PromoCreate.code
)
async def get_code(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):
        await state.clear()
        return

    if not message.text:

        await message.answer(
            "❌ Отправьте текстовый код."
        )
        return

    code = message.text.strip().upper()

    # --------------------------------------------------------
    # ВАЛИДАЦИЯ
    # --------------------------------------------------------

    if not code:

        await message.answer(
            "❌ Код не может быть пустым."
        )
        return

    if len(code) < 3:

        await message.answer(
            "❌ Код слишком короткий.\n"
            "Минимум: 3 символа."
        )
        return

    if len(code) > 32:

        await message.answer(
            "❌ Код слишком длинный.\n"
            "Максимум: 32 символа."
        )
        return

    allowed_chars = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_-"
    )

    if any(
        char not in allowed_chars
        for char in code
    ):

        await message.answer(
            "❌ Недопустимые символы.\n\n"
            "Разрешены только:\n"
            "A-Z, 0-9, _ и -"
        )
        return

    await state.update_data(
        code=code
    )

    await state.set_state(
        PromoCreate.days
    )

    await message.answer(
        "📅 <b>Сколько дней выдать?</b>\n\n"
        f"Минимум: <b>{MIN_PROMO_DAYS}</b>\n"
        f"Максимум: <b>{MAX_PROMO_DAYS}</b>\n\n"
        "Например: <code>30</code>",
        parse_mode="HTML",
    )


# ============================================================
# ПОЛУЧЕНИЕ ДНЕЙ
# ============================================================

@router.message(
    PromoCreate.days
)
async def get_days(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):
        await state.clear()
        return

    if not message.text:

        await message.answer(
            "❌ Введите количество дней числом."
        )
        return

    try:

        days = int(
            message.text.strip()
        )

    except ValueError:

        await message.answer(
            "❌ Нужно ввести целое число.\n\n"
            "Например: <code>30</code>",
            parse_mode="HTML",
        )
        return

    if days < MIN_PROMO_DAYS:

        await message.answer(
            f"❌ Минимум — {MIN_PROMO_DAYS} день."
        )
        return

    if days > MAX_PROMO_DAYS:

        await message.answer(
            f"❌ Максимум — {MAX_PROMO_DAYS} дней."
        )
        return

    data = await state.get_data()

    code = str(
        data.get(
            "code",
            ""
        )
    ).upper()

    if not code:

        await state.clear()

        await message.answer(
            "❌ Сессия создания промокода устарела.\n"
            "Создайте промокод заново."
        )
        return

    # --------------------------------------------------------
    # СОЗДАНИЕ
    # --------------------------------------------------------

    try:

        result = add_promocode(
            code,
            days,
        )

    except Exception as e:

        print(
            "Promo create error:",
            repr(e),
        )

        await message.answer(
            "❌ Не удалось создать промокод.\n\n"
            "Возможно, такой код уже существует."
        )

        await state.clear()
        return

    await state.clear()

    await message.answer(
        "✅ <b>Промокод создан!</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n"
        f"📅 Срок: <b>{days} дней</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎟 К промокодам",
                        callback_data="admin_promos",
                    )
                ]
            ]
        ),
    )


# ============================================================
# СПИСОК ПРОМОКОДОВ
# ============================================================

async def show_promo_list(
    call: CallbackQuery,
    page: int = 0,
):

    try:

        promos = get_promocodes() or []

    except Exception as e:

        print(
            "Promo list error:",
            repr(e),
        )

        await call.message.edit_text(
            "❌ Не удалось получить список промокодов.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="admin_promos",
                        )
                    ]
                ]
            ),
        )

        return

    if not promos:

        await call.message.edit_text(
            "🎟 <b>Промокоды</b>\n\n"
            "Активных промокодов нет.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="➕ Создать",
                            callback_data="promo_create",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="⬅️ Назад",
                            callback_data="admin_promos",
                        )
                    ],
                ]
            ),
        )

        return

    total = len(promos)

    total_pages = max(
        1,
        (
            total
            + PROMOS_PER_PAGE
            - 1
        )
        // PROMOS_PER_PAGE,
    )

    if page < 0:
        page = 0

    if page >= total_pages:
        page = total_pages - 1

    start = (
        page
        * PROMOS_PER_PAGE
    )

    end = (
        start
        + PROMOS_PER_PAGE
    )

    page_promos = promos[
        start:end
    ]

    text = (
        "🎟 <b>Активные промокоды</b>\n\n"
    )

    buttons = []

    for promo in page_promos:

        code = promo_field(
            promo,
            0,
            "???",
        )

        days = promo_field(
            promo,
            1,
            0,
        )

        text += (
            f"🔹 <code>{code}</code>"
            f" — <b>{days} дн.</b>\n"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    text=(
                        f"🎟 {code} · "
                        f"{days} дней"
                    ),
                    callback_data=(
                        f"promo_view_"
                        f"{str(code)}"
                    ),
                )
            ]
        )

    text += (
        "\n"
        f"📄 Страница: "
        f"<b>{page + 1}/{total_pages}</b>\n"
        f"📦 Всего: <b>{total}</b>"
    )

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=(
                    f"promo_list_page_{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="noop",
        )
    )

    if end < total:

        navigation.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"promo_list_page_{page + 1}"
                ),
            )
        )

    buttons.append(
        navigation
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="🔄 Обновить",
                callback_data=(
                    f"promo_list_page_{page}"
                ),
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="➕ Создать",
                callback_data="promo_create",
            )
        ]
    )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_promos",
            )
        ]
    )

    try:

        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=buttons
            ),
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise


# ============================================================
# ОТКРЫТЬ СПИСОК
# ============================================================

@router.callback_query(
    F.data == "promo_list"
)
async def promo_list(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await call.answer()

    await show_promo_list(
        call,
        page=0,
    )


# ============================================================
# ПАГИНАЦИЯ СПИСКА
# ============================================================

@router.callback_query(
    F.data.startswith("promo_list_page_")
)
async def promo_list_page(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    try:

        page = int(
            call.data.replace(
                "promo_list_page_",
                "",
                1,
            )
        )

    except (ValueError, AttributeError):

        await call.answer(
            "❌ Ошибка страницы.",
            show_alert=True,
        )
        return

    await call.answer()

    await show_promo_list(
        call,
        page=page,
    )


# ============================================================
# ПРОСМОТР ПРОМОКОДА
# ============================================================

@router.callback_query(
    F.data.startswith("promo_view_")
)
async def promo_view(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    code = call.data.replace(
        "promo_view_",
        "",
        1,
    )

    try:

        promos = get_promocodes() or []

    except Exception as e:

        print(
            "Promo view error:",
            repr(e),
        )

        await call.answer(
            "❌ Ошибка базы данных.",
            show_alert=True,
        )
        return

    promo = None

    for item in promos:

        item_code = str(
            promo_field(
                item,
                0,
                "",
            )
        ).upper()

        if item_code == code.upper():

            promo = item
            break

    if not promo:

        await call.answer(
            "❌ Промокод не найден.",
            show_alert=True,
        )
        return

    days = promo_field(
        promo,
        1,
        0,
    )

    text = (
        "🎟 <b>Промокод</b>\n\n"
        f"🔑 Код: <code>{code}</code>\n"
        f"📅 Выдаёт: <b>{days} дней</b>\n\n"
        "Выберите действие:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить",
                    callback_data=(
                        f"promo_delete_confirm_{code}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ К списку",
                    callback_data="promo_list",
                )
            ],
        ]
    )

    try:

        await call.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise

    await call.answer()


# ============================================================
# НАЧАЛО УДАЛЕНИЯ
# ============================================================

@router.callback_query(
    F.data == "promo_delete"
)
async def promo_delete_start(
    call: CallbackQuery,
    state: FSMContext,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await state.clear()

    await state.set_state(
        PromoDelete.code
    )

    await call.message.answer(
        "🗑 <b>Удаление промокода</b>\n\n"
        "Введите код, который нужно удалить.\n\n"
        "Для отмены отправьте:\n"
        "<code>/cancel</code>",
        parse_mode="HTML",
    )

    await call.answer()


# ============================================================
# ПОЛУЧЕНИЕ КОДА ДЛЯ УДАЛЕНИЯ
# ============================================================

@router.message(
    PromoDelete.code
)
async def promo_delete_code(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):
        await state.clear()
        return

    if not message.text:

        await message.answer(
            "❌ Отправьте код текстом."
        )
        return

    code = message.text.strip().upper()

    if code == "/CANCEL":

        await state.clear()

        await message.answer(
            "❌ Удаление отменено.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⬅️ К промокодам",
                            callback_data="admin_promos",
                        )
                    ]
                ]
            ),
        )

        return

    if not code:

        await message.answer(
            "❌ Код не может быть пустым."
        )
        return

    try:

        promos = get_promocodes() or []

    except Exception as e:

        print(
            "Promo delete lookup error:",
            repr(e),
        )

        await state.clear()

        await message.answer(
            "❌ Не удалось проверить промокод."
        )

        return

    exists = False

    for promo in promos:

        existing_code = str(
            promo_field(
                promo,
                0,
                "",
            )
        ).upper()

        if existing_code == code:

            exists = True
            break

    if not exists:

        await message.answer(
            f"❌ Промокод <code>{code}</code> не найден.",
            parse_mode="HTML",
        )
        return

    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Да, удалить",
                    callback_data=(
                        f"promo_delete_confirm_{code}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="admin_promos",
                )
            ],
        ]
    )

    await message.answer(
        "⚠️ <b>Удаление промокода</b>\n\n"
        f"🎟 Код: <code>{code}</code>\n\n"
        "Удалить его?",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ
# ============================================================

@router.callback_query(
    F.data.startswith("promo_delete_confirm_")
)
async def promo_delete_confirm(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    code = call.data.replace(
        "promo_delete_confirm_",
        "",
        1,
    )

    if not code:

        await call.answer(
            "❌ Некорректный код.",
            show_alert=True,
        )
        return

    try:

        delete_promocode(
            code
        )

    except Exception as e:

        print(
            "Promo delete error:",
            repr(e),
        )

        await call.answer(
            "❌ Не удалось удалить промокод.",
            show_alert=True,
        )
        return

    try:

        await call.message.edit_text(
            "✅ <b>Промокод удалён</b>\n\n"
            f"🎟 <code>{code}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🎟 К промокодам",
                            callback_data="admin_promos",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="📋 Список",
                            callback_data="promo_list",
                        )
                    ],
                ]
            ),
        )

    except TelegramBadRequest as e:

        if "message is not modified" not in str(e):
            raise

    await call.answer(
        "✅ Промокод удалён"
    )


# ============================================================
# NO-OP
# ============================================================

@router.callback_query(
    F.data == "noop"
)
async def promo_noop(
    call: CallbackQuery,
):

    if not call.from_user or not is_admin(
        call.from_user.id
    ):
        await call.answer(
            "❌ Нет доступа.",
            show_alert=True,
        )
        return

    await call.answer()


# ============================================================
# ОТМЕНА FSM
# ============================================================

@router.message(
    F.text == "/cancel"
)
async def promo_cancel(
    message: Message,
    state: FSMContext,
):

    if not message.from_user or not is_admin(
        message.from_user.id
    ):
        return

    current_state = await state.get_state()

    if current_state is None:
        return

    await state.clear()

    await message.answer(
        "❌ Действие отменено.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎟 К промокодам",
                        callback_data="admin_promos",
                    )
                ]
            ]
        ),
    )