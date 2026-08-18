import os
from dotenv import load_dotenv

load_dotenv()


# =====================
# BOT
# =====================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


# =====================
# АДМИНЫ
# =====================

# Telegram ID администраторов через запятую
#
# Пример:
# ADMIN_IDS=6312016802,123456789

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv(
        "ADMIN_IDS",
        "6312016802"
    ).split(",")
    if x.strip()
}


# =====================
# GITHUB
# =====================

GITHUB_TOKEN = os.getenv(
    "GITHUB_TOKEN",
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

PRICE_30 = "70₽"
PRICE_90 = "190₽"
PRICE_180 = "350₽"
PRICE_365 = "700₽"


# =====================
# ТАРИФЫ
# =====================

FREE_TARIFF = "🎁 Пробный период"
PAID_TARIFF = "👑 Orel VPN"