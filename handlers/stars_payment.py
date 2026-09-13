from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    Message,
)

from database import (
    create_payment,
    process_paid_payment,
)

from github_update import create_subscription


router = Router()


# ============================================================
# ТАРИФЫ TELEGRAM STARS
# ============================================================

PLANS = {
    "stars_30": {
        "days": 30,
        "stars": 70,
    },
    "stars_90": {
        "days": 90,
        "stars": 190,
    },
    "stars_180": {
        "days": 180,
        "stars": 350,
    },
    "stars_365": {
        "days": 365,
        "stars": 700,
    },
}


# ============================================================
# ПОКУПКА
# ============================================================

@router.callback_query(F.data.startswith("stars_"))
async def stars_buy(callback: CallbackQuery):
    plan = PLANS.get(callback.data)

    if not plan:
        await callback.answer(
            "❌ Тариф не найден",
            show_alert=True,
        )
        return

    days = plan["days"]
    stars = plan["stars"]

    try:
        await callback.message.answer_invoice(
            title="☂️ ixxy VPN",
            description=f"Подписка ixxy VPN на {days} дней",
            payload=f"ixxy_stars_{callback.from_user.id}_{days}",
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=f"☂️ ixxy VPN — {days} дней",
                    amount=stars,
                )
            ],
        )

        await callback.answer()

    except Exception as e:
        print(f"❌ Ошибка создания Stars-счёта: {e}")

        await callback.answer(
            "❌ Не удалось создать счёт",
            show_alert=True,
        )


# ============================================================
# PRE-CHECKOUT
# ============================================================

@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    try:
        payload = query.invoice_payload

        parts = payload.split("_")

        if len(parts) != 4:
            await query.answer(
                ok=False,
                error_message="Некорректный платёж.",
            )
            return

        if parts[0] != "ixxy" or parts[1] != "stars":
            await query.answer(
                ok=False,
                error_message="Некорректный платёж.",
            )
            return

        user_id = int(parts[2])
        days = int(parts[3])

        if user_id != query.from_user.id:
            await query.answer(
                ok=False,
                error_message="Платёж принадлежит другому пользователю.",
            )
            return

        valid_days = {30, 90, 180, 365}

        if days not in valid_days:
            await query.answer(
                ok=False,
                error_message="Некорректный тариф.",
            )
            return

        await query.answer(ok=True)

    except Exception as e:
        print(f"❌ Ошибка PreCheckout Stars: {e}")

        try:
            await query.answer(
                ok=False,
                error_message="Не удалось проверить платёж.",
            )
        except Exception:
            pass


# ============================================================
# УСПЕШНАЯ ОПЛАТА
# ============================================================

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    payment = message.successful_payment

    if not payment:
        return

    try:
        payload = payment.invoice_payload

        parts = payload.split("_")

        if len(parts) != 4:
            await message.answer(
                "❌ Некорректные данные платежа."
            )
            return

        if parts[0] != "ixxy" or parts[1] != "stars":
            await message.answer(
                "❌ Некорректный платёж."
            )
            return

        user_id = int(parts[2])
        days = int(parts[3])

        if user_id != message.from_user.id:
            await message.answer(
                "❌ Ошибка пользователя платежа."
            )
            return

        # ----------------------------------------------------
        # Проверяем тариф
        # ----------------------------------------------------

        plan = None

        for item in PLANS.values():
            if item["days"] == days:
                plan = item
                break

        if not plan:
            await message.answer(
                "❌ Тариф не найден."
            )
            return

        expected_stars = plan["stars"]

        # ----------------------------------------------------
        # Проверяем сумму
        # ----------------------------------------------------

        if payment.total_amount != expected_stars:
            print(
                "⚠️ Несовпадение суммы Stars: "
                f"user={user_id}, "
                f"expected={expected_stars}, "
                f"received={payment.total_amount}"
            )

            await message.answer(
                "❌ Сумма платежа не соответствует тарифу."
            )
            return

        # ----------------------------------------------------
        # ID платежа Telegram
        # ----------------------------------------------------

        payment_id = payment.telegram_payment_charge_id

        if not payment_id:
            await message.answer(
                "❌ Не удалось получить ID платежа."
            )
            return

        # ----------------------------------------------------
        # Сохраняем платёж в PostgreSQL
        #
        # Если платёж уже существует — повторно не создаём.
        # ----------------------------------------------------

        try:
            create_payment(
                user_id=user_id,
                payment_id=payment_id,
                amount=payment.total_amount,
                days=days,
                provider="stars",
            )
        except Exception as e:
            # UNIQUE(payment_id) может сработать при повторной
            # доставке одного и того же Telegram-платежа.
            print(
                f"ℹ️ Stars payment уже существует "
                f"или ошибка сохранения: {e}"
            )

        # ----------------------------------------------------
        # Создаём/обновляем файл подписки GitHub
        # ----------------------------------------------------

        link = create_subscription(
            user_id=user_id,
            days=days,
        )

        if not link:
            await message.answer(
                "⚠️ Платёж получен, но не удалось создать "
                "ссылку подписки.\n\n"
                "Обратитесь в поддержку."
            )
            return

        # ----------------------------------------------------
        # Атомарно зачисляем оплату
        #
        # process_paid_payment:
        # - проверяет payment_id
        # - не даёт начислить повторно
        # - продлевает подписку
        # - переводит платёж в paid
        # ----------------------------------------------------

        result = process_paid_payment(payment_id)

        if not result:
            await message.answer(
                "⚠️ Платёж уже был обработан или не найден.\n\n"
                f"🔗 Ваша подписка:\n{link}"
            )
            return

        # ----------------------------------------------------
        # Дата окончания
        # ----------------------------------------------------

        subscription_until = result.get(
            "subscription_until"
        )

        if subscription_until:
            try:
                until_text = subscription_until.strftime(
                    "%d.%m.%Y"
                )
            except Exception:
                until_text = str(subscription_until)
        else:
            until_text = "—"

        # ----------------------------------------------------
        # Ответ пользователю
        # ----------------------------------------------------

        await message.answer(
            f"""
🎉 <b>Оплата получена!</b>

☂️ <b>ixxy VPN активирован</b>

⏳ Срок: <b>{days} дней</b>
📅 Активен до: <b>{until_text}</b>

🔗 <b>Ваша подписка:</b>

{link}

<i>Добавьте ссылку в Happ или другой поддерживаемый клиент.</i>
""",
            parse_mode="HTML",
        )

        print(
            f"✅ Stars оплата обработана: "
            f"user={user_id}, "
            f"days={days}, "
            f"stars={payment.total_amount}, "
            f"payment_id={payment_id}"
        )

    except ValueError as e:
        print(f"❌ Ошибка данных Stars-платежа: {e}")

        await message.answer(
            "❌ Некорректные данные платежа."
        )

    except Exception as e:
        print(
            f"❌ Ошибка обработки Stars-платежа: "
            f"{type(e).__name__}: {e}"
        )

        await message.answer(
            "⚠️ Платёж получен, но произошла ошибка "
            "при активации подписки.\n\n"
            "Обратитесь в поддержку."
        )