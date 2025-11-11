from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

DEFAULT_LANGFUSE_HOST = "https://cloud.langfuse.com"


def _is_disabled(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"0", "false", "no", "off", "disabled"}


def _parse_optional(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _parse_tags(raw_value: Optional[str]) -> Tuple[str, ...]:
    if raw_value is None:
        return ()
    items = [item.strip() for item in raw_value.split(",")]
    return tuple(tag for tag in items if tag)


def _parse_metadata(raw_value: Optional[str]) -> Dict[str, Any]:
    if raw_value is None:
        return {}
    trimmed = raw_value.strip()
    if not trimmed:
        return {}
    try:
        parsed = json.loads(trimmed)
    except json.JSONDecodeError as exc:  # pragma: no cover - user-provided data
        raise ValueError(
            "LANGFUSE_METADATA debe ser un JSON válido."
        ) from exc
    if not isinstance(parsed, dict):
        raise ValueError("LANGFUSE_METADATA debe representar un objeto JSON.")
    return parsed


@dataclass(frozen=True)
class LangfuseSettings:
    public_key: str
    secret_key: str
    host: str = DEFAULT_LANGFUSE_HOST
    environment: Optional[str] = None
    release: Optional[str] = None
    tags: Tuple[str, ...] = ()
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @classmethod
    def from_env(cls) -> Optional["LangfuseSettings"]:
        if _is_disabled(os.getenv("LANGFUSE_ENABLED")):
            return None

        public_key = _parse_optional(os.getenv("LANGFUSE_PUBLIC_KEY"))
        secret_key = _parse_optional(os.getenv("LANGFUSE_SECRET_KEY"))

        if not public_key or not secret_key:
            return None

        host = _parse_optional(os.getenv("LANGFUSE_HOST")) or DEFAULT_LANGFUSE_HOST
        environment = _parse_optional(os.getenv("LANGFUSE_ENVIRONMENT"))
        release = _parse_optional(os.getenv("LANGFUSE_RELEASE"))
        tags = _parse_tags(os.getenv("LANGFUSE_TAGS"))
        metadata = _parse_metadata(os.getenv("LANGFUSE_METADATA"))

        return cls(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            environment=environment,
            release=release,
            tags=tags,
            metadata=metadata,
        )


@lru_cache(maxsize=1)
def get_langfuse_settings() -> Optional[LangfuseSettings]:
    """Devuelve la configuración de Langfuse si está disponible."""
    return LangfuseSettings.from_env()


def build_langfuse_client(
    settings: Optional[LangfuseSettings] = None,
    *,
    overrides: Optional[Dict[str, Any]] = None,
):
    """
    Crea y devuelve una instancia de Langfuse lista para usarse.

    Si la configuración no está presente, devuelve ``None`` para permitir
    que el código llamante ignore la instrumentación de forma segura.
    """
    resolved_settings = settings or get_langfuse_settings()
    if resolved_settings is None:
        return None

    try:
        from langfuse import Langfuse
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            "langfuse no está instalado. Añádelo con `uv add langfuse`."
        ) from exc

    kwargs: Dict[str, Any] = {
        "public_key": resolved_settings.public_key,
        "secret_key": resolved_settings.secret_key,
        "host": resolved_settings.host,
    }

    if overrides:
        kwargs.update(overrides)

    return Langfuse(**kwargs)


def build_langfuse_callback(
    settings: Optional[LangfuseSettings] = None,
    *,
    session_id: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Construye un ``CallbackHandler`` de Langfuse para instrumentar LangChain.

    Devuelve ``None`` si Langfuse no está configurado. Si la librería no está
    instalada, lanza una ``RuntimeError`` con instrucciones para instalarla.
    """
    resolved_settings = settings or get_langfuse_settings()
    if resolved_settings is None:
        return None

    try:
        from langfuse.callback import CallbackHandler
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError(
            "langfuse.callback.CallbackHandler no está disponible. "
            "Instala la librería `langfuse` (>=2.0)."
        ) from exc

    combined_tags: Iterable[str] = resolved_settings.tags
    if tags:
        combined_tags = tuple(resolved_settings.tags) + tuple(tags)

    combined_metadata: Dict[str, Any] = dict(resolved_settings.metadata)
    if metadata:
        combined_metadata.update(metadata)

    handler_kwargs: Dict[str, Any] = {
        "public_key": resolved_settings.public_key,
        "secret_key": resolved_settings.secret_key,
        "host": resolved_settings.host,
    }

    if session_id:
        handler_kwargs["session_id"] = session_id
    if combined_tags:
        handler_kwargs["tags"] = list(combined_tags)
    if combined_metadata:
        handler_kwargs["metadata"] = combined_metadata
    if resolved_settings.release:
        handler_kwargs["release"] = resolved_settings.release
    if resolved_settings.environment:
        handler_kwargs["environment"] = resolved_settings.environment

    return CallbackHandler(**handler_kwargs)
