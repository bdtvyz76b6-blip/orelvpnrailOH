from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_ID

from database import (
    get_all_users,
    get_user,
    remove_bs,
    get_stats,
    get_subscription_link
)

from keyboards import (
    admin_menu,
    users_keyboard,
    user_card_keyboard
)


router = Router()



# =====================
# АДМИН ПАНЕЛЬ
# =====================

@router.message(Command("admin"))
async def admin(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🦅 Админ-панель\n\n"
        "Выберите раздел:",
        reply_markup=admin_menu()
    )



# =====================
# ПОЛЬЗОВАТЕЛИ
# =====================

@router.message(F.text == "👥 Пользователи")
async def users(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    users = get_all_users()


    if not users:

        await message.answer(
            "Пользователей нет."
        )

        return


    await message.answer(
        f"👥 Пользователи\n\n"
        f"Всего: {len(users)}",
        reply_markup=users_keyboard(users)
    )



# =====================
# КАРТОЧКА ПОЛЬЗОВАТЕЛЯ
# =====================

@router.callback_query(F.data.startswith("user_"))
async def user_card(callback: CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[1]
    )


    user = get_user(user_id)


    if not user:

        await callback.answer(
            "Пользователь не найден"
        )

        return



    await callback.message.edit_text(

        f"""
👤 Карточка пользователя


🆔 ID:
{user[0]}


👤 Username:
@{user[1]}


👑 Тариф:
{user[2]}


🔗 Подписка:
{user[3]}


📅 До:
{user[4]}


📆 Создан:
{user[8]}
""",

        reply_markup=user_card_keyboard(
            user_id
        )
    )


    await callback.answer()



# =====================
# ЗАБРАТЬ ПОДПИСКУ
# =====================

@router.callback_query(F.data.startswith("remove_sub_"))
async def remove_subscription(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:
        return


    user_id = int(
        callback.data.split("_")[2]
    )


    remove_bs(
        user_id
    )


    try:

        await callback.bot.send_message(
            user_id,
            "❌ Ваша подписка отключена."
        )

    except:

        pass


    await callback.answer(
        "Подписка отключена"
    )



# =====================
# СТАТИСТИКА
# =====================

@router.message(F.text == "📊 Статистика")
async def stats(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    data = get_stats()


    await message.answer(
        f"""
📊 Статистика


👥 Пользователей:
{data['total']}


🆓 Wi-Fi:
{data['wifi']}


👑 Подписок:
{data['bs']}
"""
    )



# =====================
# ЗАЯВКИ
# =====================

@router.message(F.text == "💳 Заявки")
async def requests(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "💳 Заявки\n\n"
        "Новые оплаты приходят автоматически."
    )



# =====================
# РАССЫЛКА
# =====================

@router.message(F.text == "📢 Рассылка")
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "📢 Раздел рассылки"
    )



# =====================
# ПРОМОКОДЫ
# =====================

@router.message(F.text == "🎁 Промокоды")
async def promo(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "🎁 Раздел промокодов"
    )



# =====================
# НАСТРОЙКИ
# =====================

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):

    if message.from_user.id != ADMIN_ID:
        return


    await message.answer(
        "⚙️ Настройки"
    )