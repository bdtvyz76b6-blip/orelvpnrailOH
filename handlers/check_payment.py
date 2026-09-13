from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS

from database import (
    create_payment,
    get_all_payments,
    process_paid_payment,
    get_payment,
)

from github_update import (
    create_subscription,
    update_subscription_file,
)

from keyboards import payment_menu

from datetime import datetime
import uuid


router = Router()


# ============================================================
# АДМИН
# ============================================================

ADMIN_IDS = set(ADMIN_IDS)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ============================================================
# ПОЛУЧЕНИЕ ПОСЛЕДНЕЙ РУЧНОЙ ЗАЯВКИ
# ============================================================

def get_latest_manual_payment(user_id: int):
    """
    Ищет последнюю pending-заявку пользователя.
    """

    try:
        payments = get_all_payments()
    except Exception as e:
        print(
            f"❌ Ошибка получения платежей: {e}"
        )
        return None

    if not payments:
        return None

    user_payments = []

    for payment in payments:

        if not isinstance(
            payment,
            dict,
        ):
            continue

        if int(
            payment.get(
                "user_id",
                0,
            )
        ) != int(user_id):
            continue

        if payment.get(
            "status"
        ) != "pending":
            continue

        if payment.get(
            "provider"
        ) != "manual":
            continue

        user_payments.append(
            payment
        )

    if not user_payments:
        return None

    # Самый свежий платеж
    user_payments.sort(
        key=lambda x: str(
            x.get(
                "created_at",
                "",
            )
        ),
        reverse=True,
    )

    return user_payments[0]


# ============================================================
# ПОЛУЧЕНИЕ ЧЕКА
# ============================================================

@router.message(F.photo)
async def get_check(
    message: Message,
):

    user_id = message.from_user.id

    photo = message.photo[-1].file_id

    # --------------------------------------------------------
    # Создаём уникальный ID ручной заявки
    # --------------------------------------------------------

    payment_id = (
        f"manual_"
        f"{user_id}_"
        f"{uuid.uuid4().hex}"
    )

    # --------------------------------------------------------
    # Сохраняем заявку в PostgreSQL
    # --------------------------------------------------------

    try:

        saved = create_payment(
            user_id=user_id,
            payment_id=payment_id,
            amount=0,
            days=0,
            provider="manual",
        )

        if not saved:

            await message.answer(
                "❌ Не удалось создать заявку."
            )

            return

    except Exception as e:

        print(
            f"❌ Ошибка сохранения заявки "
            f"{user_id}: {e}"
        )

        await message.answer(
            "❌ Ошибка сохранения заявки."
        )

        return

    # --------------------------------------------------------
    # Сообщение пользователю
    # --------------------------------------------------------

    await message.answer(
        """
✅ <b>Чек отправлен</b>

Ожидайте подтверждения оплаты администратором.
""",
        parse_mode="HTML",
    )

    # --------------------------------------------------------
    # Отправляем админу
    # --------------------------------------------------------

    caption = f"""
💳 <b>Новая заявка на оплату</b>

━━━━━━━━━━━━━━━━━━

👤 Пользователь:
<b>{message.from_user.full_name}</b>

🆔 ID:
<code>{user_id}</code>

🧾 Payment ID:
<code>{payment_id}</code>

━━━━━━━━━━━━━━━━━━

Проверьте чек и выберите действие.
"""

    for admin_id in ADMIN_IDS:

        try:

            await message.bot.send_photo(
                admin_id,
                photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=payment_menu(
                    user_id
                ),
            )

        except Exception as e:

            print(
                f"❌ Не удалось отправить "
                f"заявку админу {admin_id}: {e}"
            )


# ============================================================
# ВЫДАТЬ ПОДПИСКУ
# ============================================================

