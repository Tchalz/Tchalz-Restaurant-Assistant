import json
import random
from datetime import datetime
from typing import List

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from bot import db
from bot.mock_data import MENU, RESTAURANT_HOURS, DAILY_SPECIALS
from bot.validators import validate_date, validate_party_size


@tool
def search_menu(query: str = "", dietary_filter: str = "") -> str:
    """
    Searches the menu by item name, category, or dietary requirement.
    Use this tool when a customer asks what food or drinks are available.

    Args:
        query: Optional keyword to search item names or categories, e.g. 'pizza' or 'dessert'
        dietary_filter: Optional filter, one of 'vegan', 'vegetarian', 'gluten_free'
    """
    try:
        results = MENU
        if query:
            q = query.lower()
            results = [i for i in results if q in i["name"].lower() or q in i["category"].lower()]
        if dietary_filter:
            key = dietary_filter.lower()
            if key not in ("vegan", "vegetarian", "gluten_free"):
                return f"Unsupported dietary filter: {dietary_filter}"
            results = [i for i in results if i.get(key)]
        if not results:
            return "No menu items matched your search."
        lines = [f"{i['name']} - ${i['price']:.2f} ({i['category']})" for i in results]
        return "Here are the matching items:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error searching menu: {str(e)}"


@tool
def check_allergen_info(item_name: str) -> str:
    """
    Checks the allergens present in a specific menu item.
    Use this tool whenever a customer asks about allergens, intolerances, or food safety for a dish.
    Always use this tool for allergen questions rather than guessing from search_menu results.

    Args:
        item_name: The exact or approximate name of the menu item
    """
    try:
        match = next((i for i in MENU if item_name.lower() in i["name"].lower()), None)
        if not match:
            return f"Could not find a menu item matching '{item_name}'."
        allergens = match["allergens"]
        if not allergens:
            return f"{match['name']} contains no listed allergens, but please confirm with staff for cross-contamination risk."
        return f"{match['name']} contains: {', '.join(allergens)}. Please confirm with staff if you have a severe allergy."
    except Exception as e:
        return f"Error checking allergens: {str(e)}"


@tool
def check_daily_specials() -> str:
    """
    Returns today's special menu items and promotions.
    Use this tool when a customer asks about specials, deals, or what's new today.
    """
    try:
        if not DAILY_SPECIALS:
            return "There are no specials today."
        lines = [f"{s['name']} - ${s['price']:.2f}: {s['description']}" for s in DAILY_SPECIALS]
        return "Today's specials:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching specials: {str(e)}"


@tool
def get_restaurant_hours(day: str = "") -> str:
    """
    Returns the restaurant's opening hours for a specific day, or all days if none is given.
    Use this tool when a customer asks if the restaurant is open or what time it opens/closes.

    Args:
        day: Optional day name, e.g. 'Monday'. Leave blank for the full week.
    """
    try:
        if day:
            hours = RESTAURANT_HOURS.get(day.capitalize())
            if not hours:
                return f"'{day}' is not a recognized day."
            return f"{day.capitalize()} hours: {hours}"
        lines = [f"{d}: {h}" for d, h in RESTAURANT_HOURS.items()]
        return "Weekly hours:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error fetching hours: {str(e)}"


@tool
def check_table_availability(date: str, time: str, party_size: int) -> str:
    """
    Checks whether a table is available for a given date, time, and party size.
    Use this tool before creating a reservation to confirm availability.
    If no table is available, suggest the join_waitlist tool to the customer.

    Args:
        date: Reservation date in 'YYYY-MM-DD' format
        time: Reservation time, e.g. '19:00'
        party_size: Number of guests
    """
    valid, err = validate_date(date)
    if not valid:
        return err
    valid, err = validate_party_size(party_size)
    if not valid:
        return err
    try:
        available = random.choice([True, True, False])
        if available:
            return f"A table for {party_size} is available on {date} at {time}."
        return (
            f"Sorry, no tables for {party_size} are available on {date} at {time}. "
            "I can add you to the waitlist for that slot if you'd like — just say the word."
        )
    except Exception as e:
        return f"Error checking availability: {str(e)}"


@tool
def get_order_status(order_id: str) -> str:
    """
    Checks the current status of a previously placed order.
    Use this tool when a customer asks where their order is or if it's ready.

    Args:
        order_id: The order ID, e.g. 'ORD1234'
    """
    try:
        order = db.get_order(order_id)
        if not order:
            return f"No order found with ID {order_id}."
        return (
            f"Order {order_id} ({order['order_type']}): status is '{order['status']}', "
            f"subtotal ${order['subtotal']:.2f}, estimated ready at {order['eta']}."
        )
    except Exception as e:
        return f"Error checking order status: {str(e)}"


@tool
def view_cart(config: RunnableConfig = None) -> str:
    """
    Shows everything currently in the customer's order cart, including any
    customizations, along with the running subtotal.
    Use this whenever a customer asks what's in their order, or before checkout
    to confirm everything is correct.
    """
    try:
        session_id = config["configurable"]["thread_id"] if config else "default"
        items = db.get_cart(session_id)
        if not items:
            return "The cart is currently empty."
        lines = []
        total = 0.0
        for item in items:
            modifiers = json.loads(item["modifiers"])
            mod_str = f" ({', '.join(modifiers)})" if modifiers else ""
            line_total = item["unit_price"] * item["quantity"]
            total += line_total
            lines.append(f"{item['quantity']}x {item['item_name']}{mod_str} - ${line_total:.2f}")
        lines.append(f"\nSubtotal: ${total:.2f}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error viewing cart: {str(e)}"


@tool
def add_to_cart(item_name: str, quantity: int = 1, modifiers: List[str] = [], config: RunnableConfig = None) -> str:
    """
    Adds a menu item to the customer's order cart, with optional customizations.
    Use this tool once per distinct item the customer wants — call it again for
    each additional item. Use view_cart afterward to show the running total.

    Args:
        item_name: Exact or approximate name of the menu item to add
        quantity: How many of this item to add
        modifiers: Customizations like 'extra spicy', 'no onions', 'mild', 'no ice'
    """
    try:
        match = next((i for i in MENU if item_name.lower() in i["name"].lower()), None)
        if not match:
            return f"Could not find '{item_name}' on the menu."
        if quantity < 1:
            return "Quantity must be at least 1."
        session_id = config["configurable"]["thread_id"] if config else "default"
        db.add_cart_item(session_id, match["name"], quantity, modifiers, match["price"])
        mod_str = f" ({', '.join(modifiers)})" if modifiers else ""
        return f"Added {quantity}x {match['name']}{mod_str} to your order."
    except Exception as e:
        return f"Error adding to cart: {str(e)}"


SAFE_TOOLS = [
    search_menu,
    check_allergen_info,
    check_daily_specials,
    get_restaurant_hours,
    check_table_availability,
    get_order_status,
    view_cart,
    add_to_cart,
]
