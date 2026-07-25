import asyncio

from database import (
    get_expired_users,
    remove_bs
)



# =====================
# ПРОВЕРКА ПОДПИСОК
# =====================

async def check_subscriptions(bot):

    while True:

        try:

            users = get_expired_users()


            for user_id in users:

                remove_bs(user_id)


                try:

                    await bot.send_message(

                        user_id,

                        """
⌛ Срок действия подписки закончился.

🎫 Ваша подписка была отключена.

Для продолжения использования оформите новую подписку.
"""
                    )

                except:

                    pass


        except Exception as e:

            print(
                f"Subscription checker: {e}"
            )


        await asyncio.sleep(
            600
        )