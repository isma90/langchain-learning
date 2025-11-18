from rich import print as rprint
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIMiddleware,
    HumanInTheLoopMiddleware,
)
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langfuse.langchain import CallbackHandler

from scripts.agents.tools.tools import (
    auditoria_privacidad,
    buscar_politicas,
    manejar_errores_de_tool,
    escribir_archivo,
)
from scripts.agents.tools.hitl_interaction import (
    manejar_hitl_interactivo,
    mostrar_resultado_final,
)

# ============================================================================
# CONFIGURACIÓN DEL AGENTE CON HUMAN-IN-THE-LOOP
# ============================================================================

# Inicializar Langfuse handler
langfuse_handler = CallbackHandler()

# Modelos reales con LLMs
model = init_chat_model("openai:gpt-4o-mini", temperature=0)

agent_con_middleware = create_agent(
    model=model,
    tools=[auditoria_privacidad, buscar_politicas, escribir_archivo],
    system_prompt=(
        "Eres un asistente interno. Antes de responder DEBES ejecutar 'auditoria_privacidad' "
        "y luego enriquecer tu respuesta usando las herramientas disponibles. "
        "El resultado de la auditoría se debe almacenar en un archivo .txt"
    ),
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        manejar_errores_de_tool,
        HumanInTheLoopMiddleware(
            interrupt_on={
                "escribir_archivo": {
                    "allowed_decisions": ["approve", "edit", "reject"]
                }
            }
        ),
    ],
    checkpointer=InMemorySaver(),
)

# ============================================================================
# DATOS DE PRUEBA
# ============================================================================

historial_ficticio = [
    {
        "role": "user",
        "content": (
            "Sprint 1: documentamos cómo el agente consulta bases internas, "
            "logs de llamadas y tickets históricos. La gerencia quiere métricas "
            "de precisión por cada release."
        ),
    },
    {
        "role": "assistant",
        "content": "Perfecto, guardo ese contexto como parte del backlog del agente.",
    },
    {
        "role": "user",
        "content": (
            "Sprint 2: agregamos 4 fuentes nuevas y se duplicó el número de tokens "
            "en cada interacción. También necesitamos auditorías trimestrales."
        ),
    },
    {
        "role": "assistant",
        "content": "Anotado. Ajustaré los umbrales para que el resumen automático aparezca antes.",
    },
]

nuevo_requerimiento = {
    "role": "user",
    "content": (
        "Soy Ana Vera (ana.vera@banco.cl). Necesito un memo muy breve con los lineamientos de "
        "RAG para la banca chilena y menciona que ya corrimos la auditoría obligatoria."
    ),
}

# ============================================================================
# EJECUCIÓN CON HUMAN-IN-THE-LOOP
# ============================================================================

thread_id = "middleware-demo-001"

rprint("\n[bold blue]🚀 INICIANDO AGENTE CON HUMAN-IN-THE-LOOP[/bold blue]\n")
rprint(f"[italic]Thread ID:[/italic] {thread_id}\n")

# PASO 1: Invocar el agente
rprint("[bold yellow][1] Enviando solicitud al agente...[/bold yellow]\n")

resultado = agent_con_middleware.invoke(
    {"messages": historial_ficticio + [nuevo_requerimiento]},
    config={
        "configurable": {"thread_id": thread_id},
        "callbacks": [langfuse_handler],
    },
)

rprint("[bold green]✅ Agente procesó la solicitud[/bold green]\n")

# PASO 2-4: Manejar el flujo HITL interactivo
resultado_final = manejar_hitl_interactivo(
    resultado_inicial=resultado,
    agent=agent_con_middleware,
    thread_id=thread_id,
)

# Mostrar resultado
if resultado_final:
    # Si hay resultado_final, significa que se ejecutó una acción
    mostrar_resultado_final(resultado_final)
else:
    # Si no hay resultado_final, significa que no hubo acciones sensibles
    if "messages" in resultado and resultado["messages"]:
        last_message = resultado["messages"][-1]
        rprint(f"\n[bold]Respuesta del agente:[/bold]\n{last_message.content}\n")