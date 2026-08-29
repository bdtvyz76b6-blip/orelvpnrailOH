from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
)
from aiogram.filters import Command

from datetime import datetime, timedelta

from config import SUPPORT

from database import (
    add_user,
    get_user,
    get_subscription_link,
    save_subscription_link,
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
)


router = Router()


# ============================================================
# ПРОВЕРКА ПОДПИСКИ
# ============================================================

def get_subscription_status(user_id: int):

    user = get_user(user_id)

    if not user:
        return False, "—"

    until = user[4] or ""

    if not until:
        return False, "—"

    try:

        expire_date = datetime.strptime(
            str(until),
            "%Y-%m-%d",
        ).date()

        today = datetime.now().date()

        if expire_date >= today:

            return (
                True,
                expire_date.strftime("%d.%m.%Y")
            )

    except Exception as e:

        print(
            f"❌ Ошибка проверки подписки "
            f"{user_id}: {e}"
        )

    return False, "—"


# ============================================================
# СОЗДАНИЕ ПЕРСОНАЛЬНОЙ ССЫЛКИ
# ============================================================

def ensure_subscription(user_id: int):

    link = get_subscription_link(user_id)

    if link:
        return link

    try:

        link = create_user_subscription(
            user_id
        )

        if link:

            save_subscription_link(
                user_id,
                link,
            )

        return link

    except Exception as e:

        print(
            f"❌ Ошибка создания подписки "
            f"{user_id}: {e}"
        )

        return ""


# ============================================================
# START
# ============================================================

@router.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # --------------------------------------------------------
    # ПРОВЕРКА УСЛОВИЙ
    # --------------------------------------------------------

    if not has_accepted_terms(user_id):

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
    # СОЗДАЁМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # --------------------------------------------------------

    ensure_subscription(
        user_id
    )

    # --------------------------------------------------------
    # ПРОВЕРЯЕМ СТАТУС
    # --------------------------------------------------------

    subscription_active, until_text = (
        get_subscription_status(user_id)
    )

    # --------------------------------------------------------
    # АКТИВНАЯ ПОДПИСКА
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # НЕТ ПОДПИСКИ
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # ВСЕГДА ГЛАВНОЕ МЕНЮ
    # --------------------------------------------------------

    await message.answer(
        text,
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
    )


# ============================================================
# ПРИНЯТИЕ УСЛОВИЙ
# ============================================================

@router.callback_query(
    F.data == "accept_terms"
)
async def accept(callback: CallbackQuery):

    user_id = callback.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name,
    )

    # --------------------------------------------------------
    # ПРИНИМАЕМ УСЛОВИЯ
    # --------------------------------------------------------

    accept_terms(
        user_id
    )

    # --------------------------------------------------------
    # СОЗДАЁМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # --------------------------------------------------------

    ensure_subscription(
        user_id
    )

    # --------------------------------------------------------
    # УДАЛЯЕМ СТАРОЕ СООБЩЕНИЕ
    # --------------------------------------------------------

    try:

        await callback.message.delete()

    except Exception:

        pass

    # --------------------------------------------------------
    # ПОКАЗЫВАЕМ ГЛАВНОЕ МЕНЮ
    # --------------------------------------------------------

    await callback.message.answer(
        """
✅ <b>Условия приняты!</b>

☂️ Добро пожаловать в <b>ixxy VPN</b>!

🔐 Ваша персональная подписка
уже создана.

🎫 Выберите нужный раздел
в меню ниже 👇
""",
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# КУПИТЬ ПОДПИСКУ
# ============================================================

@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy(message: Message):

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
async def stars(callback: CallbackQuery):

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
async def sbp(callback: CallbackQuery):

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
async def trial(message: Message):

    user_id = message.from_user.id

    # --------------------------------------------------------
    # РЕГИСТРАЦИЯ
    # --------------------------------------------------------

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # --------------------------------------------------------
    # ПРОВЕРКА УСЛОВИЙ
    # --------------------------------------------------------

    if not has_accepted_terms(user_id):

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

    if check_trial(user_id):

        await message.answer(
            """
❌ <b>Пробный период уже использован.</b>

Вы можете приобрести подписку
через кнопку:

🎫 <b>Купить подписку</b>
""",
            reply_markup=main_menu(user_id),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # СОЗДАЁМ ПОДПИСКУ
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

        activate_trial(
            user_id,
            link,
        )

        save_subscription_link(
            user_id,
            link,
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
            reply_markup=main_menu(user_id),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # ДАТА ОКОНЧАНИЯ
    # --------------------------------------------------------

    trial_until = (
        datetime.now().date()
        + timedelta(days=3)
    ).strftime(
        "%d.%m.%Y"
    )

    # --------------------------------------------------------
    # УСПЕШНАЯ АКТИВАЦИЯ
    # --------------------------------------------------------

    await message.answer(
        f"""
🎉 <b>Пробный период активирован!</b>

☂️ <b>ixxy VPN</b>

🟢 Подписка активна до:
<b>{trial_until}</b>

━━━━━━━━━━━━━━━━━━

⚡ Чтобы подключить VPN:

👤 Откройте <b>«Личный кабинет»</b>

и нажмите:

⚡ <b>«Подключиться»</b>
""",
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
    )


# ============================================================
# ПОДДЕРЖКА
# ============================================================

@router.message(
    F.text == "💬 Поддержка"
)
async def support(message: Message):

    await message.answer(
        f"""
💬 <b>Поддержка ixxy VPN</b>

Если возникли проблемы
с подключением, обратитесь:

{SUPPORT}
""",
        reply_markup=main_menu(
            message.from_user.id
        ),
        parse_mode="HTML",
    )