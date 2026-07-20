import base64
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

from bot.graph import build_graph
from bot.mock_data import CATEGORY_IMAGES

st.set_page_config(page_title="Tchalz Restaurant", page_icon="🍽️")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #14120F;
    color: #E8E2D6;
}

[data-testid="stSidebar"] {
    background-color: #1B1814;
    border-right: 1px solid rgba(176,141,87,0.25);
}

.main .block-container {
    border: 1px solid rgba(176,141,87,0.35);
    padding: 2.5rem 3rem;
    position: relative;
    max-width: 700px;
}

.main .block-container::before,
.main .block-container::after {
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    border: 2px solid #B08D57;
}

.main .block-container::before {
    top: -1px;
    left: -1px;
    border-right: none;
    border-bottom: none;
}

.main .block-container::after {
    bottom: -1px;
    right: -1px;
    border-left: none;
    border-top: none;
}

h1 {
    font-family: 'Cinzel', serif !important;
    letter-spacing: 2px;
    color: #E8E2D6 !important;
    text-align: center;
}

.stApp small,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
    color: #B08D57 !important;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-align: center;
    display: block;
}

.tchalz-divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 1.5rem 0 2rem;
    color: #B08D57;
    font-family: 'Cinzel', serif;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.tchalz-divider::before,
.tchalz-divider::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(176,141,87,0.4);
}

.bubble {
    max-width: 78%;
    padding: 14px 18px;
    border-radius: 2px;
    margin-bottom: 14px;
    font-size: 15px;
    line-height: 1.55;
}

.bubble.user {
    background: rgba(176,141,87,0.1);
    border: 1px solid rgba(176,141,87,0.3);
    margin-left: auto;
    color: #E8E2D6;
}

.bubble.bot {
    background: rgba(18,51,40,0.35);
    border-left: 2px solid #123328;
    border-top: 1px solid rgba(176,141,87,0.15);
    border-right: 1px solid rgba(176,141,87,0.15);
    border-bottom: 1px solid rgba(176,141,87,0.15);
    color: #E8E2D6;
}

.tchalz-label {
    font-family: 'Cinzel', serif;
    font-size: 12px;
    letter-spacing: 1.5px;
    color: #B08D57;
    margin-bottom: 6px;
    text-transform: uppercase;
}

.stChatInput textarea, .stChatInput input {
    background-color: rgba(176,141,87,0.06) !important;
    border: 1px solid rgba(176,141,87,0.35) !important;
    color: #E8E2D6 !important;
}

.stButton button {
    border: 1px solid #B08D57 !important;
    color: #B08D57 !important;
    background-color: transparent !important;
}

.stButton button:hover {
    background-color: rgba(176,141,87,0.1) !important;
}

.tchalz-gallery {
    display: flex;
    gap: 16px;
    overflow-x: auto;
    padding-bottom: 10px;
    margin-bottom: 8px;
    scroll-snap-type: x mandatory;
}

.tchalz-gallery::-webkit-scrollbar {
    height: 6px;
}

.tchalz-gallery::-webkit-scrollbar-thumb {
    background: rgba(176,141,87,0.4);
    border-radius: 4px;
}

.tchalz-gallery::-webkit-scrollbar-track {
    background: rgba(176,141,87,0.08);
}

.tchalz-tile {
    flex: 0 0 160px;
    scroll-snap-align: start;
    text-align: center;
}

.tchalz-tile img {
    width: 160px;
    height: 160px;
    object-fit: cover;
    border: 1px solid rgba(176,141,87,0.35);
    border-radius: 2px;
    display: block;
}

.tchalz-category-label {
    font-family: 'Cinzel', serif;
    font-size: 11px;
    letter-spacing: 1.5px;
    color: #B08D57;
    text-transform: uppercase;
    text-align: center;
    margin-top: 6px;
}
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()

