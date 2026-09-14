import os
import uuid
import requests


CASHERA_API_KEY = os.getenv("CASHERA_API_KEY", "").strip()

BASE_URL = "https://api.cashera.cash/api/v1"

PUBLIC_SITE_URL = os.getenv(
    "PUBLIC_SITE_URL",
    "https://ixxyweb.onrender.com"
).rstrip("/")


def create_cashera_payment(
    user_id: int,
    amount: int,
    days: int,
):

    if not CASHERA_API_KEY:
        raise RuntimeError(
            "CASHERA_API_KEY не установлен."
        )

    external_id = f"{user_id}_{uuid.uuid4().hex}"

    amount_minor = int(amount * 100)

    callback_url = (
        f"{PUBLIC_SITE_URL}/webhook/cashera"
    )

    success_url = "https://t.me/orelvpntopbot"
    fail_url = "https://t.me/orelvpntopbot"

    headers = {
        "X-Api-Key": CASHERA_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "amount": amount_minor,
        "currency": "RUB",
        "payment_method": "sbp",
        "external_id": external_id,
        "description": f"ixxy VPN — {days} дней",
        "callback_url": callback_url,
        "success_url": success_url,
        "fail_url": fail_url,
    }

    print("======================================")
    print("💳 CASHERA CREATE PAYMENT")
    print("======================================")
    print("URL:", f"{BASE_URL}/integration/transactions")
    print("amount:", amount_minor)
    print("currency:", "RUB")
    print("payment_method:", "sbp")
    print("external_id:", external_id)
    print("callback_url:", callback_url)
    print("======================================")

    try:
        response = requests.post(
            f"{BASE_URL}/integration/transactions",
            headers=headers,
            json=data,
            timeout=30,
        )
    except requests.RequestException as e:
        raise RuntimeError(
            f"Ошибка соединения с CasheRa: {e}"
        )

    print("💳 CASHERA HTTP:", response.status_code)
    print("💳 CASHERA RAW RESPONSE:")
    print(response.text)

    try:
        result = response.json()
    except Exception:
        raise RuntimeError(
            f"CasheRa вернула не JSON. "
            f"HTTP {response.status_code}: "
            f"{response.text}"
        )

    if not response.ok:
        raise RuntimeError(
            f"CasheRa HTTP {response.status_code}: "
            f"{result}"
        )

    if not isinstance(result, dict):
        raise RuntimeError(
            f"CasheRa вернула неожиданный формат: {result}"
        )

    # Иногда данные находятся внутри transaction
    transaction = result.get("transaction")

    if isinstance(transaction, dict):
        merged = dict(result)
        merged.update(transaction)
        result = merged

    payment_uuid = (
        result.get("uuid")
        or result.get("id")
        or result.get("transaction_id")
    )

    payment_url = (
        result.get("payment_url")
        or result.get("paymentUrl")
        or result.get("url")
        or result.get("pay_url")
    )

    print("======================================")
    print("💳 PARSED CASHERA")
    print("uuid:", payment_uuid)
    print("payment_url:", payment_url)
    print("======================================")

    if not payment_uuid:
        raise RuntimeError(
            f"CasheRa не вернула ID платежа: {result}"
        )

    if not payment_url:
        raise RuntimeError(
            f"CasheRa не вернула ссылку на оплату: {result}"
        )

    result["uuid"] = str(payment_uuid)
    result["payment_url"] = str(payment_url)

    return result