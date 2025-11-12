"""Utilidades para asegurar compatibilidad con APIs antiguas de LangChain."""

from __future__ import annotations

import sys
import types
from typing import List, Optional

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, get_buffer_string


def ensure_langchain_memory_module() -> None:
    """Registra el módulo ``langchain.memory`` si la instalación actual no lo incluye."""
    if "langchain.memory" in sys.modules:
        return

    class ChatMessageHistory(BaseChatMessageHistory):
        """Implementación simple en memoria compatible con la API clásica."""

        def __init__(self) -> None:
            self.messages: List[BaseMessage] = []

        def add_message(self, message: BaseMessage) -> None:
            self.messages.append(message)

        def add_messages(self, messages) -> None:
            self.messages.extend(messages)

        def clear(self) -> None:
            self.messages.clear()

        def __str__(self) -> str:
            return get_buffer_string(self.messages)

    module = types.ModuleType(
        "langchain.memory",
        "Compatibilidad local para versiones de LangChain sin `langchain.memory`.",
    )
    module.ChatMessageHistory = ChatMessageHistory
    module.__all__ = ["ChatMessageHistory"]
    sys.modules["langchain.memory"] = module


__all__ = ["ensure_langchain_memory_module"]
