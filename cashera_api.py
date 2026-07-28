import os
import requests


# =====================
# CASHeRA SETTINGS
# =====================

CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY"
)

CASHERA_MERCHANT_ID = os.getenv(
    "CASHERA_MERCHANT_ID"
)



# =====================
# СОЗДАНИЕ ПЛАТЕЖА
# =====================

def create_cashera_payment(
        user_id,
        amount,
        days
):

    url = "ВСТАВИМ_СЮДА_API_URL_CASHERA"


    headers = {

        "Authorization": f"Bearer {CASHERA_API_KEY}",

        "Content-Type": "application/json"

    }


    payload = {

        "merchant_id": CASHERA_MERCHANT_ID,

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
        json=payload,
        headers=headers
    )



    print(
        "💳 CASHeRA CREATE:",
        response.text
    )



    return response.json()