import os
import uuid
import requests


# ============================================================
# НАСТРОЙКИ CASHERA
# ============================================================

CASHERA_API_KEY = os.getenv("CASHERA_API_KEY", "").strip()

CASHERA_API_SECRET = os.getenv(
    "CASHERA_API_SECRET",
    ""
).strip()

BASE_URL = os.getenv(
    "CASHERA_BASE_URL",
    "https://api.cashera.cash/api/v1"
).rstrip("/")


# Текущий публичный адрес твоего Flask-сервиса
PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://orelvpnrailoh-1.onrender.com"
).rstrip("/")


CALLBACK_URL = (
    f"{PUBLIC_SITE_URL}/webhook/cashera"
)


# ============================================================
# СОЗДАНИЕ ПЛАТЕЖА
# ============================================================

def create_cashera_payment(
    user_id: int,
    amount: int,
    days: int
):

    if not CASHERA_API_KEY:
        raise RuntimeError(
            "CASHERA_API_KEY не установлен"
        )

    if amount <= 0:
        raise ValueError(
            "Некорректная сумма платежа"
        )

    if days <= 0:
        raise ValueError(
            "Некорректный срок подписки"
        )

    url = (
        f"{BASE_URL}/integration/transactions"
    )

    headers = {
        "X-Api-Key": CASHERA_API_KEY,
        "Content-Type": "application/json",
    }

    # Уникальный внешний ID
    external_id = (
        f"{user_id}_{uuid.uuid4().hex}"
    )

    data = {
        # Cashera принимает сумму в копейках
        "amount": amount * 100,

        "currency": "RUB",

        "payment_method": "sbp",

        "external_id": external_id,

        "description": (
            f"ixxy VPN — {days} дней"
        ),

        "callback_url": CALLBACK_URL,

        "success_url": (
            "https://t.me/orelvpntopbot"
        ),

        "fail_url": (
            "https://t.me/orelvpntopbot"
        ),
    }

    print("================================")
    print("💳 CASHERA CREATE PAYMENT")
    print("URL:", url)
    print("CALLBACK:", CALLBACK_URL)
    print("USER:", user_id)
    print("AMOUNT:", amount)
    print("DAYS:", days)
    print("EXTERNAL ID:", external_id)
    print("================================")

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=20
    )

    print(
        "💳 CASHERA HTTP:",
        response.status_code
    )

    print(
        "💳 CASHERA RESPONSE:",
        response.text
    )

    response.raise_for_status()

    result = response.json()

    if not isinstance(result, dict):
        raise RuntimeError(
            "Cashera вернула некорректный JSON"
        )

    return result