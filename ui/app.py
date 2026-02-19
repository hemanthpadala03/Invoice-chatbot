import streamlit as st
import requests
import uuid
import os
import json

API_URL = "http://127.0.0.1:8000/chat"
HISTORY_API = "http://127.0.0.1:8000/history"

CHAT_DIR = "chat_history"

st.set_page_config(page_title="Invoice AI Assistant", layout="wide")
st.title("📄 Invoice AI Assistant")

# =====================================================
# SESSION MANAGEMENT
# =====================================================

def get_all_sessions():
    if not os.path.exists(CHAT_DIR):
        return []

    sessions = []
    for file in os.listdir(CHAT_DIR):
        if file.endswith(".json"):
            sessions.append(file.replace(".json", ""))

    sessions.sort(reverse=True)
    return sessions


def load_session_history(session_id):
    try:
        response = requests.get(f"{HISTORY_API}/{session_id}")
        return response.json()
    except:
        return []


# =====================================================
# SIDEBAR (SESSION LIST)
# =====================================================

st.sidebar.title("💬 Chats")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# New chat button
if st.sidebar.button("➕ New Chat"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

st.sidebar.divider()

sessions = get_all_sessions()

for s in sessions:
    if st.sidebar.button(s):
        st.session_state.session_id = s
        st.session_state.messages = load_session_history(s)
        st.rerun()


# =====================================================
# DISPLAY CHAT
# =====================================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# =====================================================
# USER INPUT
# =====================================================

user_input = st.chat_input("Ask about invoices...")

if user_input:

    # show user message
    st.session_state.messages.append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.write(user_input)

    response = requests.post(
        API_URL,
        json={
            "question": user_input,
            "session_id": st.session_state.session_id
        }
    )

    answer = response.json()["answer"]

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    with st.chat_message("assistant"):
        st.write(answer)
