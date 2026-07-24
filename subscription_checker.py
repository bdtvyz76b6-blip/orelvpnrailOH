import asyncio

from database import get_expired_users
from github_update import expire_subscription



async def check_subscriptions(bot=None):

    while True:

        try:

            users = get_expired_users()


            for user_id in users:

                try:


                    # Меняем sub файл на истёкшую подписку
                    expire_subscription(
                        user_id
                    )


                    print(
                        f"⛔ Подписка истекла: {user_id}"
                    )



                    if bot:

                        try:

                            await bot.send_message(

                                user_id,

                                """
⛔ Орёл VPN


Ваша подписка закончилась.


Для продления нажмите:
👑 Купить подписку


Поддержка:
@orelvpntopbot
"""

                            )


                        except Exception as e:

                            print(
                                "Ошибка отправки:",
                                e
                            )



                except Exception as e:

                    print(
                        f"Ошибка пользователя {user_id}:",
                        e
                    )



        except Exception as e:

            print(
                "Ошибка чекера:",
                e
            )



        # проверка каждый час
        await asyncio.sleep(
            3600
        )