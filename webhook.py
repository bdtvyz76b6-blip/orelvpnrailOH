@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    import traceback

    data = request.json

    print("💳 CASHeRA PAYMENT:")
    print(data)


    try:

        # тестовый webhook
        if data.get("event") == "webhook.test":
            return "OK", 200


        # только изменение статуса
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



        # Получаем Telegram ID
        external_id = transaction.get(
            "external_id",
            ""
        )


        # external_id теперь:
        # 123456789_abcd1234
        # берём только Telegram ID

        user_id = external_id.split("_")[0]



        amount = int(
            transaction.get(
                "amount",
                0
            )
        )


        print(
            "AMOUNT:",
            amount
        )


        print(
            "EXTERNAL ID:",
            external_id
        )



        days = 0


        # Cashera отдаёт копейки

        if amount == 9900:

            days = 30


        elif amount == 24900:

            days = 90


        elif amount == 59900:

            days = 180


        elif amount == 99900:

            days = 365



        if not user_id:

            print(
                "Нет Telegram ID"
            )

            return "OK", 200



        if days == 0:

            print(
                "Срок не определён"
            )

            return "OK", 200



        user_id = int(
            user_id
        )


        print(
            "USER:",
            user_id
        )



        # создаём VPN подписку

        link = create_subscription(
            user_id=user_id,
            days=days
        )


        print(
            "LINK:",
            link
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
            "✅ Подписка выдана:",
            user_id
        )



    except Exception:

        traceback.print_exc()



    return "OK", 200