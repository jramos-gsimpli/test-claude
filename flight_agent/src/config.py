import os

PRICE_THRESHOLD = 870
ORIGIN_AIRPORT = "BUE"
RECIPIENT_EMAIL = "jramos@gruposimpli.com"
SEARCH_DAYS_AHEAD = 30

EUROPEAN_AIRPORTS = [
    "MAD", "BCN",
    "LHR", "LGW",
    "CDG", "ORY",
    "FCO", "MXP",
    "AMS",
    "FRA",
    "VIE",
    "ZRH",
    "LIS",
    "ATH",
    "WAW",
    "PRG",
    "BUD",
    "CPH",
    "ARN",
    "OSL",
    "HEL",
    "DUB",
    "BRU",
]

AMADEUS_CLIENT_ID = os.environ.get("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET = os.environ.get("AMADEUS_CLIENT_SECRET", "")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
