from aiogram import Router, F
from aiogram.types import Message

from database import get_all_users


router = Router()


# =====================
# НАЗАД
# =====================

@router.message(F.text == "⬅️ Назад")
async def back(message: Message):

    from keyboards import main_menu

    await message.answer(
        "Главное меню:",
        reply_markup=main_menu()
    )



# =====================
# ЗАЯВКИ
# =====================

@router.message(F.text == "💳 Заявки")
async def requests(message: Message):

    await message.answer(
        """
💳 Заявки на оплату

Новых заявок пока нет.

Когда пользователь отправит чек,
он появится здесь.
"""
    )



# =====================
# РАССЫЛКА
# =====================

@router.message(F.text == "📢 Рассылка")
async def broadcast(message: Message):

    await message.answer(
        """
📢 Рассылка

Для отправки сообщения всем пользователям:

1. Напишите сообщение после команды
2. Бот отправит его всем

Функция будет подключена к базе.
"""
    )



# =====================
# ПРОМОКОДЫ
# =====================

@router.message(F.text == "🎁 Промокоды")
async def promo(message: Message):

    await message.answer(
        """
🎁 Промокоды

Доступно:

➕ Создать промокод
📋 Список промокодов
❌ Удалить промокод
"""
    )



# =====================
# НАСТРОЙКИ
# =====================

@router.message(F.text == "⚙️ Настройки")
async def settings(message: Message):

    await message.answer(
        """
⚙️ Настройки

🔗 Wi-Fi ссылка:
будет добавлена

👑 Обход Б/С ссылка:
будет добавлена

🦅 Орёл VPN
"""
    )



# =====================
# СПИСОК ПОЛЬЗОВАТЕЛЕЙ
# =====================

@router.message(F.text == "👥 Количество пользователей")
async def count_users(message: Message):

    users = get_all_users()

    await message.answer(
        f"👥 Пользователей: {len(users)}"
    )