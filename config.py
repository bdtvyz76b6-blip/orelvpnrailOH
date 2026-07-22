import os
from dotenv import load_dotenv

load_dotenv()


# Токен бота
BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "8799505763:AAFTrQi-6AxO0wWskm3kUV1Evcnux_rI4y4"
)


# Админ Telegram ID
ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "6312016802"
    )
)


# Подписки

WIFI_LINK = (
    "https://raw.githubusercontent.com/"
    "bdtvyz76b6-blip/vpn-sub/main/sub.txt"
)


BS_LINK = (
    "https://raw.githubusercontent.com/"
    "bdtvyz76b6-blip/vpn-sub/main/LTE.txt"
)


FREE_TARIFF = "🆓 Wi-Fi"

PAID_TARIFF = "👑 Обход Б/С"


# Оплата

PRICE_BS = "99₽"


CARD_NUMBER = "2200 1513 3958 0875"

CARD_OWNER = "@rusrodyyya"


# Поддержка

SUPPORT = "@rusrodyyya"