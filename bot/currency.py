# All prices in MENU (bot/mock_data.py) are stored in USD as the base currency.
# This module converts and formats them into whatever currency the customer selects.
#
# NOTE: These exchange rates are static approximations for demo purposes.
# For production use, swap get_rate() to fetch live rates from an FX API
# (e.g. exchangerate-api.com, openexchangerates.org) and cache them for a few hours.

SYMBOLS = {
    "USD": "$",
    "NGN": "₦",
    "GBP": "£",
    "EUR": "€",
}

# Approximate rates relative to 1 USD — update periodically or replace with a live API call.
EXCHANGE_RATES = {
    "USD": 1.0,
    "NGN": 1600.0,
    "GBP": 0.77,
    "EUR": 0.90,
}

CURRENCY_NAMES = {
    "USD": "US Dollar",
    "NGN": "Nigerian Naira",
    "GBP": "British Pound",
    "EUR": "Euro",
}

DEFAULT_CURRENCY = "USD"


def format_price(usd_amount: float, currency_code: str = DEFAULT_CURRENCY) -> str:
    """Converts a USD amount to the target currency and formats it with its symbol."""
    currency_code = (currency_code or DEFAULT_CURRENCY).upper()
    rate = EXCHANGE_RATES.get(currency_code, 1.0)
    symbol = SYMBOLS.get(currency_code, "$")
    converted = usd_amount * rate

    # Naira amounts get large fast at this rate — show as whole numbers with thousands separators.
    if currency_code == "NGN":
        return f"{symbol}{converted:,.0f}"
    return f"{symbol}{converted:,.2f}"


def get_currency_from_config(config) -> str:
    """Safely pulls the customer's selected currency out of a RunnableConfig, defaulting to USD."""
    try:
        return config["configurable"].get("currency", DEFAULT_CURRENCY) if config else DEFAULT_CURRENCY
    except (KeyError, TypeError):
        return DEFAULT_CURRENCY
