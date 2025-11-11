import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
from langchain_core.prompts import PromptTemplate

from scripts.configs.config import get_settings
from scripts.configs.llm_factory import build_chat_model

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
INPUT_FILE = PROJECT_ROOT / "content" / "opiniones_usuarios.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "content" / "opiniones_usuarios_clasificadas.xlsx"
SCORE_COLUMN = "puntaje"
SENTIMENT_COLUMN = "sentimiento"
CONCURRENCY_LIMIT = 5


def _load_opinions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de opiniones en: {path}")
    return pd.read_excel(path, header=0)


def _prepare_opinion_series(df: pd.DataFrame) -> Tuple[pd.Series, str]:
    if df.shape[1] < 6:
        raise ValueError("Se esperaban al menos 6 columnas para localizar las opiniones (columna F).")
    opinion_column = df.columns[5]
    return df[opinion_column], opinion_column


def _ensure_output_columns(df: pd.DataFrame) -> None:
    if SCORE_COLUMN not in df.columns:
        df[SCORE_COLUMN] = None
    if SENTIMENT_COLUMN not in df.columns:
        df[SENTIMENT_COLUMN] = None


def _build_chain():
    settings = get_settings()
    prompt = PromptTemplate(
        template=(
            "Analiza la siguiente opinión de un usuario:\n"
            "Opinión: '''{opinion}'''\n\n"
            "Devuelve exclusivamente un JSON con esta estructura exacta:\n"
            "{{\"score\": <entero de 1 a 10>, \"sentiment\": \"Positivo|Neutro|Negativo\"}}\n"
            "Recuerda: solo responde con el JSON."
        ),
        input_variables=["opinion"],
    )
    llm = build_chat_model(settings)
    return prompt | llm


def _parse_response(raw_response: Any) -> Tuple[Optional[int], Optional[str]]:
    content = getattr(raw_response, "content", raw_response)
    if not isinstance(content, str):
        return None, None
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return None, None

    score = payload.get("score")
    sentiment = payload.get("sentiment")

    if isinstance(score, (int, float)):
        score = int(score)
        if not (1 <= score <= 10):
            score = None
    else:
        score = None

    if isinstance(sentiment, str):
        sentiment_normalized = sentiment.strip().capitalize()
        if sentiment_normalized not in {"Positivo", "Neutro", "Negativo"}:
            sentiment = None
        else:
            sentiment = sentiment_normalized
    else:
        sentiment = None

    return score, sentiment


async def _analyze_opinion(
    chain,
    opinion: str,
    semaphore: asyncio.Semaphore,
) -> Tuple[Optional[int], Optional[str]]:
    if not isinstance(opinion, str) or not opinion.strip():
        return None, None

    async with semaphore:
        try:
            response = await chain.ainvoke({"opinion": opinion})
        except Exception:
            return None, None

    return _parse_response(response)


async def process_opinions(opinions: Iterable[str], concurrency: int = CONCURRENCY_LIMIT):
    chain = _build_chain()
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [
        asyncio.create_task(_analyze_opinion(chain, opinion, semaphore))
        for opinion in opinions
    ]
    return await asyncio.gather(*tasks)


async def main() -> None:
    df = _load_opinions(INPUT_FILE)
    opinions, opinion_column = _prepare_opinion_series(df)
    _ensure_output_columns(df)

    results = await process_opinions(opinions)

    for index, (score, sentiment) in zip(opinions.index, results):
        df.at[index, SCORE_COLUMN] = score
        df.at[index, SENTIMENT_COLUMN] = sentiment

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Archivo generado: {OUTPUT_FILE}")
    print(df)


if __name__ == "__main__":
    asyncio.run(main())

