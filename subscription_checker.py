import asyncio

from database import get_expired_users
from github_update import expire_subscription


async def check_subscriptions():

    while True:

        try:

            users = get_expired_users()

            for user_id in users:

                try:

                    expire_subscription(user_id)

                    print(
                        f"⛔ Подписка истекла: {user_id}"
                    )

                except Exception as e:

                    print(
                        f"Ошибка GitHub {user_id}:",
                        e
                    )


        except Exception as e:

            print(
                "Ошибка проверки подписок:",
                e
            )


        # проверка каждый час
        await asyncio.sleep(3600)