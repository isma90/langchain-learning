from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Optional

import pandas as pd


def load_dataframe(path: Path, *, header: Optional[int]) -> pd.DataFrame:
    """Carga un DataFrame desde un archivo Excel."""
    return pd.read_excel(path, header=header)


def save_dataframe(df: pd.DataFrame, path: Path) -> None:
    """Guarda un DataFrame en el archivo Excel indicado."""
    df.to_excel(path, index=False)


def ensure_column_exists(
    df: pd.DataFrame,
    column: str,
    *,
    default_value=None,
) -> None:
    """Asegura que la columna exista en el DataFrame."""
    if column not in df.columns:
        df[column] = default_value


def rename_numeric_columns(df: pd.DataFrame, mapping: Mapping[int, str]) -> None:
    """Renombra columnas identificadas por número si coinciden con el mapeo dado."""
    if all(col in df.columns for col in mapping):
        df.rename(columns=mapping, inplace=True)


def iter_rows(
    df: pd.DataFrame,
    *,
    skip_rows: int = 0,
) -> Iterable[tuple[int, pd.Series]]:
    """Itera sobre las filas del DataFrame aplicando un offset opcional."""
    for index, row in df.iterrows():
        if index < skip_rows:
            continue
        yield index, row

