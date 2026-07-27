@app.route("/webhook/cashera", methods=["POST"])
def cashera():

    data = request.json

    print("💳 CASHeRA:")
    print(data)

    try:

        # Пример — потом поменяем под настоящий JSON
        status = data.get("status", "")

        if status == "paid":

            user_id = int(
                data.get("user_id", 0)
            )

            amount = int(
                data.get("amount", 0)
            )

            days = 0

            if amount == 70:
                days = 30

            elif amount == 190:
                days = 90

            elif amount == 350:
                days = 180

            elif amount == 700:
                days = 365


            if user_id and days:

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

⏳ Срок:
{days} дней

🔗 Ваша подписка:

{link}

📲 Добавьте её в Happ.
"""
                    )
                )

    except Exception as e:

        print(
            "ERROR:",
            e
        )

    return "OK", 200