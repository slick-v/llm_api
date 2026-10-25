import os
import uuid

import requests
import streamlit as st

BASE_URL = os.getenv("API_URL", "http://localhost:8000")
STREAM_URL = f"{BASE_URL}/chat/stream"

MAX_INPUT_CHARS = 2000
HISTORY_TO_SEND = 10  # the backend only uses the last 10 anyway

MODES = {
    "Assistant": "assistant",
    "Tutor": "tutor",
    "Coder": "coder",
    "Interviewer": "interviewer",
}


class BackendError(Exception):
    """An error with a message that is safe to show to the user."""


def error_message(response) -> str:
    if response.status_code == 422:
        return "That message is too long or empty. Please shorten it and try again."
    try:
        # 429 and 502 come with a friendly "detail" from our backend
        return response.json()["detail"]
    except (ValueError, KeyError, TypeError):
        return "Something went wrong. Please try again."


st.set_page_config(page_title="LLM Chat", page_icon="💬")
st.title("💬 LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

# a random id per browser session, used for the per-user rate limit;
# after login (part 2) this becomes the user's email
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

with st.sidebar:
    mode_label = st.selectbox("Mode", list(MODES))
    st.metric("Messages", len(st.session_state.messages))
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()


def stream_from_backend(messages, mode, user_id):
    with requests.post(
        STREAM_URL,
        json={"messages": messages[-HISTORY_TO_SEND:], "mode": mode},
        headers={"X-User-Id": user_id},
        stream=True,
        timeout=90,
    ) as response:
        # read the error text here, while the connection is still open
        if response.status_code != 200:
            raise BackendError(error_message(response))
        response.encoding = "utf-8"
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message...", max_chars=MAX_INPUT_CHARS):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            reply = st.write_stream(
                stream_from_backend(
                    st.session_state.messages,
                    MODES[mode_label],
                    st.session_state.user_id,
                )
            )
        except BackendError as e:
            st.session_state.messages.pop()
            st.error(str(e))
            st.stop()
        except requests.exceptions.RequestException:
            st.session_state.messages.pop()
            st.error("Can't reach the server right now. Please try again.")
            st.stop()

    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()