from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from .config import Settings


def build_chat_model(
    settings: Settings,
    *,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    api_key: Optional[str] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """Crea una instancia de ChatOpenAI usando la configuración compartida."""
    return ChatOpenAI(
        model=model_name or settings.model_name,
        api_key=api_key or settings.openai_api_key,
        temperature=temperature if temperature is not None else settings.temperature,
        **kwargs,
    )

