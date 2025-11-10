from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import pandas as pd
from langchain_core.prompts import BasePromptTemplate

from scripts.configs.config import Settings
from scripts.utils.io_utils import (
    ensure_column_exists,
    iter_rows,
    load_dataframe,
    rename_numeric_columns,
    save_dataframe,
)
from scripts.configs.llm_factory import build_chat_model

RowMapper = Callable[[pd.Series], Dict[str, Any]]
ResponseParser = Callable[[Any], Any]


@dataclass
class TabularPromptRunner:
    """Ejecuta un prompt sobre un dataset tabular agregando la respuesta del modelo."""

    settings: Settings
    prompt: BasePromptTemplate
    input_column: str
    output_column: str
    prompt_variable: str = "question"
    skip_rows: int = 0
    overwrite: bool = False
    build_variables: Optional[RowMapper] = None
    response_parser: Optional[ResponseParser] = None

    def run(self) -> pd.DataFrame:
        df = load_dataframe(self.settings.data_file, header=self.settings.data_header)

        if self.input_column not in df.columns:
            rename_numeric_columns(df, {0: self.input_column})

        if (
            self.settings.answer_column not in df.columns
            and self.settings.answer_column != self.input_column
        ):
            rename_numeric_columns(df, {1: self.settings.answer_column})

        ensure_column_exists(df, self.output_column, default_value=None)

        llm = build_chat_model(self.settings)
        chain = self.prompt | llm

        for index, row in iter_rows(df, skip_rows=self.skip_rows):
            existing_value = row.get(self.output_column)
            if not self.overwrite and pd.notna(existing_value):
                continue

            question_value = row.get(self.input_column)
            if pd.isna(question_value):
                continue

            variables = (
                self.build_variables(row)
                if self.build_variables is not None
                else {self.prompt_variable: question_value}
            )

            try:
                response = chain.invoke(variables)
            except Exception as exc:  # pragma: no cover - logging/managing errors
                df.at[index, self.output_column] = f"Error: {exc}"
                continue

            content = (
                self.response_parser(response)
                if self.response_parser is not None
                else getattr(response, "content", response)
            )
            df.at[index, self.output_column] = content

        save_dataframe(df, self.settings.data_file)
        return df

