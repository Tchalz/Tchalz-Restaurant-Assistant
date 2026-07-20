import os
from langchain_core.messages import HumanMessage
from bot.graph import build_graph

os.makedirs("data", exist_ok=True)
graph = build_graph()


def handle_interrupt(config: dict):
    """
    Called after an invoke leaves the graph paused (interrupted before a
    sensitive tool). Shows the pending tool call and asks for approval.
    """
    state = graph.get_state(config)
    if not state.next:
        return  # not interrupted, nothing to do

    pending = state.values["messages"][-1]
    print("\n--- Approval needed ---")
    for call in pending.tool_calls:
        print(f"  Tool: {call['name']}")
        print(f"  Args: {call['args']}")
    decision = input("Approve this action? (yes/no): ").strip().lower()

    if decision == "yes":
        resumed = graph.invoke(None, config)
    else:
        graph.update_state(
            config,
            {"messages": [HumanMessage(content="I changed my mind, please cancel that action.")]},
        )
        resumed = graph.invoke(None, config)

    final = resumed["messages"][-1]
    if getattr(final, "content", None):
        print(f"Tchalz Restaurant: {final.content}")


def chat():
    print("Welcome to Tchalz Restaurant. Type 'quit' to exit.\n")
    thread_id = input("Enter a thread/customer ID (or press Enter for 'guest'): ").strip() or "guest"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Thanks for visiting Tchalz Restaurant. Goodbye!")
            break
        if not user_input:
            continue

        result = graph.invoke({"messages": [HumanMessage(content=user_input)]}, config)
        last = result["messages"][-1]
        if getattr(last, "content", None):
            print(f"Tchalz Restaurant: {last.content}")

        handle_interrupt(config)


if __name__ == "__main__":
    chat()
