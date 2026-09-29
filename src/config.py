"""Environment config and shared client instances."""

import os
import threading

from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq


load_dotenv()


HINDSIGHT_API_KEY = os.environ["HINDSIGHT_API_KEY"]
HINDSIGHT_BASE_URL = os.environ.get(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io",
)

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)


# Name of the shared cross-deal memory bank
PLAYBOOK_BANK_ID = "playbook"


def deal_bank_id(deal_id: str) -> str:
    """Bank id for a single deal's private memory."""
    return f"deal-{deal_id}"


# ------------------------------------------------------------------
# Client storage
# ------------------------------------------------------------------
#
# IMPORTANT:
# Hindsight uses aiohttp internally.
#
# A single globally cached Hindsight client can end up being reused
# across different asyncio event loops/threads, which causes errors
# such as:
#
#   RuntimeError:
#   Timeout context manager should be used inside a task
#
# Therefore, keep one Hindsight client PER THREAD.
# The client is created inside the thread that will use it.
# ------------------------------------------------------------------

_hindsight_local = threading.local()

_groq_client = None


def get_hindsight() -> Hindsight:
    """
    Return the Hindsight client associated with the current thread.

    Each thread gets its own Hindsight client so that its aiohttp
    resources are not shared across different asyncio event loops.
    """

    client = getattr(_hindsight_local, "client", None)

    if client is None:
        client = Hindsight(
            base_url=HINDSIGHT_BASE_URL,
            api_key=HINDSIGHT_API_KEY,
        )

        _hindsight_local.client = client

    return client


def get_groq() -> Groq:
    """Return the shared Groq client."""

    global _groq_client

    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)

    return _groq_client