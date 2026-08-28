from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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
    accept_terms
)

from keyboards import (
    main_menu,
    payment_method_keyboard,
    stars_buy_keyboard,
    sbp_buy_keyboard,
    accept_terms_keyboard
)

from github_update import (
    create_subscription,
    create_user_subscription
)


router = Router()


# =========================================================
# START
# =========================================================

@router.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id

    # Создаём пользователя
    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # =====================================================
    # СОГЛАШЕНИЕ
    # =====================================================

    if not has_accepted_terms(user_id):

        await message.answer(
            """
☂️ <b>ixxy VPN</b>

<b>Добро пожаловать!</b> 👋

🚀 Быстрый и удобный VPN
🔐 Персональная подписка
🌐 Подключение через Happ и INCY

Перед началом необходимо принять
условия использования.

👇 Нажмите кнопку ниже:
""",
            reply_markup=accept_terms_keyboard(),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ПОЛУЧАЕМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # =====================================================

    link = get_subscription_link(user_id)

    if not link:

        link = create_user_subscription(
            user_id
        )

        save_subscription_link(
            user_id,
            link
        )

    # =====================================================
    # ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЯ
    # =====================================================

    user = get_user(user_id)

    status = "🔴 Не активна"
    until_text = "—"

    if user:

        until = user[4]

        if until:

            try:

                date = datetime.strptime(
                    str(until),
                    "%Y-%m-%d"
                )

                until_text = date.strftime(
                    "%d.%m.%Y"
                )

                if date.date() >= datetime.now().date():

                    status = "🟢 Активна"

                else:

                    status = "🔴 Истекла"

            except Exception:

                status = "🔴 Не активна"

    # =====================================================
    # ТИТУЛЬНОЕ МЕНЮ
    # =====================================================

    await message.answer(
        f"""
☂️ <b>ixxy VPN</b>

<b>Добро пожаловать, {message.from_user.first_name}! 👋</b>

━━━━━━━━━━━━━━━━━━

🛡 <b>Ваш VPN готов к работе</b>

🎫 <b>Статус:</b> {status}
📅 <b>До:</b> {until_text}

🔗 <b>Персональная подписка</b>
создана и закреплена за вами.

━━━━━━━━━━━━━━━━━━

📱 <b>Подключение</b>

🌐 Откройте <b>«Моя подписка»</b>
и добавьте VPN в:

🟢 Happ
🟣 INCY

━━━━━━━━━━━━━━━━━━

💎 <b>Что доступно:</b>

🎫 Купить подписку
🎁 Получить пробный период
👤 Личный кабинет
🌐 Моя подписка
💬 Поддержка

👇 <b>Выберите нужный раздел:</b>
""",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ПРИНЯТИЕ УСЛОВИЙ
# =========================================================

@router.callback_query(
    F.data == "accept_terms"
)
async def accept(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    add_user(
        user_id,
        callback.from_user.username,
        callback.from_user.first_name
    )

    accept_terms(user_id)

    # =====================================================
    # СОЗДАЁМ ПЕРСОНАЛЬНУЮ ССЫЛКУ
    # =====================================================

    link = get_subscription_link(user_id)

    if not link:

        link = create_user_subscription(
            user_id
        )

        save_subscription_link(
            user_id,
            link
        )

    # =====================================================
    # УДАЛЯЕМ СТАРОЕ СООБЩЕНИЕ
    # =====================================================

    try:

        await callback.message.delete()

    except Exception:

        pass

    # =====================================================
    # ГЛАВНОЕ МЕНЮ
    # =====================================================

    await callback.message.answer(
        f"""
✅ <b>Условия приняты!</b>

☂️ <b>Добро пожаловать в ixxy VPN!</b>

Ваша персональная подписка создана.

━━━━━━━━━━━━━━━━━━

🔗 <b>Ваша подписка</b>

<code>{link}</code>

━━━━━━━━━━━━━━━━━━

📱 Подключить VPN можно через:

🟢 <b>Happ</b>
🟣 <b>INCY</b>

🌐 Просто откройте
<b>«Моя подписка»</b> в меню.

👇 <b>Главное меню уже доступно:</b>
""",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# КУПИТЬ ПОДПИСКУ
# =========================================================

@router.message(
    F.text == "🎫 Купить подписку"
)
async def buy(
    message: Message
):

    await message.answer(
        """
☂️ <b>ixxy VPN</b>

💎 <b>Выберите способ оплаты:</b>

⭐ Telegram Stars
💳 СБП
""",
        reply_markup=payment_method_keyboard(),
        parse_mode="HTML"
    )


# =========================================================
# TELEGRAM STARS
# =========================================================

@router.callback_query(
    F.data == "pay_stars"
)
async def stars(
    callback: CallbackQuery
):

    await callback.message.answer(
        """
⭐ <b>Telegram Stars</b>

Выберите срок подписки:
""",
        reply_markup=stars_buy_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# СБП
# =========================================================

@router.callback_query(
    F.data == "pay_sbp"
)
async def sbp(
    callback: CallbackQuery
):

    await callback.message.answer(
        """
💳 <b>Оплата СБП</b>

Выберите срок подписки:
""",
        reply_markup=sbp_buy_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# ПРОБНЫЙ ПЕРИОД
# =========================================================

@router.message(
    F.text == "🎁 Пробный период"
)
async def trial(
    message: Message
):

    user_id = message.from_user.id

    add_user(
        user_id,
        message.from_user.username,
        message.from_user.first_name
    )

    # =====================================================
    # СОГЛАШЕНИЕ
    # =====================================================

    if not has_accepted_terms(user_id):

        await message.answer(
            """
☂️ <b>Сначала примите условия использования.</b>

После этого вам станет доступен
🎁 <b>пробный период на 3 дня.</b>
""",
            reply_markup=accept_terms_keyboard(),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ПРОВЕРКА TRIAL
    # =====================================================

    if check_trial(user_id):

        await message.answer(
            """
❌ <b>Пробный период уже использован.</b>

Вы можете приобрести полноценную
подписку в разделе:

🎫 <b>Купить подписку</b>
""",
            parse_mode="HTML"
        )

        return

    # =====================================================
    # СОЗДАЁМ ПОДПИСКУ
    # =====================================================

    link = create_subscription(
        user_id,
        days=3
    )

    activate_trial(
        user_id,
        link
    )

    save_subscription_link(
        user_id,
        link
    )

    # =====================================================
    # ДАТА
    # =====================================================

    trial_until = (
        datetime.now().date()
        + timedelta(days=3)
    ).strftime("%d.%m.%Y")

    # =====================================================
    # ОТВЕТ
    # =====================================================

    await message.answer(
        f"""
🎉 <b>Пробный период активирован!</b>

☂️ <b>ixxy VPN</b>

━━━━━━━━━━━━━━━━━━

⏳ Срок: <b>3 дня</b>
📅 До: <b>{trial_until}</b>

━━━━━━━━━━━━━━━━━━

🔗 <b>Персональная подписка:</b>

<code>{link}</code>

━━━━━━━━━━━━━━━━━━

📱 Добавить VPN:

🟢 <b>Happ</b>
🟣 <b>INCY</b>

🌐 Все действия доступны
в разделе <b>«Моя подписка»</b>.
""",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================================================
# ДОКУМЕНТЫ
# =========================================================

@router.message(
    F.text == "📄 Документы"
)
async def documents(
    message: Message
):

    await message.answer(
        """
📄 <b>Документы ixxy VPN</b>

Здесь находятся условия
использования сервиса.
 
https://bdt2010.github.io/managerorlvpnsite/
""",
        parse_mode="HTML"
    )


# =========================================================
# ПОДДЕРЖКА
# =========================================================

@router.message(
    F.text == "💬 Поддержка"
)
async def support(
    message: Message
):

    await message.answer(
        f"""
💬 <b>Поддержка ixxy VPN</b>

Если возникли проблемы с подключением
или подпиской — напишите в поддержку.

🛠 <b>Поддержка:</b>
{SUPPORT}
""",
        parse_mode="HTML"
    )