@router.callback_query(
    F.data.startswith("approve_")
)
async def approve(
    callback: CallbackQuery,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ID пользователя
    # --------------------------------------------------------

    try:

        user_id = int(
            callback.data.split(
                "_",
                1,
            )[1]
        )

    except Exception:

        await callback.answer(
            "❌ Неверный ID пользователя",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Ищем последнюю заявку
    # --------------------------------------------------------

    payment = get_latest_manual_payment(
        user_id
    )

    if not payment:

        await callback.answer(
            "❌ Активная заявка не найдена",
            show_alert=True,
        )

        return

    payment_id = payment.get(
        "payment_id"
    )

    # --------------------------------------------------------
    # Получаем срок
    # --------------------------------------------------------
    #
    # Для ручной оплаты срок хранится в callback-кнопке,
    # если payment_menu передаёт его.
    #
    # Поддерживаем:
    # approve_USER_DAYS
    #
    # Например:
    # approve_123456789_30
    # --------------------------------------------------------

    parts = callback.data.split("_")

    days = 30

    if len(parts) >= 3:

        try:

            days = int(
                parts[2]
            )

        except Exception:

            days = 30

    if days <= 0:

        days = 30

    # --------------------------------------------------------
    # Обновляем payment
    # --------------------------------------------------------

    try:

        # Для ручной оплаты payment уже создан,
        # но срок из старой заявки может быть 0.
        #
        # Поэтому если БД не хранит срок,
        # используем выбранный срок.

        result = process_paid_payment(
            payment_id
        )

    except Exception as e:

        print(
            f"❌ Ошибка подтверждения "
            f"платежа {payment_id}: {e}"
        )

        await callback.answer(
            "❌ Ошибка подтверждения платежа",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ВАЖНО
    # --------------------------------------------------------
    #
    # process_paid_payment() использует days,
    # сохранённые в payment.
    #
    # Если там 0 — подписка не продлится.
    #
    # Поэтому для ручных платежей нужно хранить срок
    # непосредственно при создании заявки.
    #
    # Этот блок оставлен для совместимости.
    # --------------------------------------------------------

    if not result:

        await callback.answer(
            "❌ Не удалось активировать подписку",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Создаём / обновляем GitHub-подписку
    # --------------------------------------------------------

    try:

        link = create_subscription(
            user_id,
            days=days,
        )

    except Exception as e:

        print(
            f"❌ Ошибка создания подписки "
            f"{user_id}: {e}"
        )

        link = None

    # --------------------------------------------------------
    # Получаем дату
    # --------------------------------------------------------

    try:

        from database import get_subscription_until

        expire_value = get_subscription_until(
            user_id
        )

        if expire_value:

            if hasattr(
                expire_value,
                "strftime",
            ):

                expire_date = expire_value.strftime(
                    "%Y-%m-%d"
                )

            else:

                expire_date = str(
                    expire_value
                )[:10]

        else:

            expire_date = "—"

    except Exception as e:

        print(
            f"❌ Ошибка получения даты "
            f"{user_id}: {e}"
        )

        expire_date = "—"

    # --------------------------------------------------------
    # Обновляем GitHub-файл
    # --------------------------------------------------------

    try:

        if expire_date != "—":

            update_subscription_file(
                user_id,
                expire_date,
            )

    except Exception as e:

        print(
            f"❌ Ошибка обновления GitHub "
            f"{user_id}: {e}"
        )

    # --------------------------------------------------------
    # Сообщение пользователю
    # --------------------------------------------------------

    subscription_url = (
        f"https://raw.githubusercontent.com/"
        f"bdtvyz76b6-blip/vpn-sub/main/users/"
        f"{user_id}.txt"
    )

    await callback.bot.send_message(
        user_id,
        f"""
🎉 <b>Оплата подтверждена!</b>

☂️ <b>ixxy VPN активирован</b>

━━━━━━━━━━━━━━━━━━

📅 Действует до:
<b>{expire_date}</b>

🔗 Ваша подписка:

<code>{subscription_url}</code>

━━━━━━━━━━━━━━━━━━

☂️ Приятного использования!
""",
        parse_mode="HTML",
    )

    # --------------------------------------------------------
    # Обновляем сообщение админу
    # --------------------------------------------------------

    try:

        await callback.message.edit_caption(
            caption=(
                "✅ <b>Подписка выдана</b>\n\n"
                f"👤 ID: <code>{user_id}</code>\n"
                f"⏳ Срок: <b>{days} дней</b>\n"
                f"📅 До: <b>{expire_date}</b>"
            ),
            parse_mode="HTML",
        )

    except Exception as e:

        print(
            f"⚠️ Не удалось изменить сообщение: {e}"
        )

    await callback.answer(
        "✅ Подписка выдана"
    )


# ============================================================
# ОТКЛОНИТЬ
# ============================================================

@router.callback_query(
    F.data.startswith("reject_")
)
async def reject(
    callback: CallbackQuery,
):

    if not is_admin(
        callback.from_user.id
    ):

        await callback.answer(
            "❌ Нет доступа",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ID пользователя
    # --------------------------------------------------------

    try:

        user_id = int(
            callback.data.split(
                "_",
                1,
            )[1]
        )

    except Exception:

        await callback.answer(
            "❌ Неверный ID пользователя",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Сообщение пользователю
    # --------------------------------------------------------

    try:

        await callback.bot.send_message(
            user_id,
            """
❌ <b>Оплата отклонена</b>

Чек не прошёл проверку.

Если вы считаете, что произошла ошибка,
свяжитесь с поддержкой.
""",
            parse_mode="HTML",
        )

    except Exception as e:

        print(
            f"❌ Ошибка сообщения "
            f"{user_id}: {e}"
        )

    # --------------------------------------------------------
    # Обновляем сообщение админу
    # --------------------------------------------------------

    try:

        await callback.message.edit_caption(
            caption=(
                "❌ <b>Заявка отклонена</b>\n\n"
                f"👤 ID: <code>{user_id}</code>"
            ),
            parse_mode="HTML",
        )

    except Exception as e:

        print(
            f"⚠️ Не удалось изменить сообщение: {e}"
        )

    await callback.answer(
        "❌ Отклонено"
    )