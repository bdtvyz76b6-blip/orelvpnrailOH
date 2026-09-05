from aiogram import Router, F, Bot
from aiogram.types import (
CallbackQuery,
Message,
InlineKeyboardMarkup,
InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config import ADMIN_IDS, BOT_TOKEN
from database import get_user_ids

router = Router()

============================================================

СОСТОЯНИЕ РАССЫЛКИ

============================================================

class Broadcast(StatesGroup):
waiting_message = State()
waiting_confirm = State()

============================================================

КЛАВИАТУРА ПОДТВЕРЖДЕНИЯ

============================================================

def broadcast_confirm_keyboard():
return InlineKeyboardMarkup(
inline_keyboard=[
[
InlineKeyboardButton(
text=“✅ Начать рассылку”,
callback_data=“broadcast_confirm”,
),
InlineKeyboardButton(
text=“❌ Отмена”,
callback_data=“broadcast_cancel”,
),
]
]
)

============================================================

ПРОВЕРКА АДМИНА

============================================================

def is_admin(user_id: int) -> bool:
return user_id in ADMIN_IDS

============================================================

НАЧАЛО РАССЫЛКИ

============================================================

@router.callback_query(F.data == “admin_broadcast”)
async def start_broadcast(
call: CallbackQuery,
state: FSMContext,
):
if not call.from_user or not is_admin(call.from_user.id):
await call.answer(
“❌ Нет доступа.”,
show_alert=True,
)
return

await state.clear()
await state.set_state(Broadcast.waiting_message)
await call.answer()
await call.message.answer(
    "📢 <b>Создание рассылки</b>\n\n"
    "Отправь сообщение, которое нужно разослать пользователям.\n\n"
    "Можно отправить:\n"
    "• текст\n"
    "• фото с подписью\n"
    "• видео с подписью\n"
    "• документ с подписью\n\n"
    "После этого бот покажет предпросмотр и попросит подтверждение.",
    parse_mode="HTML",
)

============================================================

ПОЛУЧЕНИЕ СООБЩЕНИЯ

============================================================

@router.message(Broadcast.waiting_message)
async def prepare_broadcast(
message: Message,
state: FSMContext,
):
if not message.from_user or not is_admin(message.from_user.id):
await state.clear()
return

# --------------------------------------------------------
# ПРОВЕРЯЕМ, ЧТО СООБЩЕНИЕ ПОДДЕРЖИВАЕТСЯ
# --------------------------------------------------------
supported = any(
    [
        bool(message.text),
        bool(message.photo),
        bool(message.video),
        bool(message.document),
    ]
)
if not supported:
    await message.answer(
        "⚠️ Этот тип сообщения пока не поддерживается.\n\n"
        "Отправь текст, фото, видео или документ."
    )
    return
# --------------------------------------------------------
# СОХРАНЯЕМ ID СООБЩЕНИЯ
# --------------------------------------------------------
await state.update_data(
    message_id=message.message_id,
    chat_id=message.chat.id,
)
await state.set_state(Broadcast.waiting_confirm)
# --------------------------------------------------------
# КОЛИЧЕСТВО ПОЛЬЗОВАТЕЛЕЙ
# --------------------------------------------------------
try:
    users = get_user_ids() or []
    users_count = len(users)
except Exception:
    users_count = 0
# --------------------------------------------------------
# ПРЕДПРОСМОТР
# --------------------------------------------------------
await message.answer(
    "📢 <b>Предпросмотр рассылки</b>\n\n"
    f"👥 Получателей: <b>{users_count}</b>\n\n"
    "Сообщение выше будет отправлено всем пользователям.\n\n"
    "Начать рассылку?",
    parse_mode="HTML",
    reply_markup=broadcast_confirm_keyboard(),
)

============================================================

ПОДТВЕРЖДЕНИЕ

============================================================

@router.callback_query(F.data == “broadcast_confirm”)
async def confirm_broadcast(
call: CallbackQuery,
state: FSMContext,
):
if not call.from_user or not is_admin(call.from_user.id):
await call.answer(
“❌ Нет доступа.”,
show_alert=True,
)
return

data = await state.get_data()
message_id = data.get("message_id")
chat_id = data.get("chat_id")
if not message_id or not chat_id:
    await state.clear()
    await call.answer(
        "❌ Сообщение для рассылки не найдено.",
        show_alert=True,
    )
    return
await call.answer()
# --------------------------------------------------------
# ПОЛУЧАЕМ ПОЛЬЗОВАТЕЛЕЙ
# --------------------------------------------------------
try:
    users = get_user_ids() or []
except Exception as e:
    await state.clear()
    await call.message.answer(
        "❌ Не удалось получить список пользователей.\n\n"
        f"<code>{type(e).__name__}</code>",
        parse_mode="HTML",
    )
    return
total = len(users)
if total == 0:
    await state.clear()
    await call.message.answer(
        "⚠️ Пользователей для рассылки нет."
    )
    return
# --------------------------------------------------------
# УВЕДОМЛЕНИЕ О СТАРТЕ
# --------------------------------------------------------
status_message = await call.message.answer(
    "📢 <b>Рассылка запущена</b>\n\n"
    f"👥 Получателей: <b>{total}</b>\n"
    "⏳ Обработка...",
    parse_mode="HTML",
)
# --------------------------------------------------------
# ОСНОВНОЙ BOT
# --------------------------------------------------------
bot = Bot(token=BOT_TOKEN)
sent = 0
failed = 0
blocked = 0
try:
    for index, user_id in enumerate(users, start=1):
        try:
            await bot.copy_message(
                chat_id=int(user_id),
                from_chat_id=chat_id,
                message_id=message_id,
            )
            sent += 1
        except TelegramForbiddenError:
            failed += 1
            blocked += 1
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1
        # ------------------------------------------------
        # Небольшая задержка, чтобы не упираться
        # в Telegram rate limit
        # ------------------------------------------------
        if index % 20 == 0:
            try:
                await status_message.edit_text(
                    "📢 <b>Рассылка выполняется</b>\n\n"
                    f"📨 Обработано: <b>{index}/{total}</b>\n"
                    f"✅ Отправлено: <b>{sent}</b>\n"
                    f"❌ Ошибок: <b>{failed}</b>",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        # Небольшая пауза между сообщениями
        import asyncio
        await asyncio.sleep(0.05)
finally:
    await bot.session.close()
# --------------------------------------------------------
# ИТОГ
# --------------------------------------------------------
await state.clear()
try:
    await status_message.edit_text(
        "📢 <b>Рассылка завершена</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"✅ Отправлено: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>\n"
        f"🚫 Заблокировали бота: <b>{blocked}</b>",
        parse_mode="HTML",
    )
except Exception:
    await call.message.answer(
        "📢 <b>Рассылка завершена</b>\n\n"
        f"👥 Всего: <b>{total}</b>\n"
        f"✅ Отправлено: <b>{sent}</b>\n"
        f"❌ Ошибок: <b>{failed}</b>\n"
        f"🚫 Заблокировали: <b>{blocked}</b>",
        parse_mode="HTML",
    )

============================================================

ОТМЕНА

============================================================

@router.callback_query(F.data == “broadcast_cancel”)
async def cancel_broadcast(
call: CallbackQuery,
state: FSMContext,
):
if not call.from_user or not is_admin(call.from_user.id):
await call.answer(
“❌ Нет доступа.”,
show_alert=True,
)
return

await state.clear()
await call.answer(
    "Рассылка отменена."
)
await call.message.edit_text(
    "❌ <b>Рассылка отменена.</b>",
    parse_mode="HTML",
)

============================================================

ОТМЕНА КОМАНДОЙ

============================================================

@router.message(
Broadcast.waiting_message,
F.text == “/cancel”,
)
@router.message(
Broadcast.waiting_confirm,
F.text == “/cancel”,
)
async def cancel_broadcast_command(
message: Message,
state: FSMContext,
):
if not message.from_user or not is_admin(message.from_user.id):
await state.clear()
return

await state.clear()
await message.answer(
    "❌ Рассылка отменена."
)