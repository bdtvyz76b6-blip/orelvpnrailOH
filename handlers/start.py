from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardRemove,
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
    show_menu_keyboard,
)

from github_update import (
    create_subscription,
    create_user_subscription,
)


router = Router()


# ============================================================
# START
# ============================================================

@router.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id

    # ========================================================
    # СОЗДАЁМ ПОЛЬЗОВАТЕЛЯ
    # ========================================================

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # ========================================================
    # СОГЛАШЕНИЕ
    # ========================================================

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

    # ========================================================
    # ПОЛУЧАЕМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # ========================================================

    link = get_subscription_link(user_id)

    if not link:

        link = create_user_subscription(
            user_id
        )

        save_subscription_link(
            user_id,
            link,
        )

    # ========================================================
    # СТАТУС
    # ========================================================

    status = "🔴 Не активна"

    user = get_user(user_id)

    if user:

        until = user[4]

        if until:

            try:

                date = datetime.strptime(
                    str(until),
                    "%Y-%m-%d",
                )

                if date.date() >= datetime.now().date():

                    status = "🟢 Активна"

                else:

                    status = "🔴 Истекла"

            except Exception:

                status = "🔴 Не активна"

    # ========================================================
    # ГЛАВНОЕ МЕНЮ
    # ========================================================

    await message.answer(
        """
☂️ <b>ixxy VPN</b>

Добро пожаловать! 👋

━━━━━━━━━━━━━━━━━━

🛡 <b>Ваш VPN готов</b>

🎫 Подписка: {status}

━━━━━━━━━━━━━━━━━━

🌐 <b>Моя подписка</b>

Откройте её прямо из меню —
там можно:

⚡ Добавить в Happ
🚀 Добавить в INCY
📋 Скопировать ссылку

━━━━━━━━━━━━━━━━━━

Выберите нужный раздел ниже 👇
""".format(
            status=status
        ),
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

    # ========================================================
    # СОЗДАЁМ ПОЛЬЗОВАТЕЛЯ
    # ========================================================

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name,
    )

    # ========================================================
    # СОХРАНЯЕМ СОГЛАШЕНИЕ
    # ========================================================

    accept_terms(user_id)

    # ========================================================
    # СОЗДАЁМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # ========================================================

    link = get_subscription_link(user_id)

    if not link:

        link = create_user_subscription(
            user_id
        )

        save_subscription_link(
            user_id,
            link,
        )

    # ========================================================
    # УДАЛЯЕМ СООБЩЕНИЕ
    # ========================================================

    try:

        await callback.message.delete()

    except Exception:

        pass

    # ========================================================
    # ГЛАВНОЕ МЕНЮ
    # ========================================================

    await callback.message.answer(
        """
✅ <b>Условия приняты!</b>

☂️ Добро пожаловать в <b>ixxy VPN</b>!

🔐 Ваша персональная подписка
уже создана.

🌐 Откройте кнопку
<b>«Моя подписка»</b> в меню.

Там доступны:

⚡ Добавить в Happ
🚀 Добавить в INCY
📋 Скопировать ссылку

👇 Всё управление VPN — в одном месте.
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

    # ========================================================
    # СОЗДАЁМ ПОЛЬЗОВАТЕЛЯ
    # ========================================================

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name,
    )

    # ========================================================
    # СОГЛАШЕНИЕ
    # ========================================================

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

    # ========================================================
    # ПРОВЕРКА TRIAL
    # ========================================================

    if check_trial(user_id):

        await message.answer(
            """
❌ <b>Пробный период уже использован.</b>

Вы можете приобрести подписку:

🎫 <b>Купить подписку</b>
""",
            parse_mode="HTML",
        )

        return

    # ========================================================
    # СОЗДАЁМ ПОДПИСКУ
    # ========================================================

    link = create_subscription(
        user_id,
        days=3,
    )

    activate_trial(
        user_id,
        link,
    )

    save_subscription_link(
        user_id,
        link,
    )

    # ========================================================
    # ДАТА
    # ========================================================

    trial_until = (
        datetime.now().date()
        + timedelta(days=3)
    ).strftime("%d.%m.%Y")

    # ========================================================
    # ОТВЕТ
    # ========================================================

    await message.answer(
        f"""
🎉 <b>Пробный период активирован!</b>

☂️ <b>ixxy VPN</b>

━━━━━━━━━━━━━━━━━━

⏳ Срок: <b>3 дня</b>
📅 До: <b>{trial_until}</b>

━━━━━━━━━━━━━━━━━━

🌐 Откройте
<b>«Моя подписка»</b> в меню.

Там можно:

⚡ Добавить в Happ
🚀 Добавить в INCY
📋 Скопировать ссылку

━━━━━━━━━━━━━━━━━━

Приятного использования! ☂️
""",
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
    )


# ============================================================
# ДОКУМЕНТЫ
# ============================================================

@router.message(
    F.text == "📄 Документы"
)
async def documents(message: Message):

    await message.answer(
        """
📄 <b>Документы ixxy VPN</b>

https://bdt2010.github.io/managerorlvpnsite/
""",
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

Если возникли проблемы с подключением,
обратитесь в поддержку:

{SUPPORT}
""",
        parse_mode="HTML",
    )


# ============================================================
# СКРЫТЬ МЕНЮ
# ============================================================

@router.message(
    F.text == "🙈 Скрыть меню"
)
async def hide_menu(message: Message):

    await message.answer(
        """
🙈 <b>Меню скрыто</b>

Нажмите кнопку ниже,
чтобы снова показать меню.
""",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML",
    )

    await message.answer(
        "👇",
        reply_markup=show_menu_keyboard(),
    )


# ============================================================
# ПОКАЗАТЬ МЕНЮ
# ============================================================

@router.callback_query(
    F.data == "show_menu"
)
async def show_menu(callback: CallbackQuery):

    user_id = callback.from_user.id

    await callback.message.answer(
        """
☰ <b>Главное меню снова показано!</b>

Выберите нужный раздел 👇
""",
        reply_markup=main_menu(user_id),
        parse_mode="HTML",
    )

    try:

        await callback.message.delete()

    except Exception:

        pass

    await callback.answer()