"""
_llm/factory_llm.py
-------------------
Creates a reusable LLM client via SAP AI Core using gen_ai_hub SDK.

Usage:
    from _llm.factory_llm import get_llm, call_llm_structured
    llm = get_llm()
    result: MyModel = call_llm_structured(llm, system_prompt, user_prompt, MyModel)
"""

import os
import logging
from typing import Type, TypeVar

from pydantic import BaseModel
from gen_ai_hub.proxy.langchain.openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

AICORE_AUTH_URL = os.getenv("AICORE_AUTH_URL")
AICORE_CLIENT_ID = os.getenv("AICORE_CLIENT_ID")
AICORE_CLIENT_SECRET = os.getenv("AICORE_CLIENT_SECRET")
AICORE_RESOURCE_GROUP = os.getenv("AICORE_RESOURCE_GROUP")
AICORE_BASE_URL = os.getenv("AICORE_BASE_URL")
LLM_DEPLOYMENT_ID = os.getenv("LLM_DEPLOYMENT_ID")


def get_llm(temperature: float = 0) -> ChatOpenAI:
    """Return a ChatOpenAI client configured for SAP AI Core."""
    return ChatOpenAI(
        deployment_id=LLM_DEPLOYMENT_ID,
        temperature=temperature,
    )


def call_llm_structured(
    llm: ChatOpenAI,
    system_prompt: str,
    user_prompt: str,
    output_model: Type[T],
    temperature: float = 0.2,
) -> T:
    """Call the LLM and parse the response into output_model using structured output."""
    structured_llm = llm.with_structured_output(output_model)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    logger.debug("Calling LLM with structured output for %s", output_model.__name__)
    result = structured_llm.invoke(messages)
    return result
