@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    import asyncio
    import traceback

    from database import (
        get_user,
        save_subscription_link,
        mark_payment_paid,
        payment_already_paid,
        activate_paid_subscription,
    )

    try:
        data = request.get_json(silent=True) or {}

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("💳 CASHeRA WEBHOOK")
        print(data)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

        event = data.get("event")

        # Тестовый webhook от Cashera
        if event == "webhook.test":
            print("✅ Webhook test")
            return "OK", 200

        # Нас интересует только изменение статуса транзакции
        if event != "transaction.status_updated":
            print(f"ℹ️ Неинтересующее событие: {event}")
            return "OK", 200

        transaction = data.get("transaction") or {}

        transaction_uuid = str(
            transaction.get("uuid") or ""
        ).strip()

        external_id = str(
            transaction.get("external_id") or ""
        ).strip()

        status = str(
            transaction.get("status") or ""
        ).strip().lower()

        amount = transaction.get("amount", 0)

        currency = str(
            transaction.get("currency") or ""
        ).upper()

        payment_method = str(
            transaction.get("payment_method") or ""
        ).lower()

        print("UUID:", transaction_uuid)
        print("EXTERNAL ID:", external_id)
        print("STATUS:", status)
        print("AMOUNT:", amount)
        print("CURRENCY:", currency)
        print("METHOD:", payment_method)

        # Оплата считается успешной только при paid
        if status != "paid":
            print(f"ℹ️ Оплата ещё не успешна: {status}")
            return "OK", 200

        # Проверяем валюту
        if currency != "RUB":
            print(
                f"❌ Неверная валюта: {currency}"
            )
            return "OK", 200

        # Проверяем external_id
        if not external_id:
            print("❌ Отсутствует external_id")
            return "OK", 200

        # Наш external_id:
        #
        # 123456789_550e8400-e29b-41d4-a716-446655440000
        #
        # Telegram ID находится до первого "_"

        user_id_str = external_id.split("_", 1)[0]

        if not user_id_str.isdigit():
            print(
                f"❌ Не удалось определить Telegram ID: "
                f"{external_id}"
            )
            return "OK", 200

        user_id = int(user_id_str)

        print("👤 USER ID:", user_id)

        # ---------------------------------------------------------
        # Определяем тариф по сумме
        # ---------------------------------------------------------

        try:
            amount = int(amount)
        except Exception:
            print("❌ Некорректная сумма")
            return "OK", 200

        tariffs = {
            12900: 30,
            37900: 90,
            65900: 180,
            108900: 365,
        }

        days = tariffs.get(amount)

        if days is None:
            print(
                f"❌ Неизвестная сумма: {amount}"
            )
            print(
                "Разрешённые суммы:",
                list(tariffs.keys())
            )
            return "OK", 200

        print(
            f"✅ Тариф определён: "
            f"{amount / 100:.2f} RUB → {days} дней"
        )

        # ---------------------------------------------------------
        # Проверяем пользователя
        # ---------------------------------------------------------

        user = get_user(user_id)

        if not user:
            print(
                f"❌ Пользователь {user_id} "
                f"не найден в БД"
            )
            return "OK", 200

        # ---------------------------------------------------------
        # Защита от повторного начисления
        # ---------------------------------------------------------

        if transaction_uuid:
            if payment_already_paid(transaction_uuid):
                print(
                    "ℹ️ Этот платёж уже обработан:"
                    f" {transaction_uuid}"
                )
                return "OK", 200

        # ---------------------------------------------------------
        # Создаём / обновляем VPN-подписку
        # ---------------------------------------------------------

        print(
            f"🔄 Создаю подписку "
            f"{user_id} на {days} дней..."
        )

        from github_update import create_subscription

        # create_subscription:
        #
        # 1. загружает servers.txt
        # 2. создаёт subscription content
        # 3. сохраняет content в БД
        # 4. сохраняет subscription_link
        #
        link = create_subscription(
            user_id=user_id,
            days=days,
        )

        if not link:
            raise RuntimeError(
                "create_subscription() "
                "не вернул ссылку"
            )

        print(
            f"🔗 Ссылка подписки: {link}"
        )

        # ---------------------------------------------------------
        # Начисляем дни в БД
        # ---------------------------------------------------------

        new_until = activate_paid_subscription(
            user_id=user_id,
            link=link,
            days=days,
        )

        print(
            f"📅 Новая дата окончания: "
            f"{new_until}"
        )

        # ---------------------------------------------------------
        # Отмечаем платёж как оплаченный
        # ---------------------------------------------------------

        if transaction_uuid:
            mark_payment_paid(
                transaction_uuid
            )

        # ---------------------------------------------------------
        # Отправляем сообщение пользователю
        # ---------------------------------------------------------

        message = f"""
☂️ <b>ixxy VPN</b>

✅ <b>Оплата успешно получена!</b>

👑 Тариф: Орёл VPN
📅 Начислено: <b>{days} дней</b>
📆 Действует до: <b>{datetime.strptime(new_until, "%Y-%m-%d").strftime("%d.%m.%Y")}</b>

🔗 <b>Ваша подписка:</b>

{link}

📲 Добавьте ссылку в Happ.

Спасибо за покупку! ❤️
"""

        try:
            asyncio.run(
                bot.send_message(
                    user_id,
                    message,
                    parse_mode="HTML",
                )
            )

            print(
                f"📨 Сообщение отправлено "
                f"пользователю {user_id}"
            )

        except Exception as telegram_error:

            print(
                "⚠️ Подписка выдана, "
                "но сообщение Telegram "
                "не отправилось:"
            )

            print(telegram_error)

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ ПЛАТЁЖ ОБРАБОТАН")
        print(f"👤 Пользователь: {user_id}")
        print(f"💰 Сумма: {amount / 100:.2f} ₽")
        print(f"📅 Дней: {days}")
        print(f"📆 До: {new_until}")
        print(f"🔗 Ссылка: {link}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "OK", 200

    except Exception as e:

        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("❌ ОШИБКА CASHeRA WEBHOOK")
        print(str(e))
        traceback.print_exc()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━")

        # Возвращаем 500, чтобы Cashera могла
        # повторить webhook при серверной ошибке.
        return "Webhook error", 500