# ---- Session state setup ----
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_interrupt" not in st.session_state:
    st.session_state.pending_interrupt = None  # holds tool_calls while paused for approval
if "currency" not in st.session_state:
    st.session_state.currency = "USD"

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id,
        "currency": st.session_state.currency,
    }
}


# ---- Sidebar ----
with st.sidebar:
    st.header("🍽️ Tchalz Restaurant")
    st.caption(f"Session: `{st.session_state.thread_id[:8]}`")

    currency_options = {"USD": "$ US Dollar", "NGN": "₦ Nigerian Naira", "GBP": "£ British Pound", "EUR": "€ Euro"}
    selected = st.selectbox(
        "Currency",
        options=list(currency_options.keys()),
        format_func=lambda code: currency_options[code],
        index=list(currency_options.keys()).index(st.session_state.currency),
    )
    if selected != st.session_state.currency:
        st.session_state.currency = selected
        st.rerun()

    if st.button("Start new conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.pending_interrupt = None
        st.rerun()


st.title("Tchalz Restaurant Assistant")
st.caption("Reservations · Table Service · Counter Service")
st.markdown('<div class="tchalz-divider">Concierge</div>', unsafe_allow_html=True)

@st.cache_data
def _img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# ---- Menu category gallery (horizontally scrollable) ----
available_categories = {name: path for name, path in CATEGORY_IMAGES.items() if path}
if available_categories:
    st.markdown('<div class="tchalz-divider">Browse the Menu</div>', unsafe_allow_html=True)

    tiles_html = ""
    for category, image_path in available_categories.items():
        b64 = _img_to_base64(image_path)
        tiles_html += (
            f'<div class="tchalz-tile">'
            f'<img src="data:image/png;base64,{b64}" alt="{category}">'
            f'<div class="tchalz-category-label">{category}</div>'
            f'</div>'
        )

    st.markdown(f'<div class="tchalz-gallery">{tiles_html}</div>', unsafe_allow_html=True)


def run_graph(input_state):
    """Invoke (or resume) the graph, update chat history, and detect interrupts."""
    result = graph.invoke(input_state, config)
    last = result["messages"][-1]

    state = graph.get_state(config)
    if state.next:
        # Paused before a sensitive tool call — needs human approval
        pending_msg = state.values["messages"][-1]
        st.session_state.pending_interrupt = pending_msg.tool_calls
    else:
        st.session_state.pending_interrupt = None
        if getattr(last, "content", None):
            st.session_state.chat_history.append(
                {"role": "assistant", "content": last.content}
            )


def render_bubble(role: str, content: str):
    """Renders a single chat message as a themed HTML bubble, matching the Tchalz design."""
    if role == "user":
        st.markdown(f'<div class="bubble user">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="tchalz-label">Tchalz</div><div class="bubble bot">{content}</div>',
            unsafe_allow_html=True,
        )


# ---- Render chat history ----
for msg in st.session_state.chat_history:
    render_bubble(msg["role"], msg["content"])


# ---- Approval flow (if a sensitive tool is pending) ----
if st.session_state.pending_interrupt:
    st.markdown('<div class="tchalz-label">Tchalz</div>', unsafe_allow_html=True)
    st.warning("This action needs your approval before it happens:")
    for call in st.session_state.pending_interrupt:
        st.write(f"**Action:** `{call['name']}`")
        st.json(call["args"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve", use_container_width=True):
            run_graph(None)
            st.rerun()
    with col2:
        if st.button("❌ Reject", use_container_width=True):
            graph.update_state(
                config,
                {"messages": [HumanMessage(content="I changed my mind, please cancel that action.")]},
            )
            run_graph(None)
            st.rerun()

# ---- Normal chat input (disabled while an approval is pending) ----
else:
    user_input = st.chat_input("Type your message...")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        render_bubble("user", user_input)

        with st.spinner("Thinking..."):
            run_graph({"messages": [HumanMessage(content=user_input)]})

        st.rerun()
