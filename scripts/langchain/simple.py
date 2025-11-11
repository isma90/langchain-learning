from langchain_core.prompts import PromptTemplate

from scripts.configs.config import get_settings
from scripts.pipelines.base import TabularPromptRunner


def main() -> None:
    settings = get_settings()

    prompt_template = PromptTemplate(
        template=(
            "Como un asistente de IA, responderás preguntas siendo muy específico "
            "y con respuestas acotadas. Pregunta: '''{question}'''"
        ),
        input_variables=["question"],
    )

    runner = TabularPromptRunner(
        settings=settings,
        prompt=prompt_template,
        input_column=settings.question_column,
        output_column=settings.model_column,
        prompt_variable="question",
        skip_rows=1,
    )

    df = runner.run()
    print("Respuestas agregadas al DataFrame y guardadas en el archivo.")
    print(df)


if __name__ == "__main__":
    main()
