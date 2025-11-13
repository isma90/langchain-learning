import os
import json
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model  # API unificada de modelos (v1)
from langfuse.langchain import CallbackHandler
from rich import print
from rich.pretty import Pretty
from tavily import TavilyClient

load_dotenv()
langfuse_handler = CallbackHandler()
tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily = TavilyClient(api_key=tavily_api_key)

# ---------- Definimos 2 herramientas simples ----------
@tool
def buscar(term: str) -> str:
    """Realiza una búsqueda."""
    # Realiza la búsqueda en Tavily
    search = tavily.search(query=term, max_results=5)
    results = search.get("results", [])
    summary = f"Reporte de búsqueda Tavily para el tema '{term}':"
    details = []
    for res in results:
        title = res.get("title", "Sin título")
        url = res.get("url", "")
        content = res.get("content", "")
        details.append(f"- {title}\n  {content}\n  {url}\n")

    return json.dumps({
        "summary": summary,
        "details": "\n".join(details) or "No se encontraron resultados."
    })

@tool
def write_report(report, file_name):
    """Escribe archivos en disco"""
    with open(file_name, "w") as file:
        file.write(report)
    return "File " + file_name + " created Successfully"

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
demo_messages = [{"role": "user", "content": "Investiga GPT-5 y dame 3 puntos clave."}]
demo_result = agent_basico.invoke({"messages": demo_messages}, config={"callbacks": [langfuse_handler]})
print("Respuesta del agente (demo)")
print(Pretty(demo_result))