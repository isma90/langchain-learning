from langchain_core.prompts import PromptTemplate

from scripts.configs.config import get_settings
from scripts.pipelines.base import TabularPromptRunner


def main() -> None:
    settings = get_settings()

    prompt_template = PromptTemplate(
        template=(
            "Responde de forma cercana y positiva en máximo dos frases la siguiente pregunta: "
            "'''{consulta}'''"
        ),
        input_variables=["consulta"],
    )

    runner = TabularPromptRunner(
        settings=settings,
        prompt=prompt_template,
        input_column=settings.question_column,
        output_column="MODELO_FRIENDLY",
        prompt_variable="consulta",
        skip_rows=1,
    )

    df = runner.run()
    print("Respuestas amigables agregadas al DataFrame y guardadas en el archivo.")
    print(df)


if __name__ == "__main__":
    main()
