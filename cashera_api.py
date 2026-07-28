import os
import requests


API_KEY = os.getenv("CASHERA_API_KEY")

MERCHANT_ID = os.getenv(
    "CASHERA_MERCHANT_ID"
)


def create_cashera_payment(
    user_id,
    amount,
    days
):

    url = "https://api.cashera.cash/v1/payments"


    headers = {

        "Authorization": f"Bearer {API_KEY}",

        "Content-Type": "application/json"

    }


    data = {

        "merchant_id": MERCHANT_ID,

        "amount": amount,

        "currency": "RUB",

        "payment_method": "sbp",

        "external_id": str(user_id),

        "metadata": {

            "days": days

        }

    }


    response = requests.post(

        url,

        json=data,

        headers=headers

    )


    print(
        "CASHeRA RESPONSE:",
        response.text
    )


    return response.json()