from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables once when the module is imported.
load_dotenv()

# Base project directory (two levels up from this file: scripts/configs/).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_FILE = PROJECT_ROOT / "content" / "preguntas_respuestas.xlsx"


def _parse_header(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"none", ""}:
        return None
    try:
        return int(lowered)
    except ValueError as exc:
        raise ValueError(
            f"DATA_HEADER must be an integer or 'none', got '{value}'."
        ) from exc


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    data_file: Path = DEFAULT_DATA_FILE
    question_column: str = "PREGUNTA"
    answer_column: str = "RESPUESTA"
    model_column: str = "MODELO"
    data_header: Optional[int] = None

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY no está configurada. Añádela en tu archivo .env."
            )

        model_name = os.getenv("MODEL_NAME", cls.model_name)

        temperature_value = os.getenv("MODEL_TEMPERATURE", str(cls.temperature))
        try:
            temperature = float(temperature_value)
        except ValueError as exc:
            raise ValueError(
                f"MODEL_TEMPERATURE debe ser un número, se recibió '{temperature_value}'."
            ) from exc

        data_file_env = os.getenv("DATA_FILE")
        if data_file_env:
            data_file_guess = Path(data_file_env).expanduser()
            if not data_file_guess.is_absolute():
                data_file_value = (PROJECT_ROOT / data_file_guess).resolve()
            else:
                data_file_value = data_file_guess
        else:
            data_file_value = DEFAULT_DATA_FILE

        question_column = os.getenv("QUESTION_COLUMN", cls.question_column)
        answer_column = os.getenv("ANSWER_COLUMN", cls.answer_column)
        model_column = os.getenv("MODEL_COLUMN", cls.model_column)

        data_header = _parse_header(os.getenv("DATA_HEADER"))

        return cls(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            data_file=data_file_value,
            question_column=question_column,
            answer_column=answer_column,
            model_column=model_column,
            data_header=data_header,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración cargada desde variables de entorno (con cache)."""
    return Settings.from_env()
