from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from config import ADMIN_ID, BS_LINK
from database import (
    get_all_users,
    get_user,
    activate_bs,
    remove_bs,
    get_stats
)
from keyboards import (
    admin_menu,
    users_keyboard,
    user_card_keyboard
)

router = Router()


@router.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🦅 Админ-панель\n\nВыберите раздел:",
        reply_markup=admin_menu()
    )


# Пользователи
@router.message(F.text == "👥 Пользователи")
async def users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    users = get_all_users()

    if not users:
        await message.answer("Пользователей пока нет.")
        return

    await message.answer(
        f"👥 Пользователи\n\nВсего: {len(users)}",
        reply_markup=users_keyboard(users)
    )


# Карточка пользователя
@router.callback_query(F.data.startswith("user_"))
async def user_card(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    user_id = int(callback.data.split("_")[1])
    user = get_user(user_id)

    if not user:
        await callback.answer("Пользователь не найден")
        return

    wifi = "✅ Активен" if user[2] else "❌ Нет"
    bs = "✅ Активен" if user[3] else "❌ Нет"

    await callback.message.edit_text(
        f"""👤 Пользователь

🆔 ID: {user[0]}
👤 Username: @{user[1]}

🟢 Wi-Fi: {wifi}
👑 Обход Б/С: {bs}

📅 Регистрация: {user[6]}""",
        reply_markup=user_card_keyboard(user_id)
    )

    await callback.answer()


# Выдать Б/С
@router.callback_query(F.data.startswith("give_bs_"))
async def give_bs(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])

    activate_bs(user_id, BS_LINK)

    await callback.bot.send_message(
        user_id,
        "🎉 Вам активировали тариф Обход Б/С!\n\n"
        f"Ваша ссылка:\n{BS_LINK}"
    )

    await callback.answer("Доступ выдан")


# Забрать Б/С
@router.callback_query(F.data.startswith("remove_bs_"))
async def remove_bs_handler(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])

    remove_bs(user_id)

    await callback.bot.send_message(
        user_id,
        "❌ Ваш доступ к Обход Б/С был отключён."
    )

    await callback.answer("Доступ отключён")


# Статистика
@router.message(F.text == "📊 Статистика")
async def stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = get_stats()

    await message.answer(
        f"""📊 Статистика

👥 Всего пользователей: {stats["total"]}
🟢 Wi-Fi: {stats["wifi"]}
👑 Обход Б/С: {stats["bs"]}

💰 Продаж: {stats["bs"]}"""
    )


# Заявки
@router.message(F.text == "💳 Заявки")
async def requests(message: Message):
    await message.answer(
        "💳 Заявки на оплату\n\n"
        "Все новые чеки будут приходить сюда автоматически."
    )


# Рассылка
@router.message(F.text == "📢 Рассылка")
async def broadcast(message: Message):
    await message.answer(
        "📢 Рассылка\n\n"
        "Функция будет добавлена следующим файлом."
    )


# Промокоды
@router.message(F.text == "🎁 Промокоды")
async def promocodes(message: Message):
    await message.answer(
        "🎁 Промокоды\n\n"
        "Функция будет добавлена следующим файлом."
    )


# Настройки
@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):
    await message.answer(
        "⚙️ Настройки\n\n"
        "Здесь будут настройки бота и подписок."
    )