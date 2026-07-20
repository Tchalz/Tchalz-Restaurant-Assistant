import json
from datetime import datetime, timedelta

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig

from bot import db
from bot.validators import validate_date, validate_party_size, validate_contact
from bot.currency import format_price, get_currency_from_config


@tool
def create_reservation(name: str, date: str, time: str, party_size: int, contact: str,
                        config: RunnableConfig = None) -> str:
    """
    Creates a table reservation. Only use this after confirming availability with check_table_availability.
    Use this tool when a customer wants to actually book a table.

    Args:
        name: Name for the reservation
        date: Reservation date in 'YYYY-MM-DD' format
        time: Reservation time, e.g. '19:00'
        party_size: Number of guests
        contact: Phone number or email for confirmation
    """
    valid, err = validate_date(date)
    if not valid:
        return err
    valid, err = validate_party_size(party_size)
    if not valid:
        return err
    valid, err = validate_contact(contact)
    if not valid:
        return err
    try:
        session_id = config["configurable"]["thread_id"] if config else None
        res_id = db.create_reservation(name, date, time, int(party_size), contact, session_id=session_id)
        return f"Reservation confirmed! ID: {res_id} for {name}, party of {party_size}, on {date} at {time}."
    except Exception as e:
        return f"Error creating reservation: {str(e)}"


@tool
def cancel_or_modify_reservation(reservation_id: str, action: str, new_date: str = "",
                                  new_time: str = "", new_party_size: int = 0) -> str:
    """
    Cancels or modifies an existing reservation.
    Use this tool when a customer wants to change or cancel a booking they already have.

    Args:
        reservation_id: The reservation ID, e.g. 'RES1234'
        action: Either 'cancel' or 'modify'
        new_date: New date if modifying, format 'YYYY-MM-DD'
        new_time: New time if modifying
        new_party_size: New party size if modifying
    """
    try:
        existing = db.get_reservation(reservation_id)
        if not existing:
            return f"No reservation found with ID {reservation_id}."

        if action.lower() == "cancel":
            db.delete_reservation(reservation_id)
            return f"Reservation {reservation_id} has been cancelled."

        elif action.lower() == "modify":
            updates = {}
            if new_date:
                valid, err = validate_date(new_date)
                if not valid:
                    return err
                updates["date"] = new_date
            if new_time:
                updates["time"] = new_time
            if new_party_size:
                valid, err = validate_party_size(new_party_size)
                if not valid:
                    return err
                updates["party_size"] = int(new_party_size)

            if not updates:
                return "Nothing to update — please specify a new date, time, or party size."

            db.update_reservation(reservation_id, **updates)
            updated = db.get_reservation(reservation_id)
            return (
                f"Reservation {reservation_id} updated: {updated['party_size']} guests on "
                f"{updated['date']} at {updated['time']}."
            )
        else:
            return "Action must be 'cancel' or 'modify'."
    except Exception as e:
        return f"Error updating reservation: {str(e)}"


@tool
def join_waitlist(name: str, date: str, time: str, party_size: int, contact: str) -> str:
    """
    Adds a customer to the waitlist for a specific date and time when no table was available.
    Only use this after check_table_availability reported no availability.

    Args:
        name: Name for the waitlist entry
        date: Requested date in 'YYYY-MM-DD' format
        time: Requested time, e.g. '19:00'
        party_size: Number of guests
        contact: Phone number or email so we can notify them if a table opens up
    """
    valid, err = validate_date(date)
    if not valid:
        return err
    valid, err = validate_party_size(party_size)
    if not valid:
        return err
    valid, err = validate_contact(contact)
    if not valid:
        return err
    try:
        waitlist_id = db.add_to_waitlist(name, date, time, int(party_size), contact)
        return (
            f"You're on the waitlist! ID: {waitlist_id} for {name}, party of {party_size}, "
            f"on {date} around {time}. We'll reach out at {contact} if a table opens up."
        )
    except Exception as e:
        return f"Error joining waitlist: {str(e)}"


@tool
def checkout_order(delivery_or_pickup: str, contact: str, config: RunnableConfig = None) -> str:
    """
    Finalizes and places the order currently sitting in the customer's cart, for
    delivery or pickup. Only use this after the customer has reviewed their cart
    with view_cart and confirmed they're ready, and after collecting their contact info.

    Args:
        delivery_or_pickup: Either 'delivery' or 'pickup'
        contact: Phone number or email for order updates
    """
    valid, err = validate_contact(contact)
    if not valid:
        return err
    if delivery_or_pickup.lower() not in ("delivery", "pickup"):
        return "Please specify 'delivery' or 'pickup'."
    try:
        currency = get_currency_from_config(config)
        session_id = config["configurable"]["thread_id"] if config else "default"
        cart_rows = db.get_cart(session_id)
        if not cart_rows:
            return "The cart is empty — add some items first before checking out."

        items = [
            {
                "name": row["item_name"],
                "quantity": row["quantity"],
                "modifiers": json.loads(row["modifiers"]),
                "unit_price": row["unit_price"],
            }
            for row in cart_rows
        ]

        minutes = 35 if delivery_or_pickup.lower() == "delivery" else 15
        eta = (datetime.now() + timedelta(minutes=minutes)).strftime("%H:%M")

        order_id, subtotal = db.create_order(items, delivery_or_pickup.lower(), contact, eta)
        db.clear_cart(session_id)

        return (
            f"Order placed! ID: {order_id}. Subtotal: {format_price(subtotal, currency)}. "
            f"Type: {delivery_or_pickup}. Estimated ready time: {eta}."
        )
    except Exception as e:
        return f"Error placing order: {str(e)}"


SENSITIVE_TOOLS = [
    create_reservation,
    cancel_or_modify_reservation,
    join_waitlist,
    checkout_order,
]
