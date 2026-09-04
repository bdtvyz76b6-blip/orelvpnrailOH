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
    add_payment,
    activate_subscription,
)

from github_update import (
    get_subscription_link,
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
# ⭐ STARS
# ============================================================

@router.callback_query(
    F.data == "pay_stars"
)
async def pay_stars(
    callback: CallbackQuery,
):

    await callback.message.answer(
        """
⭐ <b>Оплата через Telegram Stars</b>

Выберите тариф:
""",
        reply_markup=stars_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# ⭐ STARS — СОЗДАНИЕ СЧЁТА
# ============================================================

@router.callback_query(
    F.data.startswith("stars_")
)
async def stars_buy(
    callback: CallbackQuery,
):

    key = callback.data.replace(
        "stars_",
        "",
    )

    plan = PLANS.get(key)

    if not plan:

        await callback.answer(
            "❌ Ошибка тарифа",
            show_alert=True,
        )

        return

    user_id = callback.from_user.id

    payload = (
        f"vpn_{key}_{user_id}"
    )

    try:

        await callback.message.answer_invoice(

            title="☂️ ixxy vpn",

            description=(
                f"🎫 Подписка — "
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
            "❌ Не удалось создать счёт",
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

@router.message(
    F.successful_payment
)
async def stars_success(
    message: Message,
):

    payment = message.successful_payment

    if not payment:

        return

    payload = payment.invoice_payload

    parts = payload.split("_")

    if len(parts) != 3:

        await message.answer(
            "❌ Ошибка данных платежа."
        )

        return

    try:

        days_key = parts[1]

        payload_user_id = int(
            parts[2]
        )

    except (
        ValueError,
        IndexError,
    ):

        await message.answer(
            "❌ Некорректный платёж."
        )

        return

    # Проверяем пользователя
    if payload_user_id != message.from_user.id:

        await message.answer(
            "❌ Ошибка пользователя платежа."
        )

        return

    plan = PLANS.get(
        days_key
    )

    if not plan:

        await message.answer(
            "❌ Неизвестный тариф."
        )

        return

    user_id = message.from_user.id

    days = plan["days"]

    try:

        # ----------------------------------------------------
        # Получаем существующую ссылку
        # ----------------------------------------------------

        link = get_subscription_link(
            user_id
        )

        # ----------------------------------------------------
        # Активируем подписку в БД
        # ----------------------------------------------------

        new_until = activate_subscription(
            user_id,
            link,
            days,
        )

        # ----------------------------------------------------
        # Обновляем файл Happ
        # ----------------------------------------------------

        if new_until:

            update_subscription_file(
                user_id,
                new_until,
            )

        else:

            update_subscription_file(
                user_id,
                None,
            )

        # ----------------------------------------------------
        # Сохраняем платёж
        # ----------------------------------------------------

        add_payment(
            user_id,
            payment.total_amount,
            days,
            payment.telegram_payment_charge_id,
        )

    except Exception as e:

        print(
            "❌ STARS ACTIVATION ERROR:",
            repr(e),
        )

        await message.answer(
            """
⚠️ Оплата получена.

Но при выдаче подписки произошла ошибка.
Администратор уже уведомлён.
"""
        )

        return

    await message.answer(
f"""
🎉 <b>Оплата получена!</b>

☂️ ixxy vip активирован

🎫 Тариф:
{plan['title']}

📅 Срок:
{days} дней

🔗 <b>Ваша подписка:</b>

{link}
""",
        parse_mode="HTML",
    )


# ============================================================
# 💳 СБП
# ============================================================

@router.callback_query(
    F.data == "pay_sbp"
)
async def pay_sbp(
    callback: CallbackQuery,
):

    await callback.message.answer(
        """
💳 <b>Оплата через СБП</b>

Выберите тариф:
""",
        reply_markup=sbp_keyboard(),
        parse_mode="HTML",
    )

    await callback.answer()


# ============================================================
# 💳 СБП — СОЗДАНИЕ ПЛАТЕЖА
# ============================================================

@router.callback_query(
    F.data.startswith("sbp_")
)
async def sbp_buy(
    callback: CallbackQuery,
):

    key = callback.data.replace(
        "sbp_",
        "",
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

    try:

        result = create_cashera_payment(
            user_id=user_id,
            amount=amount,
            days=days,
        )

    except Exception as e:

        print(
            "❌ CASHeRA CREATE ERROR:",
            repr(e),
        )

        await callback.message.answer(
            """
❌ Не удалось создать платёж.

Попробуйте ещё раз.
"""
        )

        return

    print(
        "💳 CASHeRA RESPONSE:",
        result,
    )

    if not isinstance(
        result,
        dict,
    ):

        await callback.message.answer(
            "❌ Cashera вернул некорректный ответ."
        )

        return

    # --------------------------------------------------------
    # ID ТРАНЗАКЦИИ
    # --------------------------------------------------------

    payment_uuid = (

        result.get("uuid")

        or result.get("id")

        or result.get("transaction_id")

    )

    # --------------------------------------------------------
    # ССЫЛКА НА ОПЛАТУ
    # --------------------------------------------------------

    payment_url = (

        result.get("payment_url")

        or result.get("url")

        or result.get("payment_link")

        or result.get("pay_url")

    )

    if not payment_uuid:

        print(
            "❌ CASHeRA UUID NOT FOUND"
        )

        await callback.message.answer(
            """
❌ Cashera не вернул ID платежа.

Обратитесь в поддержку.
"""
        )

        return

    if not payment_url:

        print(
            "❌ CASHeRA PAYMENT URL NOT FOUND"
        )

        await callback.message.answer(
            """
❌ Cashera не вернул ссылку на оплату.

Обратитесь в поддержку.
"""
        )

        return

    # --------------------------------------------------------
    # СОХРАНЯЕМ ПЛАТЁЖ
    # --------------------------------------------------------

    try:

        add_payment(
            user_id=user_id,
            photo="",
            days=days,
        )

    except TypeError:

        try:

            add_payment(
                user_id,
                "",
                days,
            )

        except Exception as e:

            print(
                "❌ ADD PAYMENT ERROR:",
                repr(e),
            )

    except Exception as e:

        print(
            "❌ ADD PAYMENT ERROR:",
            repr(e),
        )

    # --------------------------------------------------------
    # СОХРАНЯЕМ ID CASHeRA
    # --------------------------------------------------------

    try:

        from database import save_payment_id

        save_payment_id(
            user_id=user_id,
            payment_id=str(
                payment_uuid
            ),
        )

    except Exception as e:

        print(
            "❌ SAVE PAYMENT ID ERROR:",
            repr(e),
        )

    # --------------------------------------------------------
    # КНОПКА ОПЛАТЫ
    # --------------------------------------------------------

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

    await callback.message.answer(
f"""
💳 <b>Счёт на оплату</b>

☂️ ixxy vip

🎫 Тариф:
{plan['title']}

📅 Срок:
{days} дней

💰 Стоимость:
{amount} ₽

Нажмите кнопку ниже для оплаты.

После успешной оплаты подписка активируется автоматически.
""",
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )