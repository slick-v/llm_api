import os

import requests
import streamlit as st

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
STREAM_URL = f"{BASE_URL}/chat/stream"

MODES = {
    "Assistant": "assistant",
    "Tutor": "tutor",
    "Coder": "coder",
    "Interviewer": "interviewer",
}

st.set_page_config(page_title="LLM Chat", page_icon="💬")
st.title("💬 LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    mode_label = st.selectbox("Mode", list(MODES))
    st.metric("Messages", len(st.session_state.messages))
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()


def stream_from_backend(messages, mode):
    with requests.post(
        STREAM_URL,
        json={"messages": messages, "mode": mode},
        stream=True,
        timeout=90,
    ) as response:
        response.raise_for_status()
        response.encoding = "utf-8"
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(
                stream_from_backend(st.session_state.messages, MODES[mode_label])
            )
        except requests.exceptions.RequestException as e:
            st.session_state.messages.pop()
            st.error(f"Backend error: {e}")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()