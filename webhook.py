@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    import traceback

    try:

        data = request.json or {}

        print("💳 CASHeRA PAYMENT:")
        print(data)

        # =========================
        # TEST WEBHOOK
        # =========================

        if data.get("event") == "webhook.test":
            return "OK", 200

        # =========================
        # ТОЛЬКО ИЗМЕНЕНИЕ СТАТУСА
        # =========================

        if data.get("event") != "transaction.status_updated":
            return "OK", 200

        transaction = data.get(
            "transaction",
            {}
        )

        # =========================
        # СТАТУС
        # =========================

        status = transaction.get(
            "status"
        )

        print(
            "STATUS:",
            status
        )

        if status != "paid":

            print(
                "⏳ Оплата ещё не успешна:",
                status
            )

            return "OK", 200

        # =========================
        # TELEGRAM ID
        # =========================

        external_id = transaction.get(
            "external_id",
            ""
        )

        print(
            "EXTERNAL ID:",
            external_id
        )

        if not external_id:

            print(
                "❌ Нет external_id"
            )

            return "OK", 200

        # Формат:
        # 123456789_abcd1234

        try:

            user_id = int(
                external_id.split("_")[0]
            )

        except Exception:

            print(
                "❌ Не удалось получить Telegram ID"
            )

            return "OK", 200

        print(
            "USER:",
            user_id
        )

        # =========================
        # СУММА
        # =========================

        amount = transaction.get(
            "amount",
            0
        )

        try:

            amount = int(
                float(amount)
            )

        except Exception:

            print(
                "❌ Некорректная сумма:",
                amount
            )

            return "OK", 200

        print(
            "AMOUNT:",
            amount
        )

        # =========================
        # ОПРЕДЕЛЯЕМ ТАРИФ
        # =========================
        #
        # Cashera отдаёт копейки
        #
        # 129 ₽   = 12900
        # 379 ₽   = 37900
        # 659 ₽   = 65900
        # 1089 ₽  = 108900
        #

        tariff_days = {

            12900: 30,

            37900: 90,

            65900: 180,

            108900: 365

        }

        days = tariff_days.get(
            amount,
            0
        )

        print(
            "DAYS:",
            days
        )

        if days == 0:

            print(
                "❌ Срок не определён для суммы:",
                amount
            )

            return "OK", 200

        # =========================
        # СОЗДАЁМ VPN ПОДПИСКУ
        # =========================

        print(
            "🔐 Создание подписки..."
        )

        result = create_subscription(
            user_id=user_id,
            days=days
        )

        print(
            "SUBSCRIPTION RESULT:",
            result
        )

        # =========================
        # ПОЛУЧАЕМ ССЫЛКУ
        # =========================

        link = ""

        if isinstance(result, str):

            link = result

        elif isinstance(result, dict):

            link = (
                result.get("link")
                or result.get("url")
                or result.get("subscription_link")
                or ""
            )

        if not link:

            print(
                "❌ create_subscription не вернул ссылку"
            )

            return "OK", 200

        print(
            "🔗 LINK:",
            link
        )

        # =========================
        # СОХРАНЯЕМ ССЫЛКУ
        # =========================

        save_subscription_link(
            user_id,
            link
        )

        print(
            "✅ Ссылка сохранена"
        )

        # =========================
        # СОХРАНЯЕМ CONTENT
        # =========================
        #
        # Если create_subscription()
        # возвращает только ссылку,
        # content здесь получить нельзя.
        #
        # Если функция возвращает dict
        # с content — сохраняем его.
        #

        if isinstance(result, dict):

            content = (
                result.get("content")
                or result.get("subscription_content")
                or ""
            )

            if content:

                save_subscription_content(
                    user_id,
                    content
                )

                print(
                    "✅ Subscription content сохранён"
                )

        # =========================
        # УВЕДОМЛЯЕМ ПОЛЬЗОВАТЕЛЯ
        # =========================

        asyncio.run(

            bot.send_message(

                user_id,

                f"""
☂️ ixxy VPN

✅ Оплата получена!

📅 Срок:
{days} дней

💰 Оплачено:
{amount / 100:.2f} ₽

🔗 Ваша подписка:

{link}

📲 Добавьте её в Happ.
"""

            )

        )

        print(
            "✅ Подписка выдана:",
            user_id,
            days,
            "дней"
        )

    except Exception:

        traceback.print_exc()

    return "OK", 200