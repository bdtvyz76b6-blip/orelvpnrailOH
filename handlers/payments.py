from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)

from database import (
    create_payment,
    process_paid_payment,
    get_subscription_link,
)

from github_update import (
    create_subscription,
    update_subscription_file,
)

from cashera_api import (
    create_cashera_payment,
)


router = Router()


# ============================================================
# ТАРИФЫ
# ============================================================

PLANS = {
    "30": {
        "days": 30,
        "stars": 70,
        "rub": 129,
        "title": "1 месяц",
    },
    "90": {
        "days": 90,
        "stars": 190,
        "rub": 379,
        "title": "3 месяца",
    },
    "180": {
        "days": 180,
        "stars": 350,
        "rub": 659,
        "title": "6 месяцев",
    },
    "365": {
        "days": 365,
        "stars": 700,
        "rub": 1089,
        "title": "12 месяцев",
    },
}


# ============================================================
# КЛАВИАТУРА STARS
# ============================================================

def stars_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 месяц — 70 ⭐",
                    callback_data="stars_30",
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца — 190 ⭐",
                    callback_data="stars_90",
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев — 350 ⭐",
                    callback_data="stars_180",
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев — 700 ⭐",
                    callback_data="stars_365",
                )
            ],
        ]
    )


# ============================================================
# КЛАВИАТУРА СБП
# ============================================================

def sbp_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1 месяц — 129 ₽",
                    callback_data="sbp_30",
                )
            ],
            [
                InlineKeyboardButton(
                    text="3 месяца — 379 ₽",
                    callback_data="sbp_90",
                )
            ],
            [
                InlineKeyboardButton(
                    text="6 месяцев — 659 ₽",
                    callback_data="sbp_180",
                )
            ],
            [
                InlineKeyboardButton(
                    text="12 месяцев — 1089 ₽",
                    callback_data="sbp_365",
                )
            ],
        ]
    )


# ============================================================
# ⭐ STARS — МЕНЮ
# ============================================================

@router.callback_query(F.data == "pay_stars")
async def pay_stars(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    await callback.message.answer(
        "⭐ <b>Оплата через Telegram Stars</b>\n\n"
        "Выберите тариф:",
        reply_markup=stars_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ⭐ STARS — СОЗДАНИЕ СЧЁТА
# ============================================================

@router.callback_query(F.data.startswith("stars_"))
async def stars_buy(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    key = callback.data.replace("stars_", "", 1)

    plan = PLANS.get(key)

    if not plan:
        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True,
        )
        return

    user_id = callback.from_user.id

    payload = f"ixxy_stars_{user_id}_{key}"

    try:

        await callback.message.answer_invoice(
            title="☂️ ixxy VPN",
            description=(
                f"Подписка ixxy VPN — "
                f"{plan['title']}"
            ),
            payload=payload,
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=plan["title"],
                    amount=plan["stars"],
                )
            ],
        )

        await callback.answer()

    except Exception as e:

        print(
            "❌ STARS INVOICE ERROR:",
            repr(e),
        )

        await callback.answer(
            "❌ Не удалось создать счёт.",
            show_alert=True,
        )


# ============================================================
# ⭐ STARS — PRE CHECKOUT
# ============================================================

@router.pre_checkout_query()
async def stars_pre_checkout(
    query: PreCheckoutQuery,
):

    try:

        await query.answer(
            ok=True,
        )

    except Exception as e:

        print(
            "❌ PRE CHECKOUT ERROR:",
            repr(e),
        )


# ============================================================
# ⭐ STARS — УСПЕШНАЯ ОПЛАТА
# ============================================================

