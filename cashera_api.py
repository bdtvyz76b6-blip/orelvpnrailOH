import os
import requests
import uuid


CASHERA_API_KEY = os.getenv(
    "CASHERA_API_KEY"
)


BASE_URL = "https://api.cashera.cash/api/v1"



def create_cashera_payment(
    user_id,
    amount,
    days
):

    url = (
        f"{BASE_URL}/integration/transactions"
    )


    headers = {

        "X-Api-Key": CASHERA_API_KEY,

        "Content-Type": "application/json"

    }



    # уникальный номер заказа
    order_id = (
        f"{user_id}_{uuid.uuid4().hex}"
    )



    data = {

        # рубли -> копейки
        "amount": amount * 100,


        "currency": "RUB",


        "payment_method": "sbp",


        # уникальный заказ
        "external_id": order_id,


        "description":
            f"Орёл VPN — {days} дней",


        "callback_url":
            "https://orelvpnrailoh-production.up.railway.app/webhook/cashera",


        "success_url":
            "https://t.me/orelvpntopbot",


        "fail_url":
            "https://t.me/orelvpntopbot"

    }



    response = requests.post(

        url,

        headers=headers,

        json=data,

        timeout=15

    )


    print(
        "💳 CASHeRA CREATE:",
        response.text
    )



    return response.json()