from langchain.agents import create_agent
from langchain.chat_models import init_chat_model  # API unificada de modelos (v1)
from langfuse.langchain import CallbackHandler
from rich import print
from rich.pretty import Pretty
from scripts.agents.tools.tools import write_report, buscar


langfuse_handler = CallbackHandler()

tools_basicos = [buscar, write_report]

# ---------- Modelo ----------
# Puedes pasar un string de modelo (proveedor:modelo) o una instancia.
# Aquí usamos el inicializador unificado para evitar vendor-lock-in.
model = init_chat_model("openai:gpt-5-mini", temperature=1)

# ---------- Creamos el agente ----------
agent_basico = create_agent(
    model=model,
    tools=tools_basicos,
    system_prompt=(
        "Busca en internet sobre algún tema que selecciones, luego de investigar arma un reporte con lo guardas como archivo"
    ),
)

# ---------- Invocación mínima ----------
demo_messages = [{"role": "user", "content": "Investiga sobre algún tema interesante"}]
demo_result = agent_basico.invoke({"messages": demo_messages}, config={"callbacks": [langfuse_handler]})
print("Respuesta del agente (demo)")
print(Pretty(demo_result))