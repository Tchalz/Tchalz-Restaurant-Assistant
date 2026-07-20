import base64
import uuid

import requests
import streamlit as st
from langchain_core.messages import HumanMessage

from bot import db
from bot.graph import build_graph
from bot.mock_data import CATEGORY_IMAGES

st.set_page_config(page_title="Tchalz Restaurant", page_icon="🍽️", layout="wide")

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
    max-width: 1200px;
    padding: 2.5rem 2rem;
}

.tchalz-frame {
    border: 1px solid rgba(176,141,87,0.35);
    padding: 2.5rem 3rem;
    position: relative;
}

.tchalz-frame::before,
.tchalz-frame::after {
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    border: 2px solid #B08D57;
}

.tchalz-frame::before {
    top: -1px;
    left: -1px;
    border-right: none;
    border-bottom: none;
}

.tchalz-frame::after {
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

[data-testid="stChatInput"],
[data-testid="stChatInputContainer"],
[data-testid="stBottomBlockContainer"] {
    background-color: #14120F !important;
}

.stChatInput textarea, .stChatInput input,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    background-color: rgba(176,141,87,0.06) !important;
    border: 1px solid rgba(176,141,87,0.35) !important;
    color: #E8E2D6 !important;
    -webkit-text-fill-color: #E8E2D6 !important;
    -webkit-appearance: none !important;
    caret-color: #E8E2D6 !important;
    color-scheme: dark !important;
    box-shadow: 0 0 0 30px #14120F inset !important;
    outline: none !important;
}

.stChatInput textarea:focus, .stChatInput input:focus,
[data-testid="stChatInput"] textarea:focus,
[data-testid="stChatInput"] input:focus {
    border: 1px solid #B08D57 !important;
    box-shadow: 0 0 0 30px #14120F inset !important;
    outline: none !important;
}

.stChatInput textarea:-webkit-autofill,
.stChatInput input:-webkit-autofill,
[data-testid="stChatInput"] textarea:-webkit-autofill,
[data-testid="stChatInput"] input:-webkit-autofill {
    -webkit-text-fill-color: #E8E2D6 !important;
    -webkit-box-shadow: 0 0 0 30px #14120F inset !important;
    transition: background-color 5000s ease-in-out 0s;
}

.stChatInput textarea::placeholder, .stChatInput input::placeholder,
[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: rgba(232,226,214,0.5) !important;
    -webkit-text-fill-color: rgba(232,226,214,0.5) !important;
}

.stButton button {
    border: 1px solid #B08D57 !important;
    color: #B08D57 !important;
    background-color: transparent !important;
}

.stButton button:hover {
    background-color: rgba(176,141,87,0.1) !important;
}

.tchalz-gallery-wrap {
    position: relative;
}

.tchalz-swipe-hint {
    display: none;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #B08D57;
    margin-bottom: 6px;
}

.tchalz-swipe-hint svg {
    animation: tchalz-swipe-nudge 1.4s ease-in-out infinite;
}

@keyframes tchalz-swipe-nudge {
    0%, 100% { transform: translateX(0); opacity: 0.6; }
    50% { transform: translateX(4px); opacity: 1; }
}

@media (max-width: 768px) {
    .tchalz-swipe-hint {
        display: flex;
    }
    .tchalz-gallery-wrap::after {
        content: "";
        position: absolute;
        top: 0;
        right: 0;
        bottom: 10px;
        width: 36px;
        background: linear-gradient(to right, rgba(20,18,15,0), #14120F 85%);
        pointer-events: none;
    }
    .tchalz-gallery::-webkit-scrollbar {
        height: 5px;
    }
    .tchalz-gallery::-webkit-scrollbar-thumb {
        background: rgba(176,141,87,0.75);
    }
    .tchalz-gallery::-webkit-scrollbar-track {
        background: rgba(176,141,87,0.15);
    }
}

.tchalz-gallery {
    display: flex;
    gap: 16px;
    overflow-x: auto;
    padding-bottom: 10px;
    margin-bottom: 8px;
    scroll-snap-type: x mandatory;
    scrollbar-width: thin;
    scrollbar-color: rgba(176,141,87,0.6) rgba(176,141,87,0.1);
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

/* ---- Side panel styling ---- */
.tchalz-panel {
    border: 1px solid rgba(176,141,87,0.3);
    padding: 0.9rem 1rem;
    margin-bottom: 1rem;
}

.tchalz-panel-title {
    font-family: 'Cinzel', serif;
    font-size: 11px;
    letter-spacing: 1.5px;
    color: #B08D57;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.tchalz-panel p {
    font-size: 13px;
    margin: 0 0 4px;
    color: #E8E2D6;
}

.tchalz-status-open {
    font-size: 11px;
    color: #6FA37C;
    margin-top: 6px;
}

.tchalz-status-pending {
    font-size: 11px;
    color: #B08D57;
    margin-top: 6px;
}

.tchalz-review {
    font-size: 13px;
    font-style: italic;
    color: #E8E2D6;
    margin: 0 0 6px;
    line-height: 1.5;
}

.tchalz-review-author {
    font-size: 11px;
    color: #8a7c5c;
    margin: 0;
}

.tchalz-weather {
    text-align: center;
}

.tchalz-weather-temp {
    font-family: 'Cinzel', serif;
    font-size: 28px;
    color: #E8E2D6;
    margin: 4px 0 2px;
}

.tchalz-weather-desc {
    font-size: 12px;
    color: #B08D57;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 0 0 4px;
}

.tchalz-weather-meta {
    font-size: 11px;
    color: #8a7c5c;
    margin: 0;
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

config = {"configurable": {"thread_id": st.session_state.thread_id}}


# ---- Sidebar ----
with st.sidebar:
    st.header("🍽️ Tchalz Restaurant")
    st.caption(f"Session: `{st.session_state.thread_id[:8]}`")
    if st.button("Start new conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.pending_interrupt = None
        st.rerun()


@st.cache_data
def _img_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


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


RESTAURANT_LAT = 6.4531   # Marina Rd, Lagos
RESTAURANT_LON = 3.3958

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain",
    67: "Freezing rain", 71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Rain showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


@st.cache_data(ttl=600)
def get_current_weather(lat: float, lon: float):
    """Fetches live weather from Open-Meteo (free, no API key). Cached for 10 minutes."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "temperature_unit": "celsius",
            },
            timeout=5,
        )
        resp.raise_for_status()
        current = resp.json()["current_weather"]
        return {
            "temp_c": round(current["temperature"]),
            "condition": WEATHER_CODES.get(current["weathercode"], "Unknown"),
            "windspeed": round(current["windspeed"]),
        }
    except Exception:
        return None


def render_left_panel():
    st.markdown(
        """
        <div class="tchalz-panel">
            <div class="tchalz-panel-title">Hours</div>
            <p>Mon&ndash;Fri: 11am&ndash;10pm</p>
            <p>Sat&ndash;Sun: 9am&ndash;11pm</p>
            <div class="tchalz-status-open">&#9679; open now</div>
        </div>
        <div class="tchalz-panel">
            <div class="tchalz-panel-title">Contact</div>
            <p>&#128205; 12 Marina Rd, Lagos</p>
            <p>&#128222; +234 801 234 5678</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    weather = get_current_weather(RESTAURANT_LAT, RESTAURANT_LON)
    if weather:
        st.markdown(
            f"""
            <div class="tchalz-panel tchalz-weather">
                <div class="tchalz-panel-title">Weather in Lagos</div>
                <div class="tchalz-weather-temp">{weather['temp_c']}&deg;C</div>
                <div class="tchalz-weather-desc">{weather['condition']}</div>
                <p class="tchalz-weather-meta">Wind {weather['windspeed']} km/h</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="tchalz-panel tchalz-weather">
                <div class="tchalz-panel-title">Weather</div>
                <p style="color:#8a7c5c;font-size:12px;">Unavailable right now</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_right_panel():
    reservation = db.get_reservation_by_session(st.session_state.thread_id)
    if reservation:
        status = reservation.get("status", "confirmed")
        status_class = "tchalz-status-open" if status == "confirmed" else "tchalz-status-pending"
        st.markdown(
            f"""
            <div class="tchalz-panel">
                <div class="tchalz-panel-title">Your reservation</div>
                <p>Table for {reservation.get('party_size', '-')}</p>
                <p>{reservation.get('date', '-')} at {reservation.get('time', '-')}</p>
                <div class="{status_class}">&#9679; {status}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="tchalz-panel">
                <div class="tchalz-panel-title">Your reservation</div>
                <p style="color:#8a7c5c;">No active reservation yet. Ask Tchalz to book one for you.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="tchalz-panel">
            <div class="tchalz-panel-title">What guests say</div>
            <p class="tchalz-review">&ldquo;Warm service, unforgettable jollof.&rdquo;</p>
            <p class="tchalz-review-author">&#9733;&#9733;&#9733;&#9733;&#9733; &mdash; Ada O.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---- Three column layout: info | chat | reservation ----
left_col, center_col, right_col = st.columns([1, 3, 1], gap="medium")

with left_col:
    render_left_panel()

with right_col:
    render_right_panel()

with center_col:
    st.markdown('<div class="tchalz-frame">', unsafe_allow_html=True)

    st.title("Tchalz Restaurant Assistant")
    st.caption("Reservations · Table Service · Counter Service")
    st.markdown('<div class="tchalz-divider">Concierge</div>', unsafe_allow_html=True)

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

        st.markdown(
            '<div class="tchalz-swipe-hint">Swipe '
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="2"><path d="M9 6l6 6-6 6"/></svg></div>'
            f'<div class="tchalz-gallery-wrap"><div class="tchalz-gallery">{tiles_html}</div></div>',
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

    st.markdown('</div>', unsafe_allow_html=True)
