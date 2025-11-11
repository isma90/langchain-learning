from scripts.utils.langchain_shims import ensure_langchain_memory_module

from scripts.configs.config import get_settings
from scripts.configs.langfuse import build_langfuse_callback
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from scripts.configs.llm_factory import build_chat_model

ensure_langchain_memory_module()
from langchain.memory import ChatMessageHistory  # noqa: E402

def _build_chain():
    settings = get_settings()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            "Como un asistente de IA, responderás preguntas de acuerdo con el siguiente historial de conversación."
        ),
        # Placeholder que recibirá la lista de mensajes del historial
        MessagesPlaceholder(variable_name="chat_history"),
        # Mensaje del usuario para esta invocación
        HumanMessagePromptTemplate.from_template("{input}"),
    ])
    llm = build_chat_model(settings)
    return prompt | llm


def main() -> None:
    langfuse_handler = build_langfuse_callback()  # lee las variables de entorno

    # 3️⃣ Cadena (pipeline): prompt → modelo
    chain = _build_chain()

    # 4️⃣ Ejemplo de uso con historial manual
    chat_history = ChatMessageHistory()
    chat_history.add_user_message("Hola, me llamo Juan")
    chat_history.add_ai_message("Hola, Juan")

    user_input = "¿Cómo me llamo?"
    chat_history.add_user_message(user_input)
    # Pasamos la lista `chat_history.messages`
    result = chain.invoke(
        {
            "input": user_input,
            "chat_history": chat_history.messages,
        },
        # 👇 Aquí se inyecta el handler de Langfuse
        config={"callbacks": [langfuse_handler] if langfuse_handler else []},
    )
    chat_history.add_ai_message(result.content)


    print(chat_history)

if __name__ == "__main__":
    main()
