from datetime import datetime, timezone

import boto3
from groq import Groq
from langfuse import propagate_attributes

from app.config import settings
from app.observability import langfuse

SYSTEM_PROMPTS = {
    "assistant": "You are a helpful, friendly assistant.",
    "tutor": "You are a patient tutor. Explain step by step with simple examples, then ask one question to check understanding.",
    "coder": "You are a senior Python developer. Give working code with short explanations and point out bugs or bad practices.",
    "interviewer": "You are a technical interviewer. Ask one question at a time, wait for the answer, then give brief feedback.",
}

MAX_HISTORY = 10  # only send the last 10 messages

# client
if settings.llm_provider == "bedrock":
    bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)
else:
    groq_client = Groq(api_key=settings.groq_api_key)


def trim_history(messages: list[dict]) -> list[dict]:
    trimmed = messages[-MAX_HISTORY:]
    while trimmed and trimmed[0]["role"] != "user":
        trimmed = trimmed[1:]
    return trimmed


# ---------- public functions (routes call these) ----------

def get_reply(messages: list[dict], mode: str = "assistant", user_id=None, session_id=None) -> tuple[str, int]:
    """Send the chat history to the LLM and return (reply, tokens_used)."""
    generation = _start_generation("llm-reply", messages, mode, user_id, session_id)
    try:
        if settings.llm_provider == "bedrock":
            reply, usage = _bedrock_reply(messages, mode)
        else:
            reply, usage = _groq_reply(messages, mode)
    except Exception as e:
        generation.update(level="ERROR", status_message=str(e))
        generation.end()
        raise

    generation.update(output=_logged(reply), usage_details=usage)
    generation.end()
    return reply, usage["input"] + usage["output"]


def stream_reply(messages: list[dict], mode: str = "assistant", user_id=None, session_id=None):
    generation = _start_generation("llm-stream", messages, mode, user_id, session_id)
    provider_stream = _bedrock_stream if settings.llm_provider == "bedrock" else _groq_stream
    usage: dict = {}  # filled in by the provider when the stream ends
    parts: list[str] = []
    try:
        for text in provider_stream(messages, mode, usage):
            if not parts:
                # time to first token: with streaming, this is the wait users feel
                generation.update(completion_start_time=datetime.now(timezone.utc))
            parts.append(text)
            yield text
    except Exception as e:
        generation.update(level="ERROR", status_message=str(e))
        raise
    finally:
        # also runs when the user presses Stop or closes the page
        generation.update(output=_logged("".join(parts)), usage_details=usage or None)
        generation.end()


# ---------- langfuse ----------

def _model_name() -> str:
    return settings.bedrock_model_id if settings.llm_provider == "bedrock" else settings.model_name


def _logged(content):
    # with LANGFUSE_LOG_CONTENT=false only numbers (tokens, timing, errors) reach Langfuse
    return content if settings.langfuse_log_content else None


def _start_generation(name: str, messages: list[dict], mode: str, user_id, session_id):
    """Start a Langfuse record of one LLM call, tagged with who asked and in which mode."""
    # attributes set here are copied onto the observation created inside the block
    with propagate_attributes(
        user_id=str(user_id) if user_id is not None else None,
        session_id=session_id,
        tags=[mode, settings.llm_provider],
        trace_name="chat",
    ):
        # start_observation (not start_as_current_observation): a streamed reply
        # continues in another thread, where a "current" context would break
        return langfuse.start_observation(
            name=name,
            as_type="generation",
            model=_model_name(),
            model_parameters={"max_tokens": settings.max_tokens},
            input=_logged([{"role": "system", "content": SYSTEM_PROMPTS[mode]}] + trim_history(messages)),
            metadata={"mode": mode, "provider": settings.llm_provider},
        )


# ---------- groq ----------

def _groq_messages(messages: list[dict], mode: str) -> list[dict]:
    system = {"role": "system", "content": SYSTEM_PROMPTS[mode]}
    return [system] + trim_history(messages)


def _groq_reply(messages, mode):
    response = groq_client.chat.completions.create(
        model=settings.model_name,
        messages=_groq_messages(messages, mode),
        max_tokens=settings.max_tokens,
    )
    usage = {"input": response.usage.prompt_tokens, "output": response.usage.completion_tokens}
    return response.choices[0].message.content, usage


def _groq_stream(messages, mode, usage: dict):
    stream = groq_client.chat.completions.create(
        model=settings.model_name,
        messages=_groq_messages(messages, mode),
        max_tokens=settings.max_tokens,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        # Groq puts the token counts on the last chunk
        if chunk.x_groq is not None and chunk.x_groq.usage is not None:
            usage.update(input=chunk.x_groq.usage.prompt_tokens, output=chunk.x_groq.usage.completion_tokens)


# ---------- bedrock (Converse API works the same for every Bedrock model) ----------

def _bedrock_messages(messages: list[dict]) -> list[dict]:
    return [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in trim_history(messages)
    ]


def _bedrock_reply(messages, mode):
    response = bedrock.converse(
        modelId=settings.bedrock_model_id,
        system=[{"text": SYSTEM_PROMPTS[mode]}],
        messages=_bedrock_messages(messages),
        inferenceConfig={"maxTokens": settings.max_tokens},
    )
    reply = response["output"]["message"]["content"][0]["text"]
    tokens = response["usage"]
    return reply, {"input": tokens["inputTokens"], "output": tokens["outputTokens"]}


def _bedrock_stream(messages, mode, usage: dict):
    response = bedrock.converse_stream(
        modelId=settings.bedrock_model_id,
        system=[{"text": SYSTEM_PROMPTS[mode]}],
        messages=_bedrock_messages(messages),
        inferenceConfig={"maxTokens": settings.max_tokens},
    )
    for event in response["stream"]:
        if "contentBlockDelta" in event:
            text = event["contentBlockDelta"]["delta"].get("text")
            if text:
                yield text
        elif "metadata" in event:
            # Bedrock sends the token counts in a last "metadata" event
            tokens = event["metadata"]["usage"]
            usage.update(input=tokens["inputTokens"], output=tokens["outputTokens"])








# def build_messages(messages: list[dict], mode:str) ->list[dict]:
#     trimmed = messages[-MAX_HISTORY:]

#     while trimmed and trimmed[0]["role"] != "user":
#         trimmed = trimmed[1:]
#     system = {"role": "system", "content": SYSTEM_PROMPTS[mode]}
#     return [system] + trimmed

#     # pass

# def get_reply(messages: list[dict], mode:str = "assistant") -> tuple[str, int]:
#     """Send the chat history to groq and return (reply, tokens_used)"""
#     # full_message = [{"role":"system", "content": SYSTEM_PROMPTS}] + messages

#     response =client.chat.completions.create(
#         model= settings.model_name,
#         messages=build_messages(messages,mode),
#         max_tokens=settings.max_tokens,
#     )

#     reply = response.choices[0].message.content
#     tokens_used = response.usage.total_tokens
#     return reply, tokens_used


# def stream_reply(messages: list[dict], mode:str = "assistant"):
#     stream = client.chat.completions.create(
#         model= settings.model_name,
#         messages=build_messages(messages, mode),
#         max_tokens=settings.max_tokens,
#         stream=True,
#     )

#     for chunk in stream:
#         if chunk.choices and chunk.choices[0].delta.content:
#             yield chunk.choices[0].delta.content
