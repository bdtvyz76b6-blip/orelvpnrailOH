@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    data = request.json

    print("💳 CASHeRA:")
    print(data)


    try:

        # тестовое событие
        if data.get("event") == "webhook.test":
            return "OK", 200


        if data.get("event") != "transaction.status_updated":
            return "OK", 200


        transaction = data.get(
            "transaction",
            {}
        )


        status = transaction.get(
            "status"
        )


        if status != "paid":

            print(
                "Оплата не успешна:",
                status
            )

            return "OK", 200



        # Telegram ID должен быть в external_id
        user_id = transaction.get(
            "external_id"
        )


        amount = int(
            transaction.get(
                "amount",
                0
            )
        )



        days = 0


        if amount == 99:
            days = 30

        elif amount == 249:
            days = 90

        elif amount == 599:
            days = 180

        elif amount == 999:
            days = 365



        if not user_id or not days:

            print(
                "Нет user_id или срок не найден"
            )

            return "OK", 200



        user_id = int(
            user_id
        )



        link = create_subscription(
            user_id,
            days=days
        )


        save_subscription_link(
            user_id,
            link
        )



        asyncio.run(

            bot.send_message(

                user_id,

                f"""
🦅 Орёл VPN

✅ Оплата получена!

📅 Срок:
{days} дней


🔗 Ваша подписка:

{link}


📲 Добавьте её в Happ.
"""

            )

        )


        print(
            "✅ Выдано:",
            user_id
        )



    except Exception as e:

        print(
            "ERROR:",
            e
        )


    return "OK", 200