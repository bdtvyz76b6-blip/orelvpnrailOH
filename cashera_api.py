import os
import requests


CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY"
)


def create_cashera_payment(
    user_id,
    amount,
    days
):

    url = "https://api.cashera.cash/api/v1/integration/transactions"


    headers = {
        "X-Api-Key": CASHERA_API_KEY,
        "Content-Type": "application/json"
    }


    data = {

        # сумма в копейках
        "amount": amount * 100,

        "currency": "RUB",

        "payment_method": "sbp",

        # сюда кладём Telegram ID
        "external_id": str(user_id),

        "description": f"Орёл VPN — {days} дней",

        "callback_url":
        "https://orelvpnrailoh-production.up.railway.app/webhook/cashera"

    }


    response = requests.post(
        url,
        headers=headers,
        json=data
    )


    print(
        "CASHeRA CREATE:",
        response.text
    )


    return response.json()