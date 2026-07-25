from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_user


router = Router()



# =====================
# НАСТРОЙКИ
# =====================

@router.callback_query(
    F.data == "settings"
)
async def settings(callback: CallbackQuery):

    user = get_user(
        callback.from_user.id
    )


    if not user:

        await callback.answer(
            "Профиль не найден",
            show_alert=True
        )

        return



    notify = "🔔 Включены"


    if user["notify_3_days"] == 0:

        notify = "🔕 Выключены"



    await callback.message.edit_text(
f"""
⚙️ Настройки


🆔 ID:
{user["user_id"]}


🔔 Уведомления:
{notify}


📱 Лимит устройств:
{user["devices_limit"]}


🌍 Серверов:
{user["servers_count"]}

""",
        reply_markup=settings_keyboard()
    )


    await callback.answer()



# =====================
# КНОПКИ
# =====================

def settings_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔔 Уведомления",
                    callback_data="toggle_notify"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_cabinet"
                )
            ]

        ]
    )



# =====================
# УВЕДОМЛЕНИЯ
# =====================

@router.callback_query(
    F.data == "toggle_notify"
)
async def toggle_notify(callback: CallbackQuery):

    from database import connect


    conn = connect()
    cur = conn.cursor()


    user = get_user(
        callback.from_user.id
    )


    new_value = 0


    if user["notify_3_days"] == 0:

        new_value = 1



    cur.execute(
        """
        UPDATE users

        SET notify_3_days=?

        WHERE user_id=?

        """,
        (
            new_value,
            callback.from_user.id
        )
    )


    conn.commit()
    conn.close()



    await callback.answer(
        "Настройки обновлены ✅"
    )



# =====================
# НАЗАД
# =====================

@router.callback_query(
    F.data == "back_cabinet"
)
async def back_cabinet(callback: CallbackQuery):

    from handlers.cabinet import show_cabinet


    await callback.message.delete()


    await show_cabinet(
        callback.message
    )


    await callback.answer()