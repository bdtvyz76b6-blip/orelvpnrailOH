from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from datetime import datetime, timezone

from config import SUPPORT

from database import (
    add_user,
    get_user,
    check_trial,
    activate_trial,
    has_accepted_terms,
    accept_terms,
)

from keyboards import (
    main_menu,
    payment_method_keyboard,
    stars_buy_keyboard,
    sbp_buy_keyboard,
    accept_terms_keyboard,
)

from github_update import (
    create_subscription,
    create_user_subscription,
    update_subscription_file,
    get_subscription_link,
)


router = Router()

UTC = timezone.utc


# ============================================================
# ДАТА
# ============================================================

def normalize_date(value):

    if value is None:
        return None

    if isinstance(value, datetime):

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=UTC
            )

        return value.astimezone(
            UTC
        ).date()

    text = str(value).strip()

    if not text:
        return None

    try:

        return datetime.fromisoformat(
            text.replace(
                "Z",
                "+00:00",
            )
        ).date()

    except Exception:
        pass

    try:

        return datetime.strptime(
            text[:10],
            "%Y-%m-%d",
        ).date()

    except Exception:
        return None


# ============================================================
# СТАТУС ПОДПИСКИ
# ============================================================

def get_subscription_status(user_id: int):

    try:

        user = get_user(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка получения пользователя "
            f"{user_id}: {e}"
        )

        return False, "—"

    if not user:
        return False, "—"

    expire_date = normalize_date(
        user.get(
            "subscription_until"
        )
    )

    if not expire_date:
        return False, "—"

    today = datetime.now(
        UTC
    ).date()

    if expire_date < today:

        return (
            False,
            expire_date.strftime(
                "%d.%m.%Y"
            ),
        )

    return (
        True,
        expire_date.strftime(
            "%d.%m.%Y"
        ),
    )


# ============================================================
# ПОСТОЯННАЯ ССЫЛКА
# ============================================================

def ensure_subscription(
    user_id: int,
) -> str:

    # Всегда используем ОДИН генератор ссылки.
    # Никаких старых ссылок из database.py.

    link = get_subscription_link(
        user_id
    )

    if link:
        return str(link).strip()

    try:

        link = create_user_subscription(
            user_id
        )

        if link:
            return str(link).strip()

    except Exception as e:

        print(
            f"❌ Ошибка создания подписки "
            f"{user_id}: {e}"
        )

    return ""


# ============================================================
# START
# ============================================================

@router.message(
    Command("start")
)
async def start(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    try:

        add_user(
            user_id,
            message.from_user.username,
            message.from_user.first_name,
        )

    except Exception as e:

        print(
            f"❌ Ошибка регистрации "
            f"{user_id}: {e}"
        )

        await message.answer(
            "❌ Не удалось зарегистрировать пользователя."
        )

        return

    # --------------------------------------------------------
    # УСЛОВИЯ
    # --------------------------------------------------------

    try:

        accepted = has_accepted_terms(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки условий "
            f"{user_id}: {e}"
        )

        accepted = False

    if not accepted:

        await message.answer(
            """
☂️ <b>Добро пожаловать в ixxy VPN</b>

🚀 Быстрый и удобный VPN
🔐 Персональная подписка
⚡ Подключение в пару нажатий

Перед использованием сервиса
необходимо принять условия.

👇 Нажмите кнопку ниже:
""",
            reply_markup=accept_terms_keyboard(),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # ПОСТОЯННАЯ ССЫЛКА
    # --------------------------------------------------------

    ensure_subscription(
        user_id
    )

    # --------------------------------------------------------
    # СТАТУС
    # --------------------------------------------------------

    subscription_active, until_text = (
        get_subscription_status(
            user_id
        )
    )

    if subscription_active:

        text = f"""
☂️ <b>ixxy VPN</b>

🟢 <b>Ваша подписка активна</b>

📅 Активна до:
<b>{until_text}</b>

━━━━━━━━━━━━━━━━━━

👤 Управление подпиской находится
в разделе <b>«Личный кабинет»</b>.

👇 Выберите раздел в меню:
"""

    else:

        text = """
☂️ <b>ixxy VPN</b>

👋 Добро пожаловать!

❌ <b>Ваша подписка не активна</b>

━━━━━━━━━━━━━━━━━━

🎫 Оформите подписку
или активируйте пробный период.

👇 Выберите раздел в меню:
"""

    await message.answer(
        text,
        reply_markup=main_menu(
            user_id
        ),
        parse_mode="HTML",
    )


# ============================================================
# ПРИНЯТИЕ УСЛОВИЙ
# ============================================================

@router.callback_query(
    F.data == "accept_terms"
)
async def accept(
    callback: CallbackQuery,
):

    user_id = callback.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    try:

        add_user(
            user_id,
            callback.from_user.username,
            callback.from_user.first_name,
        )

    except Exception as e:

        print(
            f"❌ Ошибка регистрации "
            f"{user_id}: {e}"
        )

        await callback.answer(
            "❌ Ошибка регистрации",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ПРИНИМАЕМ УСЛОВИЯ
    # --------------------------------------------------------

    try:

        accept_terms(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка принятия условий "
            f"{user_id}: {e}"
        )

        await callback.answer(
            "❌ Не удалось принять условия",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # СОЗДАЁМ ПОСТОЯННУЮ ССЫЛКУ
    # --------------------------------------------------------

    ensure_subscription(
        user_id
    )

    # --------------------------------------------------------
    # УДАЛЯЕМ СТАРОЕ СООБЩЕНИЕ
    # --------------------------------------------------------

    try:

        if callback.message:
            await callback.message.delete()

    except Exception:
        pass

    # --------------------------------------------------------
    # МЕНЮ
    # --------------------------------------------------------

    if callback.message:

        await callback.message.answer(
            """
✅ <b>Условия приняты!</b>

☂️ Добро пожаловать в <b>ixxy VPN</b>!

🔐 Ваша персональная подписка
уже создана.

🎫 Выберите нужный раздел
в меню ниже 👇
""",
            reply_markup=main_menu(
                user_id
            ),
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# КУПИТЬ
# ============================================================

@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy(
    message: Message,
):

    await message.answer(
        """
☂️ <b>ixxy VPN</b>

💎 <b>Выберите способ оплаты:</b>
""",
        reply_markup=payment_method_keyboard(),
        parse_mode="HTML",
    )


# ============================================================
# TELEGRAM STARS
# ============================================================

@router.callback_query(
    F.data == "pay_stars"
)
async def stars(
    callback: CallbackQuery,
):

    if callback.message:

        await callback.message.answer(
            """
⭐ <b>Telegram Stars</b>

Выберите срок подписки:
""",
            reply_markup=stars_buy_keyboard(),
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# СБП
# ============================================================

@router.callback_query(
    F.data == "pay_sbp"
)
async def sbp(
    callback: CallbackQuery,
):

    if callback.message:

        await callback.message.answer(
            """
💳 <b>Оплата СБП</b>

Выберите срок подписки:
""",
            reply_markup=sbp_buy_keyboard(),
            parse_mode="HTML",
        )

    await callback.answer()


# ============================================================
# ПРОБНЫЙ ПЕРИОД
# ============================================================

@router.message(
    F.text == "🎁 Пробный период"
)
async def trial(
    message: Message,
):

    if not message.from_user:
        return

    user_id = message.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    try:

        add_user(
            user_id,
            message.from_user.username,
            message.from_user.first_name,
        )

    except Exception as e:

        print(
            f"❌ Ошибка регистрации "
            f"{user_id}: {e}"
        )

        await message.answer(
            "❌ Не удалось зарегистрировать пользователя."
        )

        return

    # --------------------------------------------------------
    # УСЛОВИЯ
    # --------------------------------------------------------

    try:

        accepted = has_accepted_terms(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки условий "
            f"{user_id}: {e}"
        )

        accepted = False

    if not accepted:

        await message.answer(
            """
☂️ <b>Сначала примите условия использования.</b>

После этого станет доступен
пробный период на 3 дня.
""",
            reply_markup=accept_terms_keyboard(),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # ПРОВЕРКА TRIAL
    # --------------------------------------------------------

    try:

        already_used = check_trial(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка проверки trial "
            f"{user_id}: {e}"
        )

        already_used = False

    if already_used:

        await message.answer(
            """
❌ <b>Пробный период уже использован.</b>

Вы можете приобрести подписку
через кнопку:

🎫 <b>Купить подписку</b>
""",
            reply_markup=main_menu(
                user_id
            ),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # СОЗДАНИЕ ПОДПИСКИ
    # --------------------------------------------------------

    try:

        link = create_subscription(
            user_id,
            days=3,
        )

        if not link:

            link = ensure_subscription(
                user_id
            )

        if not link:

            raise RuntimeError(
                "Не удалось получить ссылку подписки"
            )

        # Сохраняем факт trial.
        activate_trial(
            user_id,
            link,
        )

        # Обновляем профиль.
        update_subscription_file(
            user_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка активации trial "
            f"{user_id}: {e}"
        )

        await message.answer(
            """
❌ <b>Не удалось активировать пробный период.</b>

Попробуйте ещё раз позже.
""",
            reply_markup=main_menu(
                user_id
            ),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # ПОЛУЧАЕМ ДАТУ
    # --------------------------------------------------------

    try:

        user = get_user(
            user_id
        )

        trial_until = (
            user.get(
                "subscription_until"
            )
            if isinstance(
                user,
                dict,
            )
            else None
        )

    except Exception:

        trial_until = None

    trial_date = normalize_date(
        trial_until
    )

    if trial_date:

        trial_until_text = (
            trial_date.strftime(
                "%d.%m.%Y"
            )
        )

    else:

        trial_until_text = "через 3 дня"

    # --------------------------------------------------------
    # ПОСТОЯННАЯ ССЫЛКА
    # --------------------------------------------------------

    permanent_link = get_subscription_link(
        user_id
    )

    # --------------------------------------------------------
    # УСПЕХ
    # --------------------------------------------------------

    await message.answer(
        f"""
🎉 <b>Пробный период активирован!</b>

☂️ <b>ixxy VPN</b>

🟢 Подписка активна до:
<b>{trial_until_text}</b>

━━━━━━━━━━━━━━━━━━

⚡ Чтобы подключить VPN:

👤 Откройте <b>«Личный кабинет»</b>

и нажмите:

⚡ <b>«Подключиться»</b>

🔗 Ваша постоянная ссылка:

<code>{permanent_link}</code>
""",
        reply_markup=main_menu(
            user_id
        ),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ============================================================
# ПОДДЕРЖКА
# ============================================================

@router.message(
    F.text == "💬 Поддержка"
)
async def support(
    message: Message,
):

    support_text = str(
        SUPPORT or "@orelvpntopbot"
    ).strip()

    await message.answer(
        f"""
💬 <b>Поддержка ixxy VPN</b>

Если возникли проблемы
с подключением, обратитесь:

{support_text}
""",
        reply_markup=main_menu(
            message.from_user.id
        ),
        parse_mode="HTML",
    )