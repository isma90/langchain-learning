import os

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
from langchain_community.chat_message_histories import RedisChatMessageHistory



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

def chat(id: str, message: str, client: str):
    redis_url = os.getenv('REDIS_URL')
    chat_history = RedisChatMessageHistory(session_id=id, url=redis_url)
    if (client == "user"):
        chat_history.add_user_message(message)
    else:
        chat_history.add_ai_message(message)

def main() -> None:
    langfuse_handler = build_langfuse_callback()  # lee las variables de entorno

    # 3️⃣ Cadena (pipeline): prompt → modelo
    chain = _build_chain()

    # 4️⃣ Ejemplo de uso con historial manual
    redis_url = os.getenv('REDIS_URL')
    session_id = 'cliente0'
    chat_history = RedisChatMessageHistory(session_id=session_id, url=redis_url)

    chat('chat1', 'Hola', 'user')
    chat('chat1', 'Hola que tal?', 'ai')
    chat('chat1', 'bien gracias', 'user')
    chat('chat1', 'con quien estoy hablando?', 'ai')
    chat('chat1', 'Juan Perez', 'user')
    chat('chat1', 'fabulos juan, un gusto', 'ai')

    chat('chat2', 'Hola', 'user')
    chat('chat2', 'Hola que tal?', 'ai')
    chat('chat2', 'bien gracias', 'user')
    chat('chat2', 'con quien estoy hablando?', 'ai')
    chat('chat2', 'Rodrigo Leal', 'user')
    chat('chat2', 'fabulos Rodrigo, un gusto', 'ai')


    user_input = "¿Cómo me llamo?"

    # Pasamos la lista `chat_history.messages`
    result = chain.invoke(
        {
            "input": user_input,
            "chat_history": RedisChatMessageHistory(session_id='chat1', url=redis_url).messages,
        },
        # 👇 Aquí se inyecta el handler de Langfuse
        config={"callbacks": [langfuse_handler] if langfuse_handler else []},
    )
    chat_history.add_ai_message(result.content)


    print(chat_history)

if __name__ == "__main__":
    main()
