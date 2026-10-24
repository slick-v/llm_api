import boto3
from groq import Groq

from app.config import settings

# client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPTS = {
    "assistant": "You are a helpful, friendly assistant.",
    "tutor": "You are a patient tutor. Explain step by step with simple examples, then ask one question to check understanding.",
    "coder": "You are a senior Python developer. Give working code with short explanations and point out bugs or bad practices.",
    "interviewer": "You are a technical interviewer. Ask one question at a time, wait for the answer, then give brief feedback.",
}

MAX_HISTORY = 10  # NEW: only send the last 10 messages

# client
if settings.llm_provider == "bedrock":
    bedrock = boto3.client("bedrock-runtime",region_name=settings.aws_region)
else:
    groq_client= Groq(api_key=settings.groq_api_key)



def trim_history(messages: list[dict]) -> list[dict]:
    trimmed = messages[-MAX_HISTORY]
    while trimmed and trimmed[0]["role"] != ["user"]:
        trimmed = trimmed[1:]
    return trimmed

def get_reply(messages: list[dict], mode:str = "assistant") -> tuple[str, int]:

    if settings.llm_provider == "bedrock":
        return _bedrock_reply(messages, mode)
    return _groq_reply(messages, mode)

def stream_reply(messages: list[dict] , mode: str ="assistant") :
    if settings.llm_provider == "bedrock":
        yield from _bedrock_strem(messages, mode)
    else:
        yield from _groq_stream(messages, mode)


# bedrock
def _bedrock_messages(messages: list[dict]) -> list[dict]:
    return [
        {"role": m["role"], "content": [{"text": m["content"]}]}
        for m in trim_history(messages)
    ]



def _bedrock_reply(messages, mode):
    response = bedrock.converse(
        modelId=settings.bedrock_model_id,
        system=[{ "text": SYSTEM_PROMPTS[mode]}],

        messages=_bedrock_messages(messages),
        inferenceConfig={"maxTokens": settings.max_tokens},
    )
    reply =response["output"]["message"]["content"][0]["text"]
    tokens_used = response["usage"]["totaltokens"]
    return reply, tokens_used

def _bedrock_stream(messages, mode):
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
