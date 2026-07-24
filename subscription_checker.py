import asyncio

from database import get_expired_users
from github_update import expire_subscription



async def check_subscriptions(bot=None):

    while True:

        try:

            users = get_expired_users()


            for user_id in users:

                try:

                    # Меняем GitHub файл на истёкшую подписку
                    expire_subscription(
                        user_id
                    )


                    print(
                        f"⛔ Подписка истекла: {user_id}"
                    )


                    # Сообщение пользователю
                    if bot:

                        try:

                            await bot.send_message(
                                user_id,

                                "⛔ Ваша подписка Orel VPN закончилась.\n\n"
                                "Для продления обратитесь к:\n"
                                "@orelvpntopbot"
                            )

                        except Exception as e:

                            print(
                                "Ошибка отправки сообщения:",
                                e
                            )


                except Exception as e:

                    print(
                        f"Ошибка обработки {user_id}:",
                        e
                    )


        except Exception as e:

            print(
                "Ошибка проверки подписок:",
                e
            )


        # Проверять каждый час
        await asyncio.sleep(3600)