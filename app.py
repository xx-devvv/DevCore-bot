import streamlit as st
import os
import requests
import base64
from dotenv import load_dotenv
from openai import OpenAI

# --- 1. CONFIGURATION & WIDE LAYOUT ---
st.set_page_config(
    page_title="SupportIntel AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)
load_dotenv()

# --- 2. CUSTOM CSS (THE COMPLETE MAKEOVER) ---
st.markdown("""
<style>
    /* Main Background - Deep Enterprise Blue */
    .stApp {
        background: linear-gradient(to bottom right, #0f172a, #1e293b);
        color: #e2e8f0;
    }

    /* Top Navigation Bar Style */
    header[data-testid="stHeader"] {
        background-color: transparent;
    }

    /* Custom Chat Message Bubbles */
    div[data-testid="stChatMessage"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stChatMessage"] p {
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }

    /* User Avatar Container */
    div[data-testid="stChatMessage"] img {
        border-radius: 50%;
        border: 2px solid #38bdf8; 
    }

    /* Inputs and Dropdowns */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #0f172a;
        color: white;
        border: 1px solid #475569;
    }

    /* Titles */
    h1 {
        background: -webkit-linear-gradient(#38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem !important;
    }
    h3 {
        color: #94a3b8 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. CONNECT TO OPENROUTER ---
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    if "OPENROUTER_API_KEY" in st.secrets:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    else:
        st.error("❌ CRITICAL: API Key not found.")
        st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)


# --- 4. IMPROVED MODEL LOGIC ---
@st.cache_data(ttl=3600)
def get_vision_models():
    """Scans OpenRouter for RELIABLE vision models"""
    # We force specific reliable models first to prevent "empty bubble" errors
    default_models = [
        "google/gemini-2.0-flash-exp:free",  # Fastest & Best
        "meta-llama/llama-3.2-11b-vision-instruct:free",  # Reliable
        "qwen/qwen-2.5-vl-72b-instruct:free"  # Smart but slow
    ]
    return default_models


# --- 5. DASHBOARD LAYOUT ---
# Top Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("DevCore Labs")
    st.markdown("### 🛡️ DevCore Labs Technical Resolution System")
with col2:
    st.markdown("""
        <div style="background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #38bdf8; text-align: center;">
            <p style="margin:0; color: #94a3b8; font-size: 0.8rem;">SYSTEM STATUS</p>
            <p style="margin:0; color: #4ade80; font-weight: bold;">🟢 OPERATIONAL</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# Control Panel
c1, c2, c3 = st.columns(3)

with c1:
    models = get_vision_models()
    # Defaulting to Gemini because it is usually faster than Qwen
    selected_model = st.selectbox("🧠 AI Resolution Engine", models, index=0)

with c2:
    issue_category = st.selectbox(
        "📂 Ticket Category",
        ["Hardware Failure", "Software / Bug", "Billing & Account", "Network / Connectivity", "Security Alert", "Other"]
    )

with c3:
    uploaded_file = st.file_uploader("📎 Attach Evidence (Log/Screenshot)", type=["png", "jpg", "jpeg"])

# Dynamic Alerts
if "Security" in issue_category:
    st.warning("⚠️ SECURITY PROTOCOL ACTIVATED: Responses will prioritize account lockdown.")
elif "Billing" in issue_category:
    st.info("💲 FINANCE MODE: Responses will focus on refund policies.")

st.divider()

# --- 6. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []


def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')


# Icons
icons = {
    "assistant": "https://cdn-icons-png.flaticon.com/512/4712/4712035.png",
    "user": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
}

# Render History
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=icons[message["role"]]):
        st.markdown(message["content"])

# Handle Input
if prompt := st.chat_input("Describe the technical issue..."):

    with st.chat_message("user", avatar=icons["user"]):
        st.markdown(prompt)
        if uploaded_file:
            st.image(uploaded_file, width=300)

    st.session_state.messages.append({"role": "user", "content": prompt})

    # Prepare Payload
    system_instruction = f"""
    You are a Senior Level 3 Support Engineer.
    CURRENT TICKET CATEGORY: {issue_category}
    Tone: Professional, concise, solution-oriented.
    """

    messages_payload = [{"role": "system", "content": system_instruction}]

    # Add context
    for msg in st.session_state.messages[-4:]:
        messages_payload.append(msg)

    # Attach Image
    if uploaded_file:
        base64_img = encode_image(uploaded_file)
        if messages_payload[-1]["role"] == "user":
            messages_payload.pop()
        messages_payload.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
            ]
        })

    # Generate Response
    with st.chat_message("assistant", avatar=icons["assistant"]):
        response_placeholder = st.empty()
        full_response = ""

        # 1. IMMEDIATE FEEDBACK: Show this text BEFORE the API even responds
        response_placeholder.markdown("⏳ _Analyzing ticket data... Please wait..._")

        try:
            stream = client.chat.completions.create(
                model=selected_model,
                messages=messages_payload,
                stream=True,
                extra_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "SupportBot"}
            )

            # 2. As soon as data arrives, we overwrite the "Analyzing..." text
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")

            # Check for empty response
            if not full_response:
                st.error("⚠️ The AI returned an empty response. Please switch models in the dropdown!")
            else:
                response_placeholder.markdown(full_response)

        except Exception as e:
            st.error(f"⚠️ Connection Error: {e}")

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})