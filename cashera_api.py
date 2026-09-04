import os
import uuid
import requests


# ============================================================
# НАСТРОЙКИ
# ============================================================

CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY",
    ""
).strip()

BASE_URL = "https://api.cashera.cash/api/v1"


# ============================================================
# URL НАШЕГО СЕРВЕРА
# ============================================================

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh.onrender.com"
).rstrip("/")


# ============================================================
# СОЗДАНИЕ ПЛАТЕЖА CASHeRA
# ============================================================

def create_cashera_payment(
    user_id: int,
    amount: int,
    days: int
):

    if not CASHERA_API_KEY:
        raise RuntimeError(
            "CASHERA_API_KEY не установлен в переменных окружения."
        )

    # --------------------------------------------------------
    # Уникальный ID заказа
    # --------------------------------------------------------

    external_id = (
        f"{user_id}_{uuid.uuid4().hex}"
    )

    # --------------------------------------------------------
    # RUB -> копейки
    #
    # 1 ₽    -> 100
    # 129 ₽  -> 12900
    # 379 ₽  -> 37900
    # --------------------------------------------------------

    amount_minor = int(amount * 100)

    # --------------------------------------------------------
    # URL webhook
    # --------------------------------------------------------

    callback_url = (
        f"{PUBLIC_SITE_URL}/webhook/cashera"
    )

    success_url = (
        "https://t.me/orelvpntopbot"
    )

    fail_url = (
        "https://t.me/orelvpntopbot"
    )

    # --------------------------------------------------------
    # Заголовки
    # --------------------------------------------------------

    headers = {
        "X-Api-Key": CASHERA_API_KEY,
        "Content-Type": "application/json",
    }

    # --------------------------------------------------------
    # Данные платежа
    # --------------------------------------------------------

    data = {
        "amount": amount_minor,
        "currency": "RUB",
        "payment_method": "sbp",
        "external_id": external_id,
        "description": (
            f"ixxy VPN — {days} дней"
        ),
        "callback_url": callback_url,
        "success_url": success_url,
        "fail_url": fail_url,
    }

    print(
        "💳 CASHeRA CREATE:"
    )

    print(
        "amount:",
        amount_minor
    )

    print(
        "currency:",
        "RUB"
    )

    print(
        "payment_method:",
        "sbp"
    )

    print(
        "external_id:",
        external_id
    )

    print(
        "callback_url:",
        callback_url
    )

    # --------------------------------------------------------
    # Запрос
    # --------------------------------------------------------

    response = requests.post(
        f"{BASE_URL}/integration/transactions",
        headers=headers,
        json=data,
        timeout=20
    )

    # --------------------------------------------------------
    # Логируем HTTP-код
    # --------------------------------------------------------

    print(
        "💳 CASHeRA HTTP:",
        response.status_code
    )

    # --------------------------------------------------------
    # Если Cashera вернула ошибку
    # --------------------------------------------------------

    if not response.ok:

        try:
            error_data = response.json()
        except Exception:
            error_data = response.text

        print(
            "❌ CASHeRA ERROR:",
            error_data
        )

        raise RuntimeError(
            f"Cashera HTTP {response.status_code}: "
            f"{error_data}"
        )

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    try:

        result = response.json()

    except Exception as e:

        raise RuntimeError(
            f"Cashera вернула не JSON: {e}"
        )

    # --------------------------------------------------------
    # Иногда API может вернуть объект транзакции
    # внутри transaction.
    # --------------------------------------------------------

    if isinstance(result, dict):

        transaction = result.get(
            "transaction"
        )

        if isinstance(transaction, dict):

            merged = dict(result)

            merged.update(transaction)

            result = merged

    # --------------------------------------------------------
    # Проверяем UUID
    # --------------------------------------------------------

    payment_uuid = (
        result.get("uuid")
        or result.get("id")
    )

    if not payment_uuid:

        raise RuntimeError(
            f"Cashera не вернула uuid: {result}"
        )

    # --------------------------------------------------------
    # Проверяем payment_url
    # --------------------------------------------------------

    payment_url = (
        result.get("payment_url")
        or result.get("url")
    )

    if not payment_url:

        raise RuntimeError(
            f"Cashera не вернула payment_url: {result}"
        )

    print(
        "✅ CASHeRA PAYMENT CREATED"
    )

    print(
        "uuid:",
        payment_uuid
    )

    print(
        "payment_url:",
        payment_url
    )

    return result