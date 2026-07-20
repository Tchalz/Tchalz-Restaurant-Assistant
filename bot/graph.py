import sqlite3

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from bot.state import State
from bot.llm import llm
from bot.tools_safe import SAFE_TOOLS
from bot.tools_sensitive import SENSITIVE_TOOLS

SYSTEM_PROMPT = """You are the virtual assistant for Tchalz Restaurant.
You help customers browse the menu, check allergens, view daily specials,
check opening hours, check table availability, make or modify reservations,
join the waitlist, build an order in their cart, and check order status.

Ordering flow:
- Use add_to_cart once per distinct item the customer wants, including any
  customizations they mention (e.g. "extra spicy", "no onions", "mild").
- Use view_cart whenever the customer wants to see what's in their order, or
  to confirm the running total before checkout.
- Use checkout_order only after the customer has confirmed their cart and
  given delivery/pickup preference and contact info.

Reservation flow:
- Always check table availability before creating a reservation.
- If no table is available, offer to add the customer to the waitlist with join_waitlist.

Always use the allergen tool for any allergy-related question instead of guessing.
Prices returned by tools are already formatted in the customer's selected currency —
repeat them exactly as given, don't convert, reformat, or add a different symbol.
Be warm, concise, and professional, in keeping with Tchalz Restaurant's hospitality."""

ALL_TOOLS = SAFE_TOOLS + SENSITIVE_TOOLS
SENSITIVE_TOOL_NAMES = {t.name for t in SENSITIVE_TOOLS}

llm_with_tools = llm.bind_tools(ALL_TOOLS)


def chatbot(state: State) -> dict:
    """
    The Tchalz Restaurant chatbot node. Takes the current conversation,
    sends it to the LLM (with tools bound), and returns the response.
    """
    system = SystemMessage(content=SYSTEM_PROMPT)
    response = llm_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}


def route_tools(state: State) -> str:
    """
    Inspects the last AI message. If it called a sensitive tool, route to
    'sensitive_tools' (which the graph interrupts before). If it called a
    safe tool, route to 'safe_tools'. Otherwise, end the turn.
    """
    last_message = state["messages"][-1]
    if not getattr(last_message, "tool_calls", None):
        return END

    called_names = {tc["name"] for tc in last_message.tool_calls}
    if called_names & SENSITIVE_TOOL_NAMES:
        return "sensitive_tools"
    return "safe_tools"


def build_graph(db_path: str = "data/tchalz_restaurant.sqlite"):
    """
    Builds and compiles the Tchalz Restaurant graph with a SQLite checkpointer
    and an interrupt before any sensitive (state-changing) tool call.
    """
    graph_builder = StateGraph(State)

    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_node("safe_tools", ToolNode(SAFE_TOOLS))
    graph_builder.add_node("sensitive_tools", ToolNode(SENSITIVE_TOOLS))

    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        route_tools,
        {"safe_tools": "safe_tools", "sensitive_tools": "sensitive_tools", END: END},
    )
    graph_builder.add_edge("safe_tools", "chatbot")
    graph_builder.add_edge("sensitive_tools", "chatbot")

    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    return graph_builder.compile(
        checkpointer=memory,
        interrupt_before=["sensitive_tools"],
    )