@router.message(F.successful_payment)
async def stars_success(message: Message):

    payment = message.successful_payment

    if not payment:
        return

    # --------------------------------------------------------
    # PAYLOAD
    # --------------------------------------------------------

    payload = payment.invoice_payload

    parts = payload.split("_")

    # ixxy_stars_USER_ID_DAYS
    if len(parts) != 4 or parts[0] != "ixxy" or parts[1] != "stars":

        await message.answer(
            "❌ Ошибка данных платежа."
        )

        return

    try:

        payload_user_id = int(parts[2])
        days_key = parts[3]

    except (
        ValueError,
        IndexError,
    ):

        await message.answer(
            "❌ Некорректный платёж."
        )

        return

    # --------------------------------------------------------
    # ПРОВЕРКА ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    if payload_user_id != message.from_user.id:

        print(
            "❌ STARS USER MISMATCH:",
            payload_user_id,
            message.from_user.id,
        )

        await message.answer(
            "❌ Ошибка пользователя платежа."
        )

        return

    # --------------------------------------------------------
    # ТАРИФ
    # --------------------------------------------------------

    plan = PLANS.get(days_key)

    if not plan:

        await message.answer(
            "❌ Неизвестный тариф."
        )

        return

    user_id = message.from_user.id
    days = plan["days"]

    # --------------------------------------------------------
    # ID ПЛАТЕЖА
    # --------------------------------------------------------

    payment_id = str(
        payment.telegram_payment_charge_id
    )

    # --------------------------------------------------------
    # ССЫЛКА ПОЛЬЗОВАТЕЛЯ
    # --------------------------------------------------------

    try:

        link = get_subscription_link(
            user_id
        )

        if not link:

            link = create_subscription(
                user_id,
                days=days,
            )

    except Exception as e:

        print(
            "❌ CREATE SUBSCRIPTION ERROR:",
            repr(e),
        )

        await message.answer(
            "⚠️ Оплата получена, но не удалось "
            "подготовить подписку.\n\n"
            "Администратор уже уведомлён."
        )

        return

    # ========================================================
    # СОХРАНЯЕМ ПЛАТЁЖ
    # ========================================================

    try:

        create_payment(
            user_id=user_id,
            payment_id=payment_id,
            amount=payment.total_amount,
            days=days,
            provider="stars",
        )

    except Exception as e:

        # Возможная повторная обработка одного
        # и того же Telegram-платежа
        print(
            "❌ STARS CREATE PAYMENT ERROR:",
            repr(e),
        )

        # Если платеж уже существует, всё равно
        # пытаемся корректно обработать его ниже.

    # ========================================================
    # АКТИВИРУЕМ / ПРОДЛЕВАЕМ ПОДПИСКУ
    # ========================================================

    try:

        result = process_paid_payment(
            payment_id
        )

        if not result:

            raise RuntimeError(
                "process_paid_payment returned empty result"
            )

        if result.get("already_paid"):

            new_until = result.get(
                "subscription_until"
            )

        else:

            new_until = result.get(
                "subscription_until"
            )

        # ----------------------------------------------------
        # ОБНОВЛЯЕМ GITHUB
        # ----------------------------------------------------

        if new_until:

            update_subscription_file(
                user_id,
                new_until,
            )

    except Exception as e:

        print(
            "❌ STARS ACTIVATION ERROR:",
            repr(e),
        )

        await message.answer(
            "⚠️ <b>Оплата получена.</b>\n\n"
            "Но при активации подписки произошла "
            "техническая ошибка.\n\n"
            "Администратор уже уведомлён.",
            parse_mode="HTML",
        )

        return

    # ========================================================
    # УСПЕШНЫЙ ОТВЕТ
    # ========================================================

    until_text = ""

    if new_until:

        try:
            until_text = new_until.strftime(
                "%d.%m.%Y %H:%M"
            )
        except Exception:
            until_text = str(new_until)

    text = (
        "🎉 <b>Оплата получена!</b>\n\n"
        "☂️ <b>ixxy VPN активирован</b>\n\n"
        f"🎫 Тариф: <b>{plan['title']}</b>\n"
        f"📅 Добавлено: <b>{days} дней</b>\n"
    )

    if until_text:

        text += (
            f"⏰ Действует до: "
            f"<b>{until_text}</b>\n"
        )

    text += (
        "\n🔗 <b>Ваша подписка:</b>\n\n"
        f"<code>{link}</code>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
    )


