from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class State(TypedDict):
    """Shared conversation state passed between graph nodes."""
    messages: Annotated[list, add_messages]
