from langchain.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from rich import print
from rich.pretty import Pretty

from scripts.agents.tools.tools import escribir_archivo


sys_prompt= "Ayuda al usuario creando archivos cuando lo solicite."
sys_prompt+= "Si ya has creado un archivo con escribir_archivo como respuesta a una solicitud,"
sys_prompt+= "no vuelvas a llamar a escribir_archivo para la misma solicitud."
sys_prompt+= "En su lugar, informa al usuario que el archivo ya ha sido creado."

print("Sys prompt:")
print(sys_prompt)

# Crear agente con middleware HITL
agent_demo_hitl_no_input = create_agent(
    model=init_chat_model("openai:gpt-4o-mini", temperature=0),
    tools=[escribir_archivo],
    system_prompt=sys_prompt,
    middleware=[
        HumanInTheLoopMiddleware(
            interrupt_on={
                "escribir_archivo": {
                    "allowed_decisions": ["approve", "edit", "reject"]
                }
            }
        )
    ],
    # el checkpointer es el que nos permitirá retomar la ejecución.
    # En este caso se graba en memoria pero puede ser en una DB también
    checkpointer=InMemorySaver(),
)

# ============================================================
# CONFIGURA TU DECISIÓN AQUÍ (cambia según lo que quieras probar)
# ============================================================

# Si eliges "edit", configura los nuevos valores:
# EDIT_NOMBRE = "test_editado.txt"
EDIT_CONTENIDO = "Contenido modificado por el usuario"

# Si eliges "reject", configura el motivo:
REJECT_MOTIVO = "No autorizado para crear archivos en este momento"
# ============================================================

# Configuración con thread_id
config = {"configurable": {"thread_id": "demo-no-input-004"}}

print("=" * 70)
print("DEMO: Human-in-the-Loop SIN INPUT INTERACTIVO")

# Paso 1: Invocar el agente
print("[1] Enviando solicitud al agente...")
resultado = agent_demo_hitl_no_input.invoke(
    {"messages": [{"role": "user", "content": "Crea un archivo 'test.txt' con el texto 'Hola Mundo'"}]},
    config=config
)

print("El resultado de la primera llamada al agente:")
print(Pretty(resultado))

# Paso 2: Verificar si hay interrupción
if "__interrupt__" in resultado:
    print("\n⚠️  ACCIÓN SENSIBLE DETECTADA\n")

    # Mostrar información de la acción pendiente
    for interrupt in resultado["__interrupt__"]:
        action_requests = interrupt.value['action_requests']
        print("Estimado usuario, aprueba las siguientes acciones?")
        print(Pretty(action_requests))

    # cambiar esto por otro método de entrada si no se ejecuta en colab
    decision = input("Por favor responda con 'approve', 'edit' o 'reject'")

    # Paso 3: Ejecutar según la decisión configurada
    if decision == "approve":
        print(f"\n✅ Decisión: APPROVE - Ejecutando tal cual...")
        resultado_final = agent_demo_hitl_no_input.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config
        )

    elif decision == "edit":
        print(f"\n📝 Decisión: EDIT")
        #print(f"  Nuevo nombre: {EDIT_NOMBRE}")
        print(f"  Nuevo contenido: {EDIT_CONTENIDO[:50]}...")
        # recupero el nombre del archivo que ya venía, no quiero cambiarlo
        nom = resultado["__interrupt__"][0].value["action_requests"][0]["args"]["nombre"]
        resultado_final = agent_demo_hitl_no_input.invoke(
            Command(resume={
                #más info en https://docs.langchain.com/oss/python/deepagents/human-in-the-loop#edit-tool-arguments
                "decisions": [{
                    "type": "edit",
                    "edited_action": {
                        "name": "escribir_archivo",
                        "args": {
                            "nombre": "test.txt",
                            "contenido": EDIT_CONTENIDO
                        }
                    }
                }]
            }),
            config=config
        )

    elif decision == "reject":
        print(f"\n❌ Decisión: REJECT")
        print(f"  Motivo: {REJECT_MOTIVO}")
        resultado_final = agent_demo_hitl_no_input.invoke(
            Command(resume={
                "decisions": [{
                    "type": "reject",
                    "message": REJECT_MOTIVO
                }]
            }),
            config=config
        )

    print(f"\n✓ Resultado final: {resultado_final['messages'][-1].content}")
    print(Pretty(resultado_final))

else:
    print("\n✓ No se detectaron acciones sensibles.")
    print(f"Resultado: {resultado['messages'][-1].content}")