# ============================================================
# 💳 СБП — МЕНЮ
# ============================================================

@router.callback_query(F.data == "pay_sbp")
async def pay_sbp(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    await callback.message.answer(
        "💳 <b>Оплата через СБП</b>\n\n"
        "Выберите тариф:",
        reply_markup=sbp_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 💳 СБП — СОЗДАНИЕ ПЛАТЕЖА
# ============================================================

@router.callback_query(F.data.startswith("sbp_"))
async def sbp_buy(callback: CallbackQuery):

    if not callback.message:
        await callback.answer()
        return

    key = callback.data.replace(
        "sbp_",
        "",
        1,
    )

    plan = PLANS.get(key)

    if not plan:

        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True,
        )

        return

    user_id = callback.from_user.id
    amount = plan["rub"]
    days = plan["days"]

    await callback.answer(
        "⏳ Создаю платёж..."
    )

    # ========================================================
    # CASHeRA
    # ========================================================

    try:

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days,
        )

    except Exception as e:

        print(
            "❌ CASHERA CREATE ERROR:",
            repr(e),
        )

        await callback.message.answer(
            "❌ <b>Не удалось создать платёж.</b>\n\n"
            "Попробуйте ещё раз.",
            parse_mode="HTML",
        )

        return

    print(
        "💳 CASHERA RESPONSE:",
        result,
    )

    if not isinstance(result, dict):

        await callback.message.answer(
            "❌ CasheRa вернул некорректный ответ."
        )

        return

    # ========================================================
    # ID ТРАНЗАКЦИИ
    # ========================================================

    payment_uuid = (
        result.get("uuid")
        or result.get("id")
        or result.get("transaction_id")
    )

    # ========================================================
    # ССЫЛКА НА ОПЛАТУ
    # ========================================================

    payment_url = (
        result.get("payment_url")
        or result.get("url")
        or result.get("payment_link")
        or result.get("pay_url")
    )

    if not payment_uuid:

        print(
            "❌ CASHERA UUID NOT FOUND:",
            result,
        )

        await callback.message.answer(
            "❌ CasheRa не вернул ID платежа.\n\n"
            "Обратитесь в поддержку."
        )

        return

    if not payment_url:

        print(
            "❌ CASHERA PAYMENT URL NOT FOUND:",
            result,
        )

        await callback.message.answer(
            "❌ CasheRa не вернул ссылку на оплату.\n\n"
            "Обратитесь в поддержку."
        )

        return

    # ========================================================
    # СОХРАНЯЕМ ПЛАТЁЖ В POSTGRES
    # ========================================================

    try:

        create_payment(
            user_id=user_id,
            payment_id=str(payment_uuid),
            amount=amount * 100,
            days=days,
            provider="cashera",
        )

    except Exception as e:

        print(
            "❌ CASHERA CREATE_PAYMENT ERROR:",
            repr(e),
        )

        await callback.message.answer(
            "❌ Не удалось сохранить платёж.\n\n"
            "Попробуйте ещё раз или обратитесь "
            "в поддержку."
        )

        return

    # ========================================================
    # КНОПКА ОПЛАТЫ
    # ========================================================

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 Оплатить через СБП",
                    url=payment_url,
                )
            ]
        ]
    )

    # ========================================================
    # ОТВЕТ
    # ========================================================

    await callback.message.answer(
        "💳 <b>Счёт на оплату</b>\n\n"
        "☂️ <b>ixxy VPN</b>\n\n"
        f"🎫 Тариф: <b>{plan['title']}</b>\n"
        f"📅 Срок: <b>{days} дней</b>\n"
        f"💰 Стоимость: <b>{amount} ₽</b>\n\n"
        "Нажмите кнопку ниже для оплаты.\n\n"
        "После успешной оплаты подписка "
        "активируется автоматически.",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )