import os
import json
from tavily import TavilyClient
from typing import Iterable, Optional
from dotenv import load_dotenv
from openai import OpenAI
from rich import print
from rich.pretty import Pretty

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
MODEL = 'gpt-5-mini'


def get_secret(key: str, *, required: bool = True) -> Optional[str]:
    """Return a secret regardless of the runtime."""
    value = os.getenv(key)
    if required and not value:
        raise RuntimeError(f'Environment variable {key} is not set.')
    return value


def configure_environment(required_keys: Iterable[str]) -> None:
    for key in required_keys:
        get_secret(key)

configure_environment(["OPENAI_API_KEY"])

client = OpenAI()


tavily_api_key = get_secret('TAVILY_API_KEY')
tavily = TavilyClient(api_key=tavily_api_key)

def get_topic_report(topic):
    # Realiza la búsqueda en Tavily
    search = tavily.search(query=topic, max_results=5)
    results = search.get("results", [])

    summary = f"Reporte de búsqueda Tavily para el tema '{topic}':"
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

def write_report(report):
    with open("report.txt", "w") as file:
        file.write(report)


# Paso 1: enviar al modelo la conversación y las funciones que tiene disponibles
messages = [{"role": "user", "content": "Necesito que elijas un tema, investigues sobre el y me des un resumen de lo que encontraste, el resumen que armes guardalo como archivo"}]
print("Mensaje inicial:")
print(Pretty(messages))

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_topic_report",
            "description": "tool para buscar información en internet",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Tema a investigar y reportar.",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_report",
            "description": "tool para guardar archivos en disco",
            "parameters": {
                "type": "object",
                "properties": {
                    "report": {
                        "type": "string",
                        "description": "reporte del tema investigado",
                    }
                },
                "required": ["report"],
            },
        },
    }
]

available_functions = {
    "get_topic_report": get_topic_report,
    "write_report": write_report
}

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    tools=tools,
    tool_choice="auto",  # auto es el valor por defecto, también puede ser required (al menos llamar a una), none o function (para llamar a una función particular)
)
response_message = response.choices[0].message
print ("Respuesta  a la primera llamada:")
print(Pretty(response_message))



tool_calls = response_message.tool_calls
# Paso 2: checkear si el modelo pidió ejecutar una función
if tool_calls:
    # Paso 3: llamar a la función
    # Nota: la respuesta JSON podría no siempre ser válida, tenemos que capturar esos errores
    available_functions = {
        "get_topic_report": get_topic_report,
        "write_report": write_report
    }  # en este ejemplo hay una sola función, pero podría haber más
    messages.append(response_message)  # agregar la respuesta del asistente al historial de conversación

    # Paso 4: enviar la información de cada function call y respuesta correspondiente
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        print("\nLlamando a función: " + function_name)
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        print ("Argumentos de la función:")
        print(Pretty(function_args))
        function_response = function_to_call(**function_args)
        print("Respuesta de la función:")
        print(Pretty(function_response))
        new_message=(
            {
                "tool_call_id": tool_call.id,
                "role": "tool", # se utiliza para indicarle al modelo que es la respuesta de la función de la herramienta que se ejecutó
                "name": function_name,
                "content": function_response,
            }
        )
        messages.append(new_message)  # agregar la respuesta de la función al historial de conversación
        print("Nuevo mensaje:")
        print(Pretty(new_message))
    # ahora podemos volver a llamar al modelo, que encontrará las respuestas a las llamadas de función en el historial
    second_response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
    )

    print("\nSegunda respuesta:")
    print(second_response.choices[0].message.content)