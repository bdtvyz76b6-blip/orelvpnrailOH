import asyncio

from datetime import datetime

from database import (
    get_expired_users,
    disable_subscription,
    get_user
)

from github_update import (
    expire_subscription
)





# =====================
# ПРОВЕРКА ПОДПИСОК
# =====================

async def check_subscriptions(bot):

    while True:

        try:

            expired = get_expired_users()



            for user_id in expired:


                user = get_user(
                    user_id
                )


                if not user:

                    continue



                # меняем GitHub файл

                expire_subscription(
                    user_id
                )



                # отключаем в базе

                disable_subscription(
                    user_id
                )



                try:

                    await bot.send_message(

                        user_id,

f"""
⛔ Срок действия подписки закончился.


☂️ ixxy vpn


🎫 Продлите подписку,
чтобы снова получить доступ.
"""

                    )


                except:

                    pass





        except Exception as e:

            print(
                "Subscription checker error:",
                e
            )



        # проверка раз в час

        await asyncio.sleep(
            3600
        )