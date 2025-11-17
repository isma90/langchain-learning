from rich import print
from rich.pretty import Pretty
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIMiddleware,
    SummarizationMiddleware,
    wrap_tool_call,
)
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langfuse.langchain import CallbackHandler

from scripts.agents.tools.tools import auditoria_privacidad, buscar_politicas, manejar_errores_de_tool

# Inicializar Langfuse handler
langfuse_handler = CallbackHandler()

# --------- Modelos reales con LLMs ---------
model = init_chat_model("openai:gpt-4o-mini", temperature=0)

agent_con_middleware = create_agent(
    model=model,
    tools=[auditoria_privacidad, buscar_politicas],
    system_prompt=(
        "Eres un asistente interno. Antes de responder DEBES ejecutar 'auditoria_privacidad' "
        "y luego enriquecer tu respuesta usando las herramientas disponibles."
    ),
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True), # Middleware estándar de langchain
        manejar_errores_de_tool, # nuestro middleware, que detecta y maneja errores al llamar herrmientas
    ],
    checkpointer=InMemorySaver(),
)

# --------- Historial ficticio para disparar sumarización y PII ---------
historial_ficticio = [
    {
        "role": "user",
        "content": "Sprint 1: documentamos cómo el agente consulta bases internas, logs de llamadas y tickets históricos. La gerencia quiere métricas de precisión por cada release."

    },
    {
        "role": "assistant",
        "content": "Perfecto, guardo ese contexto como parte del backlog del agente.",
    },
    {
        "role": "user",
        "content": "Sprint 2: agregamos 4 fuentes nuevas y se duplicó el número de tokens en cada interacción. También necesitamos auditorías trimestrales."

    },
    {
        "role": "assistant",
        "content": "Anotado. Ajustaré los umbrales para que el resumen automático aparezca antes.",
    }
]

nuevo_requerimiento = {
    "role": "user",
    "content": (
        "Soy Ana Vera (ana.vera@banco.cl). Necesito un memo muy breve con los lineamientos de "
        "RAG para la banca chilena y menciona que ya corrimos la auditoría obligatoria."
    ),
}

thread_id = "middleware-demo-001"
resultado = agent_con_middleware.invoke(
    {"messages": historial_ficticio + [nuevo_requerimiento]},
    config={
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler]
    },
)

print("=== Demo: middlewares en acción ===")
print(Pretty(resultado))
print()
print("Mensajes generados en la conversación:")
for msg in resultado["messages"]:
    nombre = msg.__class__.__name__
    contenido = getattr(msg, "content", "")
    print(f"- {nombre}: {contenido}")