import os
from dotenv import load_dotenv

load_dotenv()

# =====================
# BOT
# =====================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    "8799505763:AAFTrQi-6AxO0wWskm3kUV1Evcnux_rI4y4"
)

ADMIN_ID = int(
    os.getenv(
        "ADMIN_ID",
        "6312016802"
    )
)

# =====================
# GITHUB
# =====================

GITHUB_TOKEN = os.getenv(
    "ghp_dk1Gwd7C7WAIGAapOH6q9Rdd4wcBbz2RXmTK",
    ""
)

GITHUB_OWNER = "bdtvyz76b6-blip"
GITHUB_REPO = "vpn-sub"
GITHUB_BRANCH = "main"

# =====================
# ПОДДЕРЖКА
# =====================

SUPPORT = "@rusrodyyya"

# =====================
# ОПЛАТА
# =====================

CARD_NUMBER = "2200 1513 3958 0875"
CARD_OWNER = "@rusrodyyya"

# =====================
# ЦЕНЫ
# =====================

PRICE_7 = "35₽"
PRICE_30 = "85₽"
PRICE_90 = "245₽"
PRICE_365 = "605₽"

# =====================
# ТАРИФЫ
# =====================

FREE_TARIFF = "🎁 Пробный период"
PAID_TARIFF = "👑 Orel VPN"