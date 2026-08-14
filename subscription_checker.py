import asyncio

from database import (
    get_expired_users,
    disable_subscription,
    get_user
)

from github_update import expire_subscription


async def check_subscriptions(bot):

    while True:

        try:

            expired_users = get_expired_users()

            for user in expired_users:

                # get_expired_users() возвращает всю строку пользователя
                user_id = user[0]

                current_user = get_user(user_id)

                if not current_user:
                    continue

                try:
                    # Сначала меняем файл на GitHub
                    expire_subscription(user_id)

                except Exception as e:
                    print(
                        f"❌ Не удалось обновить GitHub для {user_id}:",
                        e
                    )
                    continue

                # Только если GitHub успешно обновился,
                # отключаем подписку в базе
                disable_subscription(user_id)

                try:

                    await bot.send_message(
                        user_id,
                        """
⛔ Срок действия подписки закончился.

☂️ ixxy vpn

🎫 Продлите подписку,
чтобы снова получить доступ.
"""
                    )

                except Exception as e:

                    print(
                        f"⚠️ Не удалось отправить уведомление {user_id}:",
                        e
                    )

        except Exception as e:

            print(
                "❌ Subscription checker error:",
                e
            )

        # Проверяем раз в час
        await asyncio.sleep(3600)