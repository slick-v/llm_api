import sentry_sdk
from langfuse import Langfuse


from app.config import settings

langfuse_enabled = bool(settings.langfuse_public_key and settings.langfuse_secret_key)


# LLM tracing. Without keys it is switched off and every call on it does nothing,
# so the app runs the same on a laptop without a Langfuse account.

langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    base_url=settings.langfuse_base_url,
    tracing_enabled=langfuse_enabled,
    environment=settings.app_env,
)


def init_sentry():
    """Error reporting; does nothing until SENTRY_DSN is set."""
    if not settings.sentry_dsn:
        return
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        send_default_pii=False,  # no emails, IP addresses or request bodies
        traces_sample_rate=0.1,  # timing data for 10% of requests
    )