from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import get_all_users, get_user

router = Router()


@router.callback_query(F.data == "admin_users")
async def show_users(call: CallbackQuery):

    users = get_all_users()

    if not users:
        await call.message.edit_text(
            "👥 Пользователей пока нет"
        )
        return

    buttons = []

    for user in users[:20]:

        user_id = user[0]
        username = user[1] or "без username"

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"👤 {username}",
                    callback_data=f"admin_user_{user_id}"
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data="admin_back"
            )
        ]
    )

    await call.message.edit_text(
        "👥 Пользователи:",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=buttons
        )
    )


@router.callback_query(F.data.startswith("admin_user_"))
async def user_profile(call: CallbackQuery):

    user_id = int(
        call.data.replace("admin_user_", "")
    )

    user = get_user(user_id)

    if not user:
        await call.answer(
            "Пользователь не найден",
            show_alert=True
        )
        return


    text = (
        f"👤 Пользователь\n\n"
        f"🆔 ID: {user[0]}\n"
        f"👤 Username: @{user[1] or 'нет'}\n\n"
        f"📌 Тариф: {user[2]}\n"
        f"📅 До: {user[4] or 'нет'}\n\n"
        f"🔗 Подписка:\n"
        f"{user[3] or 'нет'}\n\n"
        f"📊 Статус: 🟢 Активен"
    )


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⏳ Продлить",
                    callback_data=f"extend_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отключить",
                    callback_data=f"disable_{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="admin_users"
                )
            ]
        ]
    )


    await call.message.edit_text(
        text,
        reply_markup=keyboard
    )