from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime
from urllib.parse import quote
from database import (
    get_user,
    check_user_subscription,
    use_promocode,
)
from keyboards import (
    cabinet_keyboard,
    payment_method_keyboard,
)
from github_update import (
    update_subscription_file,
)
router = Router()
# =========================================================
# ПРОМОКОД
# =========================================================
class PromoState(StatesGroup):
    waiting_code = State()
# =========================================================
# DEEP LINKS
# =========================================================
def happ_link(subscription_url):
    return f"happ://add/{quote(subscription_url, safe='')}"
def incy_link(subscription_url):
    return f"incy://import/{quote(subscription_url, safe='')}"
# =========================================================
# КАБИНЕТ
# =========================================================
@router.message(F.text == "👤 Личный кабинет")
async def cabinet(message: Message):
    await show_cabinet(message)
async def show_cabinet(message: Message):
    user_id = message.from_user.id
    check_user_subscription(user_id)
    user = get_user(user_id)
    if not user:
        await message.answer(
            "❌ Пользователь не найден."
        )
        return
    subscription = user[3]
    until = user[4]
    link = user[5]
    # =====================================================
    # ТАРИФ
    # =====================================================
    if subscription == "vip":
        tariff = "👑 ixxy VIP"
    elif subscription == "trial":
        tariff = "🎁 Пробный период"
    else:
        tariff = "❌ Нет подписки"
    # =====================================================
    # СТАТУС
    # =====================================================
    status = "🔴 Не активна"
    until_text = "—"
    days = 0
    if until:
        try:
            date = datetime.strptime(
                str(until),
                "%Y-%m-%d"
            )
            until_text = date.strftime(
                "%d.%m.%Y"
            )
            seconds = (
                date - datetime.now()
            ).total_seconds()
            if seconds > 0:
                status = "🟢 Активна"
                days = max(
                    1,
                    int(seconds // 86400)
                )
            else:
                status = "🔴 Истекла"
        except Exception:
            pass
    # =====================================================
    # КАБИНЕТ
    # =====================================================
    text = f"""
☂️ <b>ixxy VPN</b>
╭────────────────────
│ 👤 <b>Личный кабинет</b>
╰────────────────────
🆔 ID: <code>{user_id}</code>
🎫 Тариф:
<b>{tariff}</b>
📊 Статус:
<b>{status}</b>
📅 Действует до:
<b>{until_text}</b>
⏳ Осталось:
<b>{days} дн.</b>
🔗 Подписка:
<b>{"🟢 Доступна" if link else "🔴 Отсутствует"}</b>
👇 <b>Управление подпиской</b>
"""
    await message.answer(
        text,
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )
# =========================================================
# ОБНОВИТЬ СЕРВЕРЫ
# =========================================================
@router.callback_query(F.data == "refresh_subscription")
async def refresh_subscription(
    callback: CallbackQuery
):
    user_id = callback.from_user.id
    if not check_user_subscription(user_id):
        await callback.answer(
            "❌ Подписка не активна",
            show_alert=True
        )
        return
    user = get_user(user_id)
    if not user:
        await callback.answer(
            "❌ Пользователь не найден",
            show_alert=True
        )
        return
    until = user[4]
    if not until:
        await callback.answer(
            "❌ Нет активной подписки",
            show_alert=True
        )
        return
    try:
        date = datetime.strptime(
            str(until),
            "%Y-%m-%d"
        )
        date_text = date.strftime(
            "%d.%m.%Y"
        )
    except Exception:
        await callback.answer(
            "❌ Ошибка даты подписки",
            show_alert=True
        )
        return
    await callback.answer(
        "🔄 Обновляю серверы..."
    )
    try:
        update_subscription_file(
            user_id,
            date_text
        )
        await callback.message.answer(
            """
✅ <b>Серверы обновлены!</b>
Все актуальные серверы загружены.
🔗 Ваша ссылка осталась прежней.
""",
            parse_mode="HTML"
        )
    except Exception as e:
        print(
            f"❌ Ошибка обновления серверов "
            f"{user_id}: {e}"
        )
        await callback.message.answer(
            """
❌ <b>Не удалось обновить серверы.</b>
Попробуйте ещё раз позже.
""",
            parse_mode="HTML"
        )
# =========================================================
# ПОЛУЧИТЬ ССЫЛКУ
# =========================================================
@router.callback_query(F.data == "get_link")
async def get_link(
    callback: CallbackQuery
):
    user = get_user(
        callback.from_user.id
    )
    if not user or not user[5]:
        await callback.message.answer(
            "❌ Ссылка отсутствует."
        )
        await callback.answer()
        return
    link = user[5]
    await callback.message.answer(
        f"""
🔗 <b>Ваша подписка</b>
<code>{link}</code>
📲 Выберите приложение:
🟢 <b>Happ</b> — добавить автоматически
🟣 <b>INCY</b> — добавить автоматически
Или скопируйте ссылку вручную.
""",
        parse_mode="HTML"
    )
    await callback.answer()
# =========================================================
# HAPP
# =========================================================
@router.callback_query(F.data == "add_happ")
async def add_happ(
    callback: CallbackQuery
):
    user = get_user(
        callback.from_user.id
    )
    if not user or not user[5]:
        await callback.answer(
            "❌ Ссылка отсутствует",
            show_alert=True
        )
        return
    url = happ_link(user[5])
    await callback.message.answer(
        f"""
🟢 <b>Добавление в Happ</b>
Нажмите кнопку ниже.
Если Happ установлен, приложение откроется автоматически.
""",
        parse_mode="HTML"
    )
    await callback.message.answer(
        f"🟢 <a href=\"{url}\">Открыть в Happ</a>",
        parse_mode="HTML"
    )
    await callback.answer()
# =========================================================
# INCY
# =========================================================
@router.callback_query(F.data == "add_incy")
async def add_incy(
    callback: CallbackQuery
):
    user = get_user(
        callback.from_user.id
    )
    if not user or not user[5]:
        await callback.answer(
            "❌ Ссылка отсутствует",
            show_alert=True
        )
        return
    url = incy_link(user[5])
    await callback.message.answer(
        f"""
🟣 <b>Добавление в INCY</b>
Нажмите кнопку ниже.
Если INCY установлен, приложение откроется автоматически.
""",
        parse_mode="HTML"
    )
    await callback.message.answer(
        f"🟣 <a href=\"{url}\">Открыть в INCY</a>",
        parse_mode="HTML"
    )
    await callback.answer()
# =========================================================
# ПРОМОКОД — НАЧАЛО
# =========================================================
@router.callback_query(F.data == "enter_promo")
async def enter_promo(
    callback: CallbackQuery,
    state: FSMContext
):
    await state.set_state(
        PromoState.waiting_code
    )
    await callback.message.answer(
        "🎟 <b>Введите промокод:</b>",
        parse_mode="HTML"
    )
    await callback.answer()
# =========================================================
# ПРОМОКОД — АКТИВАЦИЯ
# =========================================================
@router.message(PromoState.waiting_code)
async def activate_promo(
    message: Message,
    state: FSMContext
):
    user_id = message.from_user.id
    code = (
        message.text
        .strip()
        .upper()
    )
    try:
        result = use_promocode(
            user_id,
            code
        )
    except Exception as e:
        print(
            f"❌ Ошибка промокода "
            f"{user_id}: {e}"
        )
        await state.clear()
        await message.answer(
            "❌ Произошла ошибка при активации."
        )
        return
    if result["reason"] == "not_found":
        await state.clear()
        await message.answer(
            "❌ Промокод не найден."
        )
        return
    if result["reason"] == "already_used":
        await state.clear()
        await message.answer(
            "❌ Вы уже использовали этот промокод."
        )
        return
    if result["reason"] == "user_not_found":
        await state.clear()
        await message.answer(
            "❌ Пользователь не найден."
        )
        return
    days = result["days"]
    new_date = result["date"]
    try:
        update_subscription_file(
            user_id,
            new_date
        )
    except Exception as e:
        print(
            f"❌ Ошибка обновления серверов "
            f"{user_id}: {e}"
        )
    try:
        date_text = datetime.strptime(
            new_date,
            "%Y-%m-%d"
        ).strftime(
            "%d.%m.%Y"
        )
    except Exception:
        date_text = new_date
    await state.clear()
    await message.answer(
        f"""
🎉 <b>Промокод активирован!</b>
🎟 Код: <code>{code}</code>
➕ Начислено: <b>{days} дней</b>
📅 Подписка до: <b>{date_text}</b>
✅ Серверы обновлены.
""",
        reply_markup=cabinet_keyboard(),
        parse_mode="HTML"
    )
# =========================================================
# ПРОДЛЕНИЕ
# =========================================================
@router.callback_query(F.data == "renew")
async def renew(
    callback: CallbackQuery
):
    await callback.message.answer(
        """
☂️ <b>Продление ixxy VPN</b>
Выберите способ оплаты:
""",
        reply_markup=payment_method